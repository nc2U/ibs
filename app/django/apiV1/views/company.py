from rest_framework import viewsets

from company.models import Company, Logo, Department, JobGrade, Position, DutyTitle, Staff
from ..pagination import PageNumberPaginationOneThousand
from apiV1.permissions.auth_perms import permissions, IsSuperUserOrReadOnly, IsStaffOrReadOnly
from apiV1.permissions.ibs_perms import IbsModulePermission
from ..serializers.company import CompanySerializer, LogoSerializer, DepartmentSerializer, \
    JobGradeSerializer, PositionSerializer, DutyTitleSerializer, StaffSerializer


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
    search_fields = ('name', 'promotion_period', 'positions__name', 'criteria_new')

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
    search_fields = ('name',)

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IbsModulePermission)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'sort', 'department', 'user', 'status')
    search_fields = ('name', 'id_number', 'personal_email', 'company_email')

    @property
    def required_permission(self):
        return 'hr_work.read' if self.action in ('list', 'retrieve') else 'hr_work.create' if self.action == 'create' else 'hr_work.update' if self.action in ('update', 'partial_update') else 'hr_work.delete' if self.action == 'destroy' else 'hr_work.read'
