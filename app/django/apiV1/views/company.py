from rest_framework import viewsets

from ..pagination import *
from ..permission import *
from ..serializers.company import *


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
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company', 'upper_depart')
    search_fields = ('name', 'task')


class JobGradeViewSet(viewsets.ModelViewSet):
    queryset = JobGrade.objects.all()
    serializer_class = JobGradeSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company',)
    search_fields = ('name', 'promotion_period', 'positions__name', 'criteria_new')


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company',)
    search_fields = ('name',)


class DutyTitleViewSet(viewsets.ModelViewSet):
    queryset = DutyTitle.objects.all()
    serializer_class = DutyTitleSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneThousand
    filterset_fields = ('company',)
    search_fields = ('name',)


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filterset_fields = ('company', 'sort', 'department', 'grade', 'position', 'duty', 'status')
    search_fields = ('name', 'id_number', 'personal_phone', 'email')
