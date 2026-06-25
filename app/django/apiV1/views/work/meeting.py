from django_filters.rest_framework import FilterSet, CharFilter, DateTimeFromToRangeFilter
from rest_framework import viewsets, permissions

from apiV1.pagination import PageNumberPaginationTwenty
from apiV1.permission import ProjectPermission
from apiV1.serializers.work.meeting import MeetingCategorySerializer, MeetingSerializer, MeetingFileSerializer
from work.models.meeting import MeetingCategory, Meeting, MeetingFile


class MeetingCategoryViewSet(viewsets.ModelViewSet):
    queryset = MeetingCategory.objects.all()
    serializer_class = MeetingCategorySerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    filterset_fields = ('project',)


class MeetingFilter(FilterSet):
    project__slug = CharFilter(field_name='project__slug', label='프로젝트')
    meeting_date = DateTimeFromToRangeFilter(field_name='meeting_date', label='회의 일시 범위')
    search = CharFilter(method='search_filter', label='검색어(제목/내용)')

    class Meta:
        model = Meeting
        fields = ('project', 'project__slug', 'category', 'status', 'meeting_date', 'search')

    @staticmethod
    def search_filter(queryset, name, value):
        return queryset.filter(title__icontains=value) | queryset.filter(content__icontains=value)


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    pagination_class = PageNumberPaginationTwenty
    filterset_class = MeetingFilter

    def get_queryset(self):
        return super().get_queryset().select_related(
            'project', 'category', 'creator', 'updater'
        ).prefetch_related('attendees', 'files')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updater=self.request.user)


class MeetingFileViewSet(viewsets.ModelViewSet):
    queryset = MeetingFile.objects.all()
    serializer_class = MeetingFileSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
