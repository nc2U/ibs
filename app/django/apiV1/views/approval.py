from django.utils import timezone
from django_filters.rest_framework import FilterSet, CharFilter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from apiV1.permissions.auth_perms import permissions
from apiV1.serializers.approval import (
    DocCategorySerializer, DocumentTypeSerializer, ApprovalDocumentSerializer,
    ApprovalDocumentListSerializer, ApprovalActionCreateSerializer,
    ApprovalAttachmentSerializer, RoutePreviewStepSerializer,
)
from apiV1.serializers.company import StaffAssignmentSerializer
from approval.models import (
    DocCategory, DocumentType, ApprovalDocument, ApprovalStep, ApprovalAction, ApprovalAttachment
)
from approval.services import build_dynamic_approval_route
from approval.tasks import notify_approvers_task, notify_drafter_task, generate_approval_pdf_task
from company.models import Staff, StaffAssignment


class DocCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """결재 문서 카테고리 조회"""
    queryset = DocCategory.objects.filter(is_active=True).order_by('order', 'id')
    serializer_class = DocCategorySerializer
    permission_classes = (permissions.IsAuthenticated,)


class DocumentTypeFilter(FilterSet):
    category = CharFilter(field_name='category__code', lookup_expr='exact')
    category_id = CharFilter(field_name='category__id', lookup_expr='exact')

    class Meta:
        model = DocumentType
        fields = ('category', 'category_id', 'is_active')


class DocumentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """결재 문서 유형 조회 (관리자 등록, 일반 사용자 읽기 전용)"""
    queryset = DocumentType.objects.filter(is_active=True).select_related(
        'category', 'final_approval_duty'
    ).prefetch_related(
        'policy_rules__final_approval_duty',
        'route_templates__approvers',
        'allowed_departments', 'allowed_duties', 'allowed_positions'
    )
    serializer_class = DocumentTypeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = DocumentTypeFilter

    @action(detail=False, methods=['get'])
    def for_draft(self, request):
        """현재 사용자의 보직(소속 부서/직책)에 따라 기안 가능한 문서 유형만 필터링하여 반환"""
        assignment_id = request.query_params.get('assignment')
        user = request.user

        assignment = None
        if assignment_id:
            assignment = StaffAssignment.objects.filter(pk=assignment_id, staff__user=user).first()
        if not assignment:
            assignment = StaffAssignment.objects.filter(staff__user=user, is_primary=True).first() or \
                         StaffAssignment.objects.filter(staff__user=user).first()

        qs = self.get_queryset()

        if assignment:
            dept = assignment.department
            duty = assignment.duty
            pos = assignment.position

            # 부서 제한 필터: allowed_departments가 비어있거나, 해당 부서가 포함된 경우
            # (Q 객체 조합 또는 Python 리스트 필터링)
            available_types = []
            for dt in qs:
                # 1. 부서 검사
                dept_allowed = not dt.allowed_departments.exists() or (dept and dt.allowed_departments.filter(pk=dept.pk).exists())
                # 2. 직책 검사
                duty_allowed = not dt.allowed_duties.exists() or (duty and dt.allowed_duties.filter(pk=duty.pk).exists())
                # 3. 직위 검사
                pos_allowed = not dt.allowed_positions.exists() or (pos and dt.allowed_positions.filter(pk=pos.pk).exists())

                if dept_allowed and duty_allowed and pos_allowed:
                    available_types.append(dt)

            serializer = self.get_serializer(available_types, many=True)
            return Response(serializer.data)

        # 보직이 없는 경우 전사 공통(제한 없는) 문서만 반환
        common_types = [dt for dt in qs if not dt.allowed_departments.exists() and not dt.allowed_duties.exists() and not dt.allowed_positions.exists()]
        serializer = self.get_serializer(common_types, many=True)
        return Response(serializer.data)


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
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filterset_class = ApprovalDocumentFilter

    def get_queryset(self):
        user = self.request.user
        qs = ApprovalDocument.objects.select_related(
            'doc_type', 'drafter', 'drafter__profile',
            'drafter_assignment__department', 'drafter_assignment__duty', 'drafter_assignment__position',
            'workspace'
        ).prefetch_related(
            'attachments__creator__profile',
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
        """문서 유형과 기안 보직 및 금액(amount)에 따른 결재선 실시간 미리보기"""
        doc_type_id = request.query_params.get('doc_type')
        assignment_id = request.query_params.get('assignment')
        amount = request.query_params.get('amount')

        if not doc_type_id:
            return Response({'detail': 'doc_type 파라미터가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doc_type = DocumentType.objects.prefetch_related(
                'policy_rules__final_approval_duty', 'route_templates__approvers'
            ).get(pk=doc_type_id)
        except DocumentType.DoesNotExist:
            return Response({'detail': '문서 유형을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        assignment = None
        if assignment_id:
            assignment = StaffAssignment.objects.filter(pk=assignment_id).select_related(
                'company', 'department', 'position', 'duty'
            ).first()

        content = {'amount': amount} if amount else None
        steps_data = build_dynamic_approval_route(doc_type, request.user, assignment, content)
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

        # 동적 결재선 단계 목록 산출 (금액/내용 포함)
        route_steps = build_dynamic_approval_route(
            document.doc_type, document.drafter, assignment, document.content
        )

        if not route_steps:
            # 기안자가 대표이사 본인인지 확인
            is_ceo = False
            if assignment and assignment.duty and assignment.duty.name == '대표이사':
                is_ceo = True
            elif StaffAssignment.objects.filter(staff__user=request.user, duty__name='대표이사').exists():
                is_ceo = True

            if is_ceo:
                # 대표이사 본인 기안인 경우 -> 즉시 최종 승인 처리
                document.status = ApprovalDocument.STATUS_APPROVED
                document.completed_at = timezone.now()
                document.doc_number = document.generate_doc_number()
                document.content_hash = document.compute_hash()
                document.submitted_at = timezone.now()
                document.save()
                generate_approval_pdf_task.delay(document.pk)
                serializer = ApprovalDocumentSerializer(document, context={'request': request})
                return Response(serializer.data)
            else:
                # 일반 직원의 결재선이 0단계로 나온 경우 (조직도/부서장/대표이사 계정 미연동) -> 상신 차단
                return Response(
                    {'detail': '지정된 결재선이 없습니다. 소속 부서의 책임자(부서장) 또는 대표이사 계정 연동 상태를 확인해 주세요.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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

    # ── GET /approval-document/my_approved/ ──────────────────
    @action(detail=False, methods=['get'])
    def my_approved(self, request):
        """내가 결재에 참여하여 최종 승인된 문서 목록"""
        qs = ApprovalDocument.objects.filter(
            status=ApprovalDocument.STATUS_APPROVED,
            steps__approvers=request.user,
        ).select_related(
            'doc_type', 'drafter', 'drafter__profile', 'drafter_assignment__department'
        ).distinct().order_by('-completed_at', '-id')

        serializer = ApprovalDocumentListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class ApprovalAttachmentViewSet(viewsets.ModelViewSet):
    """결재 문서 첨부파일 개별 관리 (업로드 / 삭제)"""
    queryset = ApprovalAttachment.objects.all().select_related('document', 'creator')
    serializer_class = ApprovalAttachmentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filterset_fields = ('document',)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_destroy(self, instance):
        # 기안자 또는 슈퍼유저만 삭제 가능 (결재 완료 전)
        doc = instance.document
        user = self.request.user
        if not user.is_superuser and doc.drafter != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('기안자만 첨부파일을 삭제할 수 있습니다.')
        if doc.status == ApprovalDocument.STATUS_APPROVED:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('최종 승인된 문서의 첨부파일은 삭제할 수 없습니다.')
        instance.delete()
