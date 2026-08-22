from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import FilterSet, CharFilter, NumberFilter, DateFilter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from apiV1.permissions.auth_perms import permissions
from apiV1.serializers.approval import (
    DocCategorySerializer, DocumentTypeSerializer, ApprovalDocumentSerializer,
    ApprovalDocumentListSerializer, ApprovalActionCreateSerializer,
    ApprovalAttachmentSerializer, RoutePreviewStepSerializer,
    ApprovalDelegationSerializer,
)
from apiV1.serializers.company import StaffAssignmentSerializer
from approval.models import (
    DocCategory, DocumentType, ApprovalDocument, ApprovalStep, ApprovalAction, ApprovalDelegation, ApprovalAttachment
)
from approval.services import build_dynamic_approval_route
from approval.tasks import notify_approvers_task, notify_drafter_task, notify_cancel_task, generate_approval_pdf_task
from company.models import Staff, StaffAssignment


def get_active_delegator_ids(user):
    """현재 날짜 기준으로 해당 사용자에게 결재 권한을 위임한 위임자(원 결재자) ID 목록"""
    today = timezone.localdate()
    return list(ApprovalDelegation.objects.filter(
        delegatee=user,
        is_active=True,
        start_date__lte=today,
        end_date__gte=today,
    ).values_list('delegator_id', flat=True))


class ApprovalDelegationViewSet(viewsets.ModelViewSet):
    """결재 권한 위임 (부재 및 대결 설정) ViewSet"""
    serializer_class = ApprovalDelegationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ApprovalDelegation.objects.all().select_related('delegator__profile', 'delegatee__profile')
        # 내가 위임했거나(delegator) 위임받은(delegatee) 내역 조회
        return ApprovalDelegation.objects.filter(
            Q(delegator=user) | Q(delegatee=user)
        ).select_related('delegator__profile', 'delegatee__profile')

    def perform_create(self, serializer):
        # 관리자가 명시하지 않은 경우 본인을 delegator로 설정
        if 'delegator' not in serializer.validated_data or not self.request.user.is_superuser:
            serializer.save(delegator=self.request.user)
        else:
            serializer.save()


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
            assignment = StaffAssignment.objects.filter(
                pk=assignment_id, staff__user=user
            ).select_related('staff__position', 'department', 'duty').first()
        if not assignment:
            assignment = StaffAssignment.objects.filter(
                staff__user=user, is_primary=True
            ).select_related('staff__position', 'department', 'duty').first() or \
                         StaffAssignment.objects.filter(
                             staff__user=user
                         ).select_related('staff__position', 'department', 'duty').first()

        qs = self.get_queryset()

        if assignment:
            dept = assignment.department
            duty = assignment.duty
            pos = assignment.staff.position if assignment.staff else None

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
    category = NumberFilter(field_name='doc_type__category')
    doc_type = NumberFilter(field_name='doc_type')
    doc_type_code = CharFilter(field_name='doc_type__code', lookup_expr='exact')
    status = CharFilter(field_name='status', lookup_expr='exact')
    department = NumberFilter(field_name='drafter_assignment__department')
    drafter = CharFilter(field_name='drafter__username', lookup_expr='exact')
    drafter_name = CharFilter(field_name='drafter__profile__name', lookup_expr='icontains')
    start_date = DateFilter(field_name='created_at__date', lookup_expr='gte')
    end_date = DateFilter(field_name='created_at__date', lookup_expr='lte')
    search = CharFilter(method='filter_search')

    class Meta:
        model = ApprovalDocument
        fields = ('category', 'doc_type', 'doc_type_code', 'status', 'department',
                  'drafter', 'drafter_name', 'start_date', 'end_date', 'search')

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value) |
            Q(doc_number__icontains=value) |
            Q(drafter__profile__name__icontains=value) |
            Q(drafter__username__icontains=value)
        )


class ApprovalDocumentViewSet(viewsets.ModelViewSet):
    """결재 문서 CRUD + 상신/결재 액션"""
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filterset_class = ApprovalDocumentFilter

    def get_queryset(self):
        user = self.request.user
        qs = ApprovalDocument.objects.select_related(
            'doc_type', 'doc_type__category', 'drafter', 'drafter__profile',
            'drafter_assignment__department', 'drafter_assignment__duty', 'drafter_assignment__staff__position',
            'workspace'
        ).prefetch_related(
            'attachments__creator__profile',
            'observers__profile',
            'steps__approvers__profile', 'steps__actions__approver__profile',
            'steps__actions__delegated_from__profile',
        )
        if user.is_superuser:
            return qs

        # 기안자, 결재자(본인 또는 위임받은 대결자), 또는 참조자인 문서만 조회 가능
        delegator_ids = get_active_delegator_ids(user)
        approver_q = Q(steps__approvers=user)
        if delegator_ids:
            approver_q |= Q(steps__approvers__in=delegator_ids)

        return (
            qs.filter(drafter=user) | qs.filter(approver_q) | qs.filter(observers=user)
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
        ).select_related('company', 'department', 'staff__position', 'duty')
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
                'company', 'department', 'staff__position', 'duty'
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
            if assignment and assignment.duty and (assignment.duty.code == 'CEO' or assignment.duty.name == '대표이사'):
                is_ceo = True
            elif StaffAssignment.objects.filter(
                Q(duty__code='CEO') | Q(duty__name='대표이사'),
                staff__user=request.user
            ).exists():
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

        is_direct_approver = current_step.approvers.filter(pk=request.user.pk).exists()
        is_delegated = False
        delegated_from = None

        if not is_direct_approver:
            # 대결 권한 확인
            delegator_ids = get_active_delegator_ids(request.user)
            delegator_match = current_step.approvers.filter(pk__in=delegator_ids).first()
            if delegator_match:
                is_delegated = True
                delegated_from = delegator_match
            else:
                return Response({'detail': '이 단계의 결재 권한(또는 대결 권한)이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        # 이미 승인/반려 처리를 완료한 경우 재처리 불가 (단, 단순 의견 작성자는 추후 승인/반려 가능)
        existing_action_filter = Q(approver=request.user)
        if is_delegated and delegated_from:
            existing_action_filter |= Q(delegated_from=delegated_from)

        if current_step.actions.filter(
            existing_action_filter,
            action__in=[ApprovalAction.ACTION_APPROVED, ApprovalAction.ACTION_REJECTED]
        ).exists():
            return Response({'detail': '이미 승인 또는 반려 처리하셨습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 결재 행동 기록
        ApprovalAction.objects.create(
            step=current_step,
            approver=request.user,
            is_delegated=is_delegated,
            delegated_from=delegated_from,
            action=act_data['action'],
            comment=act_data.get('comment', ''),
            content_hash=document.content_hash,
        )

        # ── 단순 의견(commented) 등록인 경우: 문서 상태를 변경하지 않고 종료 ──
        if act_data['action'] == ApprovalAction.ACTION_COMMENTED:
            try:
                notify_drafter_task.delay(document.pk, 'commented', act_data.get('comment', ''))
            except Exception:
                notify_drafter_task(document.pk, 'commented', act_data.get('comment', ''))
            return Response({'detail': '결재 의견이 성공적으로 등록되었습니다.'})

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

            # 연동된 공문(OfficialLetter) 상태 동기화
            official_letter_id = (document.content or {}).get('official_letter_id')
            if official_letter_id:
                from docs.models import OfficialLetter
                OfficialLetter.objects.filter(pk=official_letter_id).update(approval_status='rejected')

            try:
                notify_drafter_task.delay(document.pk, 'rejected', act_data.get('comment', ''))
            except Exception:
                notify_drafter_task(document.pk, 'rejected', act_data.get('comment', ''))
            return Response({'detail': '반려 처리되었습니다.'})

        # 단계 승인
        current_step.status = ApprovalStep.STATUS_APPROVED
        current_step.save()

        next_step = document.steps.filter(step_order=document.current_step + 1).first()
        if next_step:
            document.current_step += 1
            document.save()
            try:
                notify_approvers_task.delay(document.pk, next_step.pk)
            except Exception:
                notify_approvers_task(document.pk, next_step.pk)
            return Response({'detail': f'{next_step.role_label} 결재자에게 요청이 전달되었습니다.'})

        # 최종 승인
        document.status = ApprovalDocument.STATUS_APPROVED
        document.completed_at = timezone.now()
        document.doc_number = document.generate_doc_number()
        document.save()

        # 연동된 공문(OfficialLetter) 상태 동기화
        official_letter_id = (document.content or {}).get('official_letter_id')
        if official_letter_id:
            from docs.models import OfficialLetter
            OfficialLetter.objects.filter(pk=official_letter_id).update(approval_status='approved')

        try:
            notify_drafter_task.delay(document.pk, 'approved')
        except Exception:
            notify_drafter_task(document.pk, 'approved')
        try:
            generate_approval_pdf_task.delay(document.pk)
        except Exception:
            generate_approval_pdf_task(document.pk)
        return Response({'detail': '최종 승인되었습니다. PDF가 생성됩니다.'})

    # ── POST /approval-document/{id}/cancel/ ─────────────────
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """기안자가 결재를 회수 (임시저장 상태로 복귀하여 수정 및 재상신 가능)"""
        document = self.get_object()
        if document.drafter != request.user and not request.user.is_superuser:
            return Response({'detail': '기안자만 회수할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        if document.status == ApprovalDocument.STATUS_APPROVED:
            return Response({'detail': '최종 승인된 문서는 회수할 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        if document.status != ApprovalDocument.STATUS_PENDING:
            return Response({'detail': '결재 진행 중인 문서만 회수할 수 있습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1차 결재자가 이미 승인한 경우 회수 제한
        first_step = document.steps.filter(step_order=1).first()
        if first_step and first_step.actions.filter(action=ApprovalAction.ACTION_APPROVED).exists():
            return Response(
                {'detail': '1차 결재자가 이미 승인을 완료하여 결재가 진행 중인 문서는 회수할 수 없습니다. 결재자에게 반려를 요청해 주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1차 결재자 및 결재선 결재자 ID 추출 (회수 알림 및 이전 알림 정리용)
        approver_ids = list(
            ApprovalStep.objects.filter(document=document).values_list('approvers__id', flat=True)
        )

        # 상태를 임시저장(DRAFT)으로 되돌리고 기존 결재선 단계 초기화
        document.status = ApprovalDocument.STATUS_DRAFT
        document.current_step = 0
        document.submitted_at = None
        document.steps.all().delete()
        document.save()

        # 결재자들에게 회수 알림 비동기 발송
        if approver_ids:
            try:
                notify_cancel_task.delay(document.pk, approver_ids)
            except Exception:
                notify_cancel_task(document.pk, approver_ids)

        return Response({'detail': '기안 문서가 성공적으로 회수되었습니다. 내용을 수정하여 다시 상신할 수 있습니다.'})

    # ── GET /approval-document/{id}/print_pdf/ ────────────────
    @action(detail=True, methods=['get'])
    def print_pdf(self, request, pk=None):
        """결재 문서 공식 PDF 렌더링 및 다운로드/미리보기"""
        from django.http import HttpResponse
        from django.template.loader import render_to_string
        from urllib.parse import quote
        try:
            from weasyprint import HTML
        except ImportError:
            return Response({'detail': 'WeasyPrint PDF 렌더러가 설정되지 않았습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        document = self.get_object()
        html_string = render_to_string('approval/pdf_document.html', {
            'document': document,
            'steps': document.steps.all().prefetch_related('actions__approver__profile', 'approvers__profile'),
            'settings': settings,
        })
        pdf_bytes = HTML(string=html_string, base_url=settings.DOMAIN_HOST).write_pdf()

        filename = f'전자결재_{document.doc_type.name}_{document.doc_number or document.pk}.pdf'
        encoded_filename = quote(filename.encode('utf-8'))

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f"inline; filename*=UTF-8''{encoded_filename}"
        return response

    # ── GET /approval-document/my_pending/ ───────────────────
    @action(detail=False, methods=['get'])
    def my_pending(self, request):
        """현재 사용자가 결재해야 할 대기 문서 목록 (대결 권한 포함)"""
        from django.db.models import F
        delegator_ids = get_active_delegator_ids(request.user)
        approver_q = Q(steps__approvers=request.user)
        if delegator_ids:
            approver_q |= Q(steps__approvers__in=delegator_ids)

        qs = ApprovalDocument.objects.filter(
            status=ApprovalDocument.STATUS_PENDING,
            steps__status=ApprovalStep.STATUS_PENDING,
            steps__step_order=F('current_step'),
        ).filter(approver_q).select_related('doc_type', 'drafter', 'drafter__profile').distinct()

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

    # ── GET /approval-document/my_observed/ ──────────────────
    @action(detail=False, methods=['get'])
    def my_observed(self, request):
        """내가 참조자로 지정된 문서 목록"""
        qs = ApprovalDocument.objects.filter(
            observers=request.user
        ).select_related(
            'doc_type', 'drafter', 'drafter__profile', 'drafter_assignment__department'
        ).distinct().order_by('-created_at', '-id')

        serializer = ApprovalDocumentListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    # ── GET /approval-document/all_documents/ ────────────────
    @action(detail=False, methods=['get'])
    def all_documents(self, request):
        """전사 결재 문서 목록 조회 (현재 슈퍼유저 전용, 페이지네이션 및 필터 지원)"""
        if not request.user.is_superuser:
            return Response({'detail': '전사 결재 문서를 조회할 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        qs = self.filter_queryset(self.get_queryset()).order_by('-created_at', '-id')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ApprovalDocumentListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

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
