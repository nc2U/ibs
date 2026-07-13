from django.db.models import Q
from django_filters.rest_framework import FilterSet, CharFilter, DateTimeFromToRangeFilter
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apiV1.pagination import PageNumberPaginationTwenty
from apiV1.permissions.work_perms import ProjectPermission, MeetingPermission
from apiV1.serializers.work.meeting import MeetingCategorySerializer, MeetingSerializer, MeetingFileSerializer
from work.models.meeting import MeetingCategory, Meeting, MeetingFile


class MeetingCategoryViewSet(viewsets.ModelViewSet):
    queryset = MeetingCategory.objects.all()
    serializer_class = MeetingCategorySerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    filterset_fields = ('project',)

    @property
    def required_permission(self):
        mapping = {
            'create': 'project.update',
            'update': 'project.update',
            'partial_update': 'project.update',
            'destroy': 'project.update'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # 1. 슈퍼유저나 work_manager는 전체 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            base_qs = queryset
        else:
            # 2. 공개 프로젝트 OR 사용자가 멤버인 프로젝트의 카테고리만 조회
            base_qs = queryset.filter(
                Q(project__is_public=True) | Q(project__members__user=user)
            ).distinct()

        # 3. 성능 최적화
        return base_qs.select_related('project')


class MeetingFilter(FilterSet):
    project__slug = CharFilter(field_name='project__slug', label='프로젝트')
    meeting_date = DateTimeFromToRangeFilter(field_name='meeting_date', label='회의 일시 범위')
    search = CharFilter(method='search_filter', label='검색어(제목/내용)')

    class Meta:
        model = Meeting
        fields = ('project', 'project__slug', 'category', 'status', 'meeting_date', 'search')

    @staticmethod
    def search_filter(queryset, name, value):
        return queryset.filter(Q(title__icontains=value) | Q(content__icontains=value)).distinct()


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = (permissions.IsAuthenticated, MeetingPermission)
    pagination_class = PageNumberPaginationTwenty
    filterset_class = MeetingFilter

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # 1. 슈퍼유저나 work_manager는 전체 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            base_qs = queryset
        else:
            # 2. 공개 프로젝트 OR 사용자가 멤버인 프로젝트의 회의만 조회
            base_qs = queryset.filter(
                Q(project__is_public=True) | Q(project__members__user=user)
            ).distinct()

        # 3. 성능 최적화
        return base_qs.select_related(
            'project', 'category', 'creator', 'updater'
        ).prefetch_related('attendees', 'files')

    @property
    def required_permission(self):
        mapping = {  # 매핑 로직 정의
            'list': 'meeting.read',
            'retrieve': 'meeting.read',
            'create': 'meeting.create',
            'update': 'meeting.update',
            'partial_update': 'meeting.update',
            'destroy': 'meeting.delete',
            'confirm': 'meeting.confirm'
        }
        # 정의되지 않은 액션에 대해 기본 권한 반환
        return mapping.get(self.action, None)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        instance = self.get_object()

        if instance.status != '2':
            from rest_framework.exceptions import ValidationError
            raise ValidationError('회의 상태가 종료 상태인 경우에만 확정할 수 있습니다.')

        # 토글: 확정 여부 반전
        instance.is_confirmed = not instance.is_confirmed
        instance.updater = request.user
        instance.save()

        return Response({'is_confirmed': instance.is_confirmed})

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updater=self.request.user)


class MeetingFileViewSet(viewsets.ModelViewSet):
    queryset = MeetingFile.objects.all()
    serializer_class = MeetingFileSerializer
    permission_classes = (permissions.IsAuthenticated, MeetingPermission)

    @property
    def required_permission(self):
        mapping = {
            'create': 'meeting.update',
            'update': 'meeting.update',
            'partial_update': 'meeting.update',
            'destroy': 'meeting.update'
        }
        return mapping.get(self.action, None)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # 1. 슈퍼유저나 work_manager는 전체 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            base_qs = queryset
        else:
            # 2. 공개 프로젝트 OR 사용자가 멤버인 프로젝트의 회의 파일만 조회
            base_qs = queryset.filter(
                Q(meeting__project__is_public=True) | Q(meeting__project__members__user=user)
            ).distinct()

        # 3. 성능 최적화
        return base_qs.select_related('meeting__project', 'creator')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
