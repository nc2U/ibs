from django_filters.rest_framework import FilterSet, CharFilter
from rest_framework import viewsets

from company.models import (
    Company, Logo, CompanySeal, Department, JobGrade, Position, DutyTitle,
    ExecutiveRank, Executive, Staff, StaffAssignment,
    PersonnelOrder, StaffCareer, StaffCertificate, StaffRewardPunishment,
    StaffLeaveQuota, StaffLeaveUsage,
    PromotionPolicy, StaffEvaluation, PromotionCandidate
)
from ..pagination import PageNumberPaginationOneThousand
from apiV1.permissions.auth_perms import permissions, IsSuperUserOrReadOnly, IsStaffOrReadOnly
from apiV1.permissions.ibs_perms import HqProjectModulePermission
from ..serializers.company import (
    CompanySerializer, LogoSerializer, CompanySealSerializer, DepartmentSerializer,
    JobGradeSerializer, PositionSerializer, DutyTitleSerializer,
    ExecutiveRankSerializer, ExecutiveSerializer,
    StaffSerializer, StaffAssignmentSerializer,
    PersonnelOrderSerializer, StaffCareerSerializer, StaffCertificateSerializer, StaffRewardPunishmentSerializer,
    StaffLeaveQuotaSerializer, StaffLeaveUsageSerializer,
    PromotionPolicySerializer, StaffEvaluationSerializer, PromotionCandidateSerializer,
)


class CompanyDataFilterMixin:
    """
    인사/조직 데이터의 소속 회사(user.staff.company) 격리 필터 믹스인.
    슈퍼유저 또는 work_manager는 모든 회사 데이터를 조회/관리할 수 있으며,
    일반 사용자는 자신이 소속된 회사의 데이터만 조회/관리할 수 있습니다.
    소속 회사가 없는 경우 빈 쿼리셋을 반환합니다.
    """
    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if not user or not user.is_authenticated:
            return qs.none()
        if user.is_superuser or getattr(user, 'work_manager', False):
            return qs
        staff = getattr(user, 'staff', None)
        if staff and staff.company_id:
            return qs.filter(company_id=staff.company_id)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_superuser or getattr(user, 'work_manager', False)):
            staff = getattr(user, 'staff', None)
            if staff and staff.company:
                serializer.save(company=staff.company)
                return
        serializer.save()


# Company --------------------------------------------------------------------------
class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperUserOrReadOnly)


class LogoViewSet(viewsets.ModelViewSet):
    queryset = Logo.objects.all()
    serializer_class = LogoSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperUserOrReadOnly)


class CompanySealViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = CompanySeal.objects.all()
    serializer_class = CompanySealSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'seal_type', 'is_active')
    search_fields = ('name', 'manager')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class DepartmentViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'upper_depart')
    search_fields = ('name', 'task')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class JobGradeViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = JobGrade.objects.all()
    serializer_class = JobGradeSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company',)
    search_fields = ('code', 'role', 'min_promotion_years', 'positions__name', 'promotion_criteria')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class PositionViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company',)
    search_fields = ('name',)

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class DutyTitleViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = DutyTitle.objects.all()
    serializer_class = DutyTitleSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company',)
    search_fields = ('code', 'name', 'desc')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class ExecutiveRankViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = ExecutiveRank.objects.all()
    serializer_class = ExecutiveRankSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company',)
    search_fields = ('code', 'name', 'role_desc')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class ExecutiveViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = Executive.objects.all()
    serializer_class = ExecutiveSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'rank', 'director_type', 'is_registered', 'is_standing', 'represent_type')
    search_fields = ('staff__name', 'rank__name', 'note')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class StaffFilter(FilterSet):
    department = CharFilter(field_name='assignments__department', lookup_expr='exact')
    position = CharFilter(field_name='position', lookup_expr='exact')
    duty = CharFilter(field_name='assignments__duty', lookup_expr='exact')

    class Meta:
        model = Staff
        fields = ('company', 'sort', 'employment_type', 'department', 'position', 'duty', 'user', 'status')


class StaffViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = Staff.objects.all().select_related(
        'position', 'grade', 'company', 'user', 'executive__rank'
    ).prefetch_related(
        'assignments__department', 'assignments__duty'
    )
    serializer_class = StaffSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_class = StaffFilter
    search_fields = ('name', 'id_number', 'personal_phone', 'email')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class StaffAssignmentViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = StaffAssignment.objects.all().select_related(
        'company', 'staff', 'department', 'duty'
    )
    serializer_class = StaffAssignmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'staff', 'department', 'duty', 'is_primary')
    search_fields = ('staff__name', 'department__name', 'assigned_tasks')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class PersonnelOrderViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = PersonnelOrder.objects.all().select_related(
        'company', 'staff', 'prev_department', 'prev_grade', 'prev_position', 'prev_duty',
        'new_department', 'new_grade', 'new_position', 'new_duty'
    )
    serializer_class = PersonnelOrderSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'staff', 'order_type', 'is_processed', 'new_department')
    search_fields = ('staff__name', 'order_no', 'description')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class StaffCareerViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = StaffCareer.objects.all().select_related('company', 'staff')
    serializer_class = StaffCareerSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'staff')
    search_fields = ('staff__name', 'company_name', 'assigned_tasks')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class StaffCertificateViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = StaffCertificate.objects.all().select_related('company', 'staff')
    serializer_class = StaffCertificateSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'staff', 'has_allowance')
    search_fields = ('staff__name', 'name', 'grade', 'cert_number', 'issuer')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class StaffRewardPunishmentViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = StaffRewardPunishment.objects.all().select_related('company', 'staff')
    serializer_class = StaffRewardPunishmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'staff', 'sort')
    search_fields = ('staff__name', 'type_name', 'reason', 'organization')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class StaffLeaveQuotaViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = StaffLeaveQuota.objects.all().select_related('company', 'staff')
    serializer_class = StaffLeaveQuotaSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'staff', 'year')
    search_fields = ('staff__name', 'note')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class StaffLeaveUsageViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = StaffLeaveUsage.objects.all().select_related('company', 'staff', 'approval_doc')
    serializer_class = StaffLeaveUsageSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'staff', 'leave_type', 'is_cancelled')
    search_fields = ('staff__name', 'reason')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


# Promotion & Evaluation -----------------------------------------------------------
class PromotionPolicyViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = PromotionPolicy.objects.all().select_related(
        'company', 'current_grade', 'target_grade'
    )
    serializer_class = PromotionPolicySerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'current_grade', 'target_grade', 'is_active')
    search_fields = ('current_grade__code', 'target_grade__code', 'required_credentials', 'disqualification_conditions')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class StaffEvaluationViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = StaffEvaluation.objects.all().select_related(
        'company', 'staff', 'evaluator', 'reviewer'
    )
    serializer_class = StaffEvaluationSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'staff', 'eval_year', 'eval_period', 'grade')
    search_fields = ('staff__name', 'achievement_summary', 'notes')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'


class PromotionCandidateViewSet(CompanyDataFilterMixin, viewsets.ModelViewSet):
    queryset = PromotionCandidate.objects.all().select_related(
        'company', 'policy__current_grade', 'policy__target_grade', 'staff'
    )
    serializer_class = PromotionCandidateSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, HqProjectModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'policy', 'staff', 'eval_year', 'status')
    search_fields = ('staff__name', 'committee_review')

    @property
    def required_permission(self):
        return 'hq.hr_work.read' if self.action in ('list', 'retrieve') else 'hq.hr_work.create' if self.action == 'create' else 'hq.hr_work.update' if self.action in ('update', 'partial_update') else 'hq.hr_work.delete' if self.action == 'destroy' else 'hq.hr_work.read'

