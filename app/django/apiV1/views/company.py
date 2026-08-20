from django_filters.rest_framework import FilterSet, CharFilter
from rest_framework import viewsets

from company.models import (
    Company, Logo, Department, JobGrade, Position, DutyTitle,
    ExecutiveRank, Executive, Staff, StaffAssignment,
    PromotionPolicy, StaffEvaluation, PromotionCandidate
)
from ..pagination import PageNumberPaginationOneThousand
from apiV1.permissions.auth_perms import permissions, IsSuperUserOrReadOnly, IsStaffOrReadOnly
from apiV1.permissions.ibs_perms import IbsModulePermission
from ..serializers.company import (
    CompanySerializer, LogoSerializer, DepartmentSerializer,
    JobGradeSerializer, PositionSerializer, DutyTitleSerializer,
    ExecutiveRankSerializer, ExecutiveSerializer,
    StaffSerializer, StaffAssignmentSerializer,
    PromotionPolicySerializer, StaffEvaluationSerializer, PromotionCandidateSerializer,
)


# Company --------------------------------------------------------------------------
class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperUserOrReadOnly)


class LogoViewSet(viewsets.ModelViewSet):
    queryset = Logo.objects.all()
    serializer_class = LogoSerializer
    permission_classes = (permissions.IsAuthenticated, IsSuperUserOrReadOnly)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'upper_depart')
    search_fields = ('name', 'task')

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'


class JobGradeViewSet(viewsets.ModelViewSet):
    queryset = JobGrade.objects.all()
    serializer_class = JobGradeSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company',)
    search_fields = ('code', 'role', 'min_promotion_years', 'positions__name', 'promotion_criteria')

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company',)
    search_fields = ('name',)

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'


class DutyTitleViewSet(viewsets.ModelViewSet):
    queryset = DutyTitle.objects.all()
    serializer_class = DutyTitleSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company',)
    search_fields = ('code', 'name', 'desc')

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'


class ExecutiveRankViewSet(viewsets.ModelViewSet):
    queryset = ExecutiveRank.objects.all()
    serializer_class = ExecutiveRankSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company',)
    search_fields = ('code', 'name', 'role_desc')

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'


class ExecutiveViewSet(viewsets.ModelViewSet):
    queryset = Executive.objects.all()
    serializer_class = ExecutiveSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'rank', 'director_type', 'is_registered', 'is_standing', 'represent_type')
    search_fields = ('staff__name', 'rank__name', 'note')

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'


class StaffFilter(FilterSet):
    department = CharFilter(field_name='assignments__department', lookup_expr='exact')
    position = CharFilter(field_name='position', lookup_expr='exact')
    duty = CharFilter(field_name='assignments__duty', lookup_expr='exact')

    class Meta:
        model = Staff
        fields = ('company', 'sort', 'department', 'position', 'duty', 'user', 'status')


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all().select_related(
        'position', 'grade', 'company', 'user', 'executive__rank'
    ).prefetch_related(
        'assignments__department', 'assignments__duty'
    )
    serializer_class = StaffSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_class = StaffFilter
    search_fields = ('name', 'id_number', 'personal_phone', 'email')

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'


class StaffAssignmentViewSet(viewsets.ModelViewSet):
    queryset = StaffAssignment.objects.all().select_related(
        'company', 'staff', 'department', 'duty'
    )
    serializer_class = StaffAssignmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'staff', 'department', 'duty', 'is_primary')
    search_fields = ('staff__name', 'department__name', 'assigned_tasks')

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'


# Promotion & Evaluation -----------------------------------------------------------
class PromotionPolicyViewSet(viewsets.ModelViewSet):
    queryset = PromotionPolicy.objects.all().select_related(
        'company', 'current_grade', 'target_grade'
    )
    serializer_class = PromotionPolicySerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'current_grade', 'target_grade', 'is_active')
    search_fields = ('current_grade__code', 'target_grade__code', 'required_credentials', 'disqualification_conditions')

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'


class StaffEvaluationViewSet(viewsets.ModelViewSet):
    queryset = StaffEvaluation.objects.all().select_related(
        'company', 'staff', 'evaluator', 'reviewer'
    )
    serializer_class = StaffEvaluationSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'staff', 'eval_year', 'eval_period', 'grade')
    search_fields = ('staff__name', 'achievement_summary', 'notes')

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'


class PromotionCandidateViewSet(viewsets.ModelViewSet):
    queryset = PromotionCandidate.objects.all().select_related(
        'company', 'policy__current_grade', 'policy__target_grade', 'staff'
    )
    serializer_class = PromotionCandidateSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'policy', 'staff', 'eval_year', 'status')
    search_fields = ('staff__name', 'committee_review')

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'
