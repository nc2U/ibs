"""
approval.services.document_service
===================================
결재 문서 핵심 비즈니스 로직 서비스 레이어.

View (ApprovalDocumentViewSet)의 submit/act 액션에서 호출되는 핵심 상태 전이 로직을
이 서비스 모듈로 위임하여, View를 얇게(thin) 유지하고 비즈니스 로직의 단위 테스트를 용이하게 합니다.
"""
from django.db import transaction
from django.utils import timezone

from approval.models import ApprovalDocument, ApprovalStep


@transaction.atomic
def submit_document(document: ApprovalDocument, route_steps: list[dict]) -> ApprovalDocument:
    """
    임시저장(draft) 또는 반려(rejected) 상태의 결재 문서를 상신(pending)으로 전환합니다.

    처리 순서:
    1. 기존 결재 단계 초기화 (재상신 대응)
    2. route_steps로부터 ApprovalStep 인스턴스 생성
    3. content_hash 산출 (위변조 방지 기준점 기록)
    4. 문서 상태 → pending, submitted_at 기록

    Args:
        document: 상신할 ApprovalDocument 인스턴스 (드래프트 또는 반려 상태여야 함)
        route_steps: build_dynamic_approval_route() 반환값 (step_order, role_label, approvers, condition 포함)

    Returns:
        상태가 갱신된 ApprovalDocument 인스턴스

    Raises:
        ValueError: 상신 불가 상태인 경우
        ValueError: route_steps가 비어있는 경우
    """
    if document.status not in (ApprovalDocument.STATUS_DRAFT, ApprovalDocument.STATUS_REJECTED):
        raise ValueError('임시저장 또는 반려 상태에서만 상신할 수 있습니다.')

    if not route_steps:
        raise ValueError('결재선이 비어있습니다. 소속 부서 또는 대표이사 계정 연동 상태를 확인해 주세요.')

    # 1. 기존 단계 초기화 (재상신 시 이전 결재선 삭제)
    document.steps.all().delete()

    # 2. 결재 단계 인스턴스 생성
    for step_data in route_steps:
        step = ApprovalStep.objects.create(
            document=document,
            step_order=step_data['step_order'],
            role_label=step_data['role_label'],
            condition=step_data['condition'],
            status=ApprovalStep.STATUS_PENDING,
        )
        step.approvers.set(step_data['approvers'])

    # 3. content_hash 산출 — 상신 시점 문서 내용의 SHA-256 기록
    document.content_hash = document.compute_hash()

    # 4. 상태 전이
    document.status = ApprovalDocument.STATUS_PENDING
    document.current_step = 1
    document.submitted_at = timezone.now()
    document.save(update_fields=['content_hash', 'status', 'current_step', 'submitted_at'])

    return document


@transaction.atomic
def finalize_approval(document: ApprovalDocument) -> ApprovalDocument:
    """
    마지막 결재 단계 승인 완료 시 문서를 최종 승인(approved) 처리합니다.

    처리 순서:
    1. 문서 상태 → approved, completed_at 기록
    2. DocNumberSequence를 통해 원자적 채번 (레이스컨디션 방지)

    Args:
        document: 최종 승인 처리할 ApprovalDocument 인스턴스

    Returns:
        상태 및 doc_number가 갱신된 ApprovalDocument 인스턴스
    """
    document.status = ApprovalDocument.STATUS_APPROVED
    document.completed_at = timezone.now()
    document.doc_number = document.generate_doc_number()
    document.save(update_fields=['status', 'completed_at', 'doc_number'])
    return document
