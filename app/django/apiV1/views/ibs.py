from rest_framework import viewsets, status
from rest_framework.response import Response

from ibs.models import CalendarSchedule, AccountSort, AccountSubD1, AccountSubD2, \
    AccountSubD3, ProjectAccountD2, ProjectAccountD3, UserWidgetConfig, WiseSaying
from ..pagination import PageNumberPaginationOneHundred, PageNumberPaginationTwenty, \
    PageNumberPaginationTwoHundred, PageNumberPaginationThreeHundred
from apiV1.permissions.auth_perms import permissions, IsProjectStaffOrReadOnly, IsStaffOrReadOnly
from ..serializers.ibs import CalendarScheduleSerializer, AccountSortSerializer, AccountSubD1Serializer, \
    AccountSubD2Serializer, AccountSubD3Serializer, ProjectAccountD2Serializer, ProjectAccountD3Serializer, \
    UserWidgetConfigSerializer, WiseSaySerializer


# Ibs --------------------------------------------------------------------------
class CalendarScheduleViewSet(viewsets.ModelViewSet):
    queryset = CalendarSchedule.objects.select_related('creator').all()
    serializer_class = CalendarScheduleSerializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    pagination_class = PageNumberPaginationOneHundred
    search_fields = ('title', 'start_date', 'start_time', 'end_date', 'end_time')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class AccountSortViewSet(viewsets.ModelViewSet):
    queryset = AccountSort.objects.all()
    serializer_class = AccountSortSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class AccountSubD1ViewSet(viewsets.ModelViewSet):
    queryset = AccountSubD1.objects.prefetch_related('sorts').all()
    serializer_class = AccountSubD1Serializer
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)
    filterset_fields = ('sorts',)


class AccountSubD2ViewSet(viewsets.ModelViewSet):
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


class ProjectAccountD2ViewSet(viewsets.ModelViewSet):
    queryset = ProjectAccountD2.objects.select_related('d1').all()
    pagination_class = PageNumberPaginationTwenty
    serializer_class = ProjectAccountD2Serializer
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
    filterset_fields = ('d1__sorts', 'd1')


class ProjectAccountD3ViewSet(viewsets.ModelViewSet):
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

    def create(self, request, *args, **kwargs):
        instance = UserWidgetConfig.objects.filter(user=request.user).first()
        if instance:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)


class WiseSayViewSet(viewsets.ModelViewSet):
    queryset = WiseSaying.objects.all().order_by('id')
    serializer_class = WiseSaySerializer
    pagination_class = PageNumberPaginationThreeHundred
    permission_classes = (permissions.IsAuthenticated, IsProjectStaffOrReadOnly)
