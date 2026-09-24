from django.db.models import Q
from django_filters.rest_framework import (
    FilterSet, CharFilter, BooleanFilter, NumberFilter, DateTimeFromToRangeFilter
)
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apiV1.pagination import PageNumberPaginationTwenty
from apiV1.permissions.work_perms import ProjectPermission, MeetingPermission
from apiV1.serializers.work.meeting import (
    MeetingCategorySerializer, MeetingSerializer, MeetingListSerializer, MeetingFileSerializer
)
from work.models.meeting import MeetingCategory, Meeting, MeetingFile


class MeetingCategoryFilter(FilterSet):
    project = CharFilter(method='filter_project', label='프로젝트 PK 또는 슬러그')
    project__slug = CharFilter(method='filter_project', label='프로젝트 슬러그')

    class Meta:
        model = MeetingCategory
        fields = ('project', 'project__slug')

    def filter_project(self, queryset, name, value):
        if not value:
            return queryset
        if str(value).isdigit():
            return queryset.filter(Q(project__isnull=True) | Q(project_id=int(value)))
        return queryset.filter(Q(project__isnull=True) | Q(project__slug=value))


class MeetingCategoryViewSet(viewsets.ModelViewSet):
    queryset = MeetingCategory.objects.all()
    serializer_class = MeetingCategorySerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    filterset_class = MeetingCategoryFilter

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

        # 1. 슈퍼유저나 work_manager는 전체 조회 가능 (FilterSet에서 공용 + 해당 워크스페이스로 필터링)
        if user.is_superuser or getattr(user, 'work_manager', False):
            base_qs = queryset
        else:
            # 2. 일반 사용자: 공용 카테고리 OR 공개 프로젝트 OR 사용자가 멤버인 프로젝트 카테고리
            base_qs = queryset.filter(
                Q(project__isnull=True) | Q(project__is_public=True) | Q(project__members__user=user)
            ).distinct()

        # 3. 정렬 및 최적화
        return base_qs.select_related('project').order_by('order', 'id')


class MeetingFilter(FilterSet):
    project__slug = CharFilter(field_name='project__slug', label='프로젝트')
    project__search = CharFilter(field_name='project__slug', label='프로젝트-검색')
    status__exclude = CharFilter(field_name='status', exclude=True, label='상태-제외')
    category__exclude = NumberFilter(field_name='category', exclude=True, label='카테고리-제외')
    creator__exclude = NumberFilter(field_name='creator__pk', exclude=True, label='작성자-제외')
    attendees__exclude = NumberFilter(field_name='attendees__pk', exclude=True, label='참석자-제외')
    meeting_date = DateTimeFromToRangeFilter(field_name='meeting_date', label='회의 일시 범위')
    created = DateTimeFromToRangeFilter(field_name='created', label='등록일 범위')
    creator = NumberFilter(field_name='creator__pk', label='작성자')
    attendees = NumberFilter(field_name='attendees__pk', label='참석자')
    is_confirmed = BooleanFilter(field_name='is_confirmed', label='확정 여부')
    search = CharFilter(method='search_filter', label='검색어(제목/의제/내용/결정사항)')

    project__my_project = BooleanFilter(method='filter_my_project', label='내 프로젝트 회의 여부')
    project__bookmark = BooleanFilter(method='filter_bookmark', label='북마크 프로젝트 회의 여부')
    project_status = CharFilter(field_name='project__status', lookup_expr='exact', label='프로젝트상태-일치')
    project_status__exclude = CharFilter(field_name='project__status', exclude=True, label='프로젝트상태-제외')

    def filter_my_project(self, queryset, name, value):
        if self.request and self.request.user.is_authenticated:
            user = self.request.user
            if user.is_superuser or getattr(user, 'work_manager', False):
                return queryset
            if value:
                return queryset.filter(project__members__user=user)
            else:
                return queryset.exclude(project__members__user=user)
        return queryset

    def filter_bookmark(self, queryset, name, value):
        if self.request and self.request.user.is_authenticated:
            user = self.request.user
            if value:
                return queryset.filter(project__bookmarked_by__user=user)
            else:
                return queryset.exclude(project__bookmarked_by__user=user)
        return queryset

    class Meta:
        model = Meeting
        fields = (
            'project', 'project__slug', 'category', 'status', 'status__exclude', 'is_confirmed',
            'creator', 'creator__exclude', 'attendees', 'attendees__exclude',
            'meeting_date', 'created', 'search', 'project__my_project', 'project__bookmark',
            'project_status', 'project_status__exclude',
        )

    @staticmethod
    def search_filter(queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value)
            | Q(agenda__icontains=value)
            | Q(content__icontains=value)
            | Q(decisions__icontains=value)
        ).distinct()


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = (permissions.IsAuthenticated, MeetingPermission)
    pagination_class = PageNumberPaginationTwenty
    filterset_class = MeetingFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return MeetingListSerializer
        return MeetingSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().exclude(project__status='9')

        # 1. 슈퍼유저나 work_manager는 전체 조회 가능
        if user.is_superuser or getattr(user, 'work_manager', False):
            base_qs = queryset
        else:
            # 2. 공개 프로젝트 OR 사용자가 멤버인 프로젝트의 회의만 조회
            base_qs = queryset.filter(
                Q(project__is_public=True) | Q(project__members__user=user)
            ).distinct()

        # 3. 성능 최적화: 목록 조회 시 필수 관계만, 상세 조회 시 파일/링크/연계업무까지 prefetch
        base_qs = base_qs.select_related('project', 'category', 'creator', 'updater')
        if self.action == 'list':
            return base_qs.prefetch_related('attendees')
        return base_qs.prefetch_related(
            'attendees', 'files', 'links', 'issues__assigned_to', 'issues__project'
        )

    @property
    def required_permission(self):
        mapping = {  # 매핑 로직 정의
            'list': 'meeting.read',
            'retrieve': 'meeting.read',
            'create': 'meeting.create',
            'update': 'meeting.update',
            'partial_update': 'meeting.update',
            'destroy': 'meeting.delete',
            'confirm': 'meeting.confirm',
            'ai_summarize': 'meeting.create',
        }
        # 정의되지 않은 액션에 대해 기본 권한 반환
        return mapping.get(self.action, None)

    @action(detail=False, methods=['post'], url_path='ai-summarize')
    def ai_summarize(self, request):
        """
        클라이언트(웹/모바일)에서 업로드한 회의 음성 녹음 파일을 전달받아
        Gemini 1.5 Flash를 통해 STT 및 회의록(제목, 카테고리, 의제, 본문, 결정사항, 액션아이템)을 추출합니다.
        완료 후 서버의 임시 파일은 즉시 삭제되어 스토리지를 점유하지 않습니다.
        """
        audio_file = request.FILES.get('audio')
        if not audio_file:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'audio': '음성 녹음 파일(audio)이 전송되지 않았습니다.'})

        mime_type = audio_file.content_type or 'audio/webm'
        if 'octet-stream' in mime_type:
            # 확장자 기반 mime-type 추론
            name_lower = audio_file.name.lower()
            if name_lower.endswith('.m4a'):
                mime_type = 'audio/mp4'
            elif name_lower.endswith('.mp3'):
                mime_type = 'audio/mp3'
            elif name_lower.endswith('.wav'):
                mime_type = 'audio/wav'
            else:
                mime_type = 'audio/webm'

        try:
            from work.services.meeting_ai_service import summarize_meeting_audio
            audio_bytes = audio_file.read()
            summary_result = summarize_meeting_audio(audio_bytes, mime_type=mime_type)
            return Response(summary_result)
        except Exception as e:
            from rest_framework.exceptions import APIException
            raise APIException(f'AI 회의록 생성 중 오류가 발생했습니다: {str(e)}')
        finally:
            # 안전한 메모리/임시 파일 정리
            if hasattr(audio_file, 'close'):
                audio_file.close()

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
