from django.db import IntegrityError, transaction
from django_filters import DateFilter, BooleanFilter
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets, status
from rest_framework.response import Response

from ibs.models import (
    CalendarSchedule, AccountSort, AccountSubD1, AccountSubD2,
    AccountSubD3, ProjectAccountD2, ProjectAccountD3, UserWidgetConfig, WiseSaying
)
from ..pagination import (
    PageNumberPaginationOneHundred, PageNumberPaginationTwenty,
    PageNumberPaginationTwoHundred, PageNumberPaginationThreeHundred
)
from apiV1.permissions.auth_perms import (
    permissions, IsProjectStaffOrReadOnly, IsStaffOrReadOnly, IsCreatorOrReadOnly
)
from ..serializers.ibs import (
    CalendarScheduleSerializer, AccountSortSerializer, AccountSubD1Serializer,
    AccountSubD2Serializer, AccountSubD3Serializer, ProjectAccountD2Serializer,
    ProjectAccountD3Serializer, UserWidgetConfigSerializer, WiseSaySerializer
)


# Ibs --------------------------------------------------------------------------
class CalendarScheduleFilterSet(FilterSet):
    start_date_from = DateFilter(field_name='start_date', lookup_expr='gte', label='시작일(이후)')
    start_date_to = DateFilter(field_name='start_date', lookup_expr='lte', label='시작일(이전)')
    end_date_from = DateFilter(field_name='end_date', lookup_expr='gte', label='종료일(이후)')
    end_date_to = DateFilter(field_name='end_date', lookup_expr='lte', label='종료일(이전)')
    all_day = BooleanFilter(field_name='all_day', label='종일 여부')

    class Meta:
        model = CalendarSchedule
        fields = ('start_date_from', 'start_date_to', 'end_date_from', 'end_date_to', 'all_day')


class CalendarScheduleViewSet(viewsets.ModelViewSet):
    queryset = CalendarSchedule.objects.select_related('creator__profile').all()
    serializer_class = CalendarScheduleSerializer
    permission_classes = (permissions.IsAuthenticated, IsCreatorOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    filterset_class = CalendarScheduleFilterSet
    search_fields = ('title', 'creator__username', 'creator__profile__name', 'start_date', 'start_time', 'end_date', 'end_time')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class AccountSortViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccountSort.objects.all()
    serializer_class = AccountSortSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class AccountSubD1ViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccountSubD1.objects.prefetch_related('sorts').all()
    serializer_class = AccountSubD1Serializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filterset_fields = ('sorts',)


class AccountSubD2ViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccountSubD2.objects.select_related('d1').all()
    serializer_class = AccountSubD2Serializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationTwenty
    filterset_fields = ('d1__sorts', 'd1')


class AccountSubD3ViewSet(viewsets.ModelViewSet):
    queryset = AccountSubD3.objects.select_related('sort', 'd2').all()
    serializer_class = AccountSubD3Serializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    pagination_class = PageNumberPaginationTwoHundred
    filterset_fields = ('sort', 'd2__d1', 'd2', 'is_hide', 'is_special')
    http_method_names = ['get', 'patch', 'head', 'options']


class ProjectAccountD2ViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProjectAccountD2.objects.select_related('d1').all()
    pagination_class = PageNumberPaginationTwenty
    serializer_class = ProjectAccountD2Serializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('d1__sorts', 'd1')


class ProjectAccountD3ViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProjectAccountD3.objects.select_related('sort', 'd2').all()
    pagination_class = PageNumberPaginationOneHundred
    serializer_class = ProjectAccountD3Serializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('sort', 'd2__d1', 'd2')


class UserWidgetConfigViewSet(viewsets.ModelViewSet):
    queryset = UserWidgetConfig.objects.all()
    serializer_class = UserWidgetConfigSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return UserWidgetConfig.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # [M-1] 동시성 요청 시 OneToOne 충돌을 방어하기 위해 select_for_update() 적용
        instance = UserWidgetConfig.objects.select_for_update().filter(user=request.user).first()
        if instance:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            instance = UserWidgetConfig.objects.select_for_update().get(user=request.user)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)


class WiseSayViewSet(viewsets.ModelViewSet):
    queryset = WiseSaying.objects.all().order_by('id')
    serializer_class = WiseSaySerializer
    pagination_class = PageNumberPaginationThreeHundred
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)

