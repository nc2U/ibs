from django.utils import timezone
from django_filters.rest_framework import FilterSet, CharFilter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apiV1.permissions.auth_perms import permissions
from apiV1.serializers.approval import (
    DocumentTypeSerializer, ApprovalDocumentSerializer,
    ApprovalDocumentListSerializer, ApprovalActionCreateSerializer,
    RoutePreviewStepSerializer,
)
from apiV1.serializers.company import StaffAssignmentSerializer
from approval.models import DocumentType, ApprovalDocument, ApprovalStep, ApprovalAction
from approval.services import build_dynamic_approval_route
from approval.tasks import notify_approvers_task, notify_drafter_task, generate_approval_pdf_task
from company.models import StaffAssignment


class DocumentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """결재 문서 유형 조회 (관리자 등록, 일반 사용자 읽기 전용)"""
    queryset = DocumentType.objects.filter(is_active=True).select_related(
        'final_approval_duty'
    ).prefetch_related('route_templates__approvers')
    serializer_class = DocumentTypeSerializer
    permission_classes = (permissions.IsAuthenticated,)


class ApprovalDocumentFilter(FilterSet):
    status = CharFilter(field_name='status', lookup_expr='exact')
    doc_type = CharFilter(field_name='doc_type__code', lookup_expr='exact')
    drafter = CharFilter(field_name='drafter__username', lookup_expr='exact')

    class Meta:
        model = ApprovalDocument
        fields = ('status', 'doc_type', 'drafter')


class ApprovalDocumentViewSet(viewsets.ModelViewSet):
    """결재 문서 CRUD + 상신/결재 액션"""
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = ApprovalDocumentFilter

    def get_queryset(self):
        user = self.request.user
        qs = ApprovalDocument.objects.select_related(
            'doc_type', 'drafter', 'drafter__profile',
            'drafter_assignment__department', 'drafter_assignment__duty', 'drafter_assignment__position',
            'workspace'
        ).prefetch_related(
            'steps__approvers__profile', 'steps__actions__approver__profile'
        )
        if user.is_superuser:
            return qs
        # 기안자이거나 결재자 중 한 명인 문서만 조회
        return (
            qs.filter(drafter=user) | qs.filter(steps__approvers=user)
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return ApprovalDocumentListSerializer
        return ApprovalDocumentSerializer

    def perform_create(self, serializer):
        user = self.request.user
        assignment = serializer.validated_data.get('drafter_assignment')
        if not assignment:
            # 주보직 자동 탐색
            assignment = StaffAssignment.objects.filter(
                staff__user=user, is_primary=True
            ).first() or StaffAssignment.objects.filter(
                staff__user=user
            ).first()

        serializer.save(
            drafter=user,
            drafter_assignment=assignment,
            status=ApprovalDocument.STATUS_DRAFT
        )

    # ── GET /approval-document/my_assignments/ ───────────────
    @action(detail=False, methods=['get'])
    def my_assignments(self, request):
        """현재 로그인 사용자의 보직/겸직 목록 조회 (기안 폼 선택용)"""
        assignments = StaffAssignment.objects.filter(
            staff__user=request.user, staff__status='1'
        ).select_related('company', 'department', 'position', 'duty')
        serializer = StaffAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    # ── GET /approval-document/preview_route/ ────────────────
    @action(detail=False, methods=['get'])
    def preview_route(self, request):
        """문서 유형과 기안 보직에 따른 결재선 실시간 미리보기"""
        doc_type_id = request.query_params.get('doc_type')
        assignment_id = request.query_params.get('assignment')

        if not doc_type_id:
            return Response({'detail': 'doc_type 파라미터가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doc_type = DocumentType.objects.prefetch_related('route_templates__approvers').get(pk=doc_type_id)
        except DocumentType.DoesNotExist:
            return Response({'detail': '문서 유형을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        assignment = None
        if assignment_id:
            assignment = StaffAssignment.objects.filter(pk=assignment_id).select_related(
                'company', 'department', 'position', 'duty'
            ).first()

        steps_data = build_dynamic_approval_route(doc_type, request.user, assignment)
        serializer = RoutePreviewStepSerializer(steps_data, many=True)
        return Response(serializer.data)

    # ── POST /approval-document/{id}/submit/ ──────────────────
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """임시저장 → 상신. 조직도 또는 템플릿 기반으로 동적 결재선 생성 후 1단계 알림"""
        document = self.get_object()
        if document.drafter != request.user:
            return Response({'detail': '기안자만 상신할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        if document.status not in (ApprovalDocument.STATUS_DRAFT, ApprovalDocument.STATUS_REJECTED):
            return Response(
                {'detail': '임시저장 또는 반려 상태에서만 상신할 수 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 기안 보직 확인
        assignment = document.drafter_assignment
        if not assignment:
            assignment = StaffAssignment.objects.filter(
                staff__user=request.user, is_primary=True
            ).first() or StaffAssignment.objects.filter(
                staff__user=request.user
            ).first()
            if assignment:
                document.drafter_assignment = assignment
                document.save(update_fields=['drafter_assignment'])

        # 동적 결재선 단계 목록 산출
        route_steps = build_dynamic_approval_route(document.doc_type, document.drafter, assignment)

        if not route_steps:
            # 결재선이 없는 경우 (예: 대표이사 본인 기안 등) -> 즉시 최종 승인 처리
            document.status = ApprovalDocument.STATUS_APPROVED
            document.completed_at = timezone.now()
            document.doc_number = document.generate_doc_number()
            document.content_hash = document.compute_hash()
            document.submitted_at = timezone.now()
            document.save()
            generate_approval_pdf_task.delay(document.pk)
            serializer = ApprovalDocumentSerializer(document, context={'request': request})
            return Response(serializer.data)

        # 재상신 시 기존 단계 초기화
        document.steps.all().delete()

        # 결재선 단계 인스턴스 복사 생성
        for step_data in route_steps:
            step = ApprovalStep.objects.create(
                document=document,
                step_order=step_data['step_order'],
                role_label=step_data['role_label'],
                condition=step_data['condition'],
                status=ApprovalStep.STATUS_PENDING,
            )
            step.approvers.set(step_data['approvers'])

        # 문서 해시 + 상태 갱신
        document.content_hash = document.compute_hash()
        document.status = ApprovalDocument.STATUS_PENDING
        document.current_step = 1
        document.submitted_at = timezone.now()
        document.save()

        # 1단계 결재자에게 알림
        first_step = document.steps.order_by('step_order').first()
        notify_approvers_task.delay(document.pk, first_step.pk)

        serializer = ApprovalDocumentSerializer(document, context={'request': request})
        return Response(serializer.data)

    # ── POST /approval-document/{id}/act/ ────────────────────
    @action(detail=True, methods=['post'])
    def act(self, request, pk=None):
        """현재 결재 단계에서 승인 / 반려 / 의견 처리"""
        document = self.get_object()
        if document.status != ApprovalDocument.STATUS_PENDING:
            return Response({'detail': '결재 진행 중인 문서가 아닙니다.'}, status=status.HTTP_400_BAD_REQUEST)

        input_ser = ApprovalActionCreateSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        act_data = input_ser.validated_data

        try:
            current_step = document.steps.get(step_order=document.current_step)
        except ApprovalStep.DoesNotExist:
            return Response({'detail': '현재 결재 단계를 찾을 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        if not current_step.approvers.filter(pk=request.user.pk).exists():
            return Response({'detail': '이 단계의 결재 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        if current_step.actions.filter(approver=request.user).exists():
            return Response({'detail': '이미 결재 처리하셨습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 결재 행동 기록
        ApprovalAction.objects.create(
            step=current_step,
            approver=request.user,
            action=act_data['action'],
            comment=act_data.get('comment', ''),
            content_hash=document.content_hash,
        )

        # AND/OR 조건 처리
        completed, approved = current_step.is_completed()
        if not completed:
            return Response({'detail': '결재가 처리되었습니다. 다른 결재자의 결재를 기다리고 있습니다.'})

        if not approved:
            # 반려
            current_step.status = ApprovalStep.STATUS_REJECTED
            current_step.save()
            document.status = ApprovalDocument.STATUS_REJECTED
            document.save()
            notify_drafter_task.delay(document.pk, 'rejected', act_data.get('comment', ''))
            return Response({'detail': '반려 처리되었습니다.'})

        # 단계 승인
        current_step.status = ApprovalStep.STATUS_APPROVED
        current_step.save()

        next_step = document.steps.filter(step_order=document.current_step + 1).first()
        if next_step:
            document.current_step += 1
            document.save()
            notify_approvers_task.delay(document.pk, next_step.pk)
            return Response({'detail': f'{next_step.role_label} 결재자에게 요청이 전달되었습니다.'})

        # 최종 승인
        document.status = ApprovalDocument.STATUS_APPROVED
        document.completed_at = timezone.now()
        document.doc_number = document.generate_doc_number()
        document.save()
        notify_drafter_task.delay(document.pk, 'approved')
        generate_approval_pdf_task.delay(document.pk)
        return Response({'detail': '최종 승인되었습니다. PDF가 생성됩니다.'})

    # ── POST /approval-document/{id}/cancel/ ─────────────────
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """기안자가 결재를 취소"""
        document = self.get_object()
        if document.drafter != request.user and not request.user.is_superuser:
            return Response({'detail': '기안자만 취소할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        if document.status == ApprovalDocument.STATUS_APPROVED:
            return Response({'detail': '최종 승인된 문서는 취소할 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        document.status = ApprovalDocument.STATUS_CANCELLED
        document.save()
        return Response({'detail': '결재가 취소되었습니다.'})

    # ── GET /approval-document/my_pending/ ───────────────────
    @action(detail=False, methods=['get'])
    def my_pending(self, request):
        """현재 사용자가 결재해야 할 대기 문서 목록 (현재 단계 한정)"""
        from django.db.models import F
        qs = ApprovalDocument.objects.filter(
            status=ApprovalDocument.STATUS_PENDING,
            steps__status=ApprovalStep.STATUS_PENDING,
            steps__step_order=F('current_step'),
            steps__approvers=request.user,
        ).select_related('doc_type', 'drafter', 'drafter__profile').distinct()

        serializer = ApprovalDocumentListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    # ── GET /approval-document/my_drafted/ ───────────────────
    @action(detail=False, methods=['get'])
    def my_drafted(self, request):
        """내가 기안한 문서 목록"""
        qs = ApprovalDocument.objects.filter(
            drafter=request.user
        ).select_related('doc_type', 'drafter', 'drafter__profile').order_by('-created_at')

        serializer = ApprovalDocumentListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)
