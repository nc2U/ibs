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

    # 문서 유형에 대상 자료실 카테고리가 지정된 경우 일반 문서로 자동 아카이빙
    try:
        archive_to_docs(document)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning('결재 문서 자동 아카이빙 실패 (doc %s): %s', document.pk, e)

    return document


def archive_to_docs(document: ApprovalDocument):
    """
    최종 승인된 ApprovalDocument의 doc_type에 target_doc_category가 지정되어 있을 경우
    docs.models.Document (일반 문서)로 자동 아카이빙(보관)합니다.
    """
    if not document.doc_type or not document.doc_type.target_doc_category:
        return None

    if document.status != ApprovalDocument.STATUS_APPROVED:
        return None

    from docs.models import Document, File
    from work.models import IssueProject

    target_category = document.doc_type.target_doc_category
    identifier = f"[전자결재:{document.pk}]"

    # 중복 아카이빙 방지: 이미 생성된 문서가 있는지 확인
    existing = Document.objects.filter(description__startswith=identifier).first()
    if existing:
        # PDF 파일이 뒤늦게 생성되었으나 기존에 파일 등록이 안 된 경우 추가
        if document.pdf_file and document.pdf_file.name:
            if not existing.files.filter(description__contains="전자결재 최종 승인 문서").exists():
                File.objects.create(
                    docs=existing,
                    file=document.pdf_file,
                    file_name=f"{document.doc_number or document.title}.pdf",
                    file_type="application/pdf",
                    creator=document.drafter,
                    description=f"전자결재 최종 승인 문서 ({document.doc_number})",
                )
        return existing

    # 워크스페이스 결정
    workspace = document.workspace
    if not workspace:
        company = None
        if document.drafter_assignment and document.drafter_assignment.company:
            company = document.drafter_assignment.company
        else:
            try:
                drafter_staff = document.drafter.staff
                if drafter_staff and drafter_staff.company:
                    company = drafter_staff.company
            except Exception:
                pass

        if company:
            workspace = (
                IssueProject.objects.filter(company=company, type='1').first() or
                IssueProject.objects.filter(company=company).first()
            )
        if not workspace:
            workspace = IssueProject.objects.first()

    if not workspace:
        return None

    execution_date = document.completed_at.date() if document.completed_at else timezone.localdate()

    doc_record = Document.objects.create(
        issue_project=workspace,
        category=target_category,
        doc_type=target_category.doc_type or '1',
        title=document.title,
        execution_date=execution_date,
        description=f"{identifier} {document.doc_number or ''} {document.title}"[:255],
        creator=document.drafter,
        security_level=document.security_level if hasattr(document, 'security_level') else Document.SECURITY_COMPANY,
    )

    # 1. 승인된 PDF 파일 등록 (생성되어 있을 경우)
    if document.pdf_file and document.pdf_file.name:
        File.objects.create(
            docs=doc_record,
            file=document.pdf_file,
            file_name=f"{document.doc_number or document.title}.pdf",
            file_type="application/pdf",
            creator=document.drafter,
            description=f"전자결재 최종 승인 문서 ({document.doc_number})",
        )

    # 2. 첨부파일 등록
    for att in document.attachments.all():
        if att.file:
            File.objects.create(
                docs=doc_record,
                file=att.file,
                file_name=att.file_name or att.file.name.split('/')[-1],
                file_type=att.file_type or '',
                file_size=att.file_size,
                creator=att.creator or document.drafter,
                description="결재 첨부파일",
            )

    return doc_record
