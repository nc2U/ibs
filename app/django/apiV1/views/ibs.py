from rest_framework import viewsets

from ibs.models import CalendarSchedule, AccountSort, AccountSubD1, AccountSubD2, \
    AccountSubD3, ProjectAccountD2, ProjectAccountD3, UserWidgetConfig, WiseSaying
from ..pagination import PageNumberPaginationOneHundred, PageNumberPaginationTwenty, \
    PageNumberPaginationTwoHundred, PageNumberPaginationThreeHundred
from apiV1.permissions.auth_perms import permissions, IsProjectStaffOrReadOnly
from ..serializers.ibs import CalendarScheduleSerializer, AccountSortSerializer, AccountSubD1Serializer, \
    AccountSubD2Serializer, AccountSubD3Serializer, ProjectAccountD2Serializer, ProjectAccountD3Serializer, \
    UserWidgetConfigSerializer, WiseSaySerializer


# Ibs --------------------------------------------------------------------------
class CalendarScheduleViewSet(viewsets.ModelViewSet):
    queryset = CalendarSchedule.objects.all()
    serializer_class = CalendarScheduleSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    search_fields = ('start_date', 'start_time', 'end_date', 'end_time')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class AccountSortViewSet(viewsets.ModelViewSet):
    queryset = AccountSort.objects.all()
    serializer_class = AccountSortSerializer


class AccountSubD1ViewSet(viewsets.ModelViewSet):
    queryset = AccountSubD1.objects.all()
    serializer_class = AccountSubD1Serializer
    filterset_fields = ('sorts',)


class AccountSubD2ViewSet(viewsets.ModelViewSet):
    queryset = AccountSubD2.objects.all()
    serializer_class = AccountSubD2Serializer
    pagination_class = PageNumberPaginationTwenty
    filterset_fields = ('d1__sorts', 'd1')


class AccountSubD3ViewSet(viewsets.ModelViewSet):
    queryset = AccountSubD3.objects.all()
    serializer_class = AccountSubD3Serializer
    pagination_class = PageNumberPaginationTwoHundred
    filterset_fields = ('sort', 'd2__d1', 'd2', 'is_hide', 'is_special')


class ProjectAccountD2ViewSet(viewsets.ModelViewSet):
    queryset = ProjectAccountD2.objects.all()
    pagination_class = PageNumberPaginationTwenty
    serializer_class = ProjectAccountD2Serializer
    filterset_fields = ('d1__sorts', 'd1')


class ProjectAccountD3ViewSet(viewsets.ModelViewSet):
    queryset = ProjectAccountD3.objects.all()
    pagination_class = PageNumberPaginationOneHundred
    serializer_class = ProjectAccountD3Serializer
    filterset_fields = ('sort', 'd2__d1', 'd2')


class UserWidgetConfigViewSet(viewsets.ModelViewSet):
    queryset = UserWidgetConfig.objects.all()
    serializer_class = UserWidgetConfigSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return UserWidgetConfig.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WiseSayViewSet(viewsets.ModelViewSet):
    queryset = WiseSaying.objects.all()
    serializer_class = WiseSaySerializer
    pagination_class = PageNumberPaginationThreeHundred
    permissions_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
