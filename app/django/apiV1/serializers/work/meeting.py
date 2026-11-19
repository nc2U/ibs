import logging
import json
from urllib.parse import urlparse

from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from work.models.issue import Issue
from work.models.meeting import MeetingCategory, Meeting, MeetingFile, MeetingLink
from _utils.file_service import FileService


logger = logging.getLogger(__name__)


def _validate_safe_meeting_url(raw_url: str) -> str:
    url = str(raw_url).strip()
    if not url:
        return ''
    parsed = urlparse(url)
    if not parsed.scheme:
        if ':' in url.split('/')[0]:
            raise serializers.ValidationError({'links': '허용되지 않는 URL 스킴입니다. http:// 또는 https:// 링크만 등록할 수 있습니다.'})
        url = f'https://{url}'
        parsed = urlparse(url)
    if parsed.scheme.lower() not in ('http', 'https'):
        raise serializers.ValidationError({'links': '허용되지 않는 URL 스킴입니다. http:// 또는 https:// 링크만 등록할 수 있습니다.'})
    return url


class MeetingCategorySerializer(serializers.ModelSerializer):
    project_slug = serializers.ReadOnlyField(source='project.slug')

    class Meta:
        model = MeetingCategory
        fields = ('pk', 'project', 'project_slug', 'name', 'color', 'order')


class MeetingFileSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = MeetingFile
        fields = ('pk', 'meeting', 'file', 'file_name', 'file_type',
                  'file_size', 'description', 'created', 'creator')


class MeetingLinkSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = MeetingLink
        fields = ('pk', 'meeting', 'link', 'name', 'hit', 'created', 'creator')

    def validate_link(self, value):
        return _validate_safe_meeting_url(value)


class IssueInMeetingSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(read_only=True, slug_field='slug')
    status = serializers.SlugRelatedField(read_only=True, slug_field='name')
    assigned_to = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Issue
        fields = ('pk', 'project', 'subject', 'status', 'assigned_to', 'closed')


class MeetingListSerializer(serializers.ModelSerializer):
    project_desc = SimpleIssueProjectSerializer(source='project', read_only=True)
    category_desc = MeetingCategorySerializer(source='category', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    attendees_desc = SimpleUserSerializer(source='attendees', many=True, read_only=True)
    attendees_count = serializers.IntegerField(read_only=True)
    other_attendees_count = serializers.IntegerField(read_only=True)
    total_attendees_count = serializers.IntegerField(read_only=True)
    other_attendees_list = serializers.ListField(child=serializers.CharField(), read_only=True)
    issues = IssueInMeetingSerializer(many=True, read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updater = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Meeting
        fields = ('pk', 'project', 'project_desc', 'title', 'category', 'category_desc',
                  'status', 'status_display', 'is_confirmed', 'meeting_date', 'location',
                  'attendees', 'attendees_desc', 'attendees_count',
                  'other_attendees', 'other_attendees_list', 'other_attendees_count', 'total_attendees_count',
                  'issues', 'created', 'updated', 'creator', 'updater')


class MeetingSerializer(serializers.ModelSerializer):
    project_desc = SimpleIssueProjectSerializer(source='project', read_only=True)
    category_desc = MeetingCategorySerializer(source='category', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    attendees_desc = SimpleUserSerializer(source='attendees', many=True, read_only=True)
    attendees_count = serializers.IntegerField(read_only=True)
    other_attendees_count = serializers.IntegerField(read_only=True)
    total_attendees_count = serializers.IntegerField(read_only=True)
    other_attendees_list = serializers.ListField(child=serializers.CharField(), read_only=True)
    files = MeetingFileSerializer(many=True, read_only=True)
    links = MeetingLinkSerializer(many=True, read_only=True)
    issues = IssueInMeetingSerializer(many=True, read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updater = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Meeting
        fields = ('pk', 'project', 'project_desc', 'title', 'category', 'category_desc',
                  'status', 'status_display', 'is_confirmed', 'agenda', 'content', 'decisions',
                  'action_items', 'meeting_date', 'location',
                  'attendees', 'attendees_desc', 'attendees_count',
                  'other_attendees', 'other_attendees_list', 'other_attendees_count', 'total_attendees_count',
                  'files', 'links', 'issues', 'created', 'updated', 'creator', 'updater')

    def validate(self, attrs):
        is_confirmed = attrs.get('is_confirmed', getattr(self.instance, 'is_confirmed', False) if self.instance else False)
        status = attrs.get('status', getattr(self.instance, 'status', '1') if self.instance else '1')

        if is_confirmed and status != '2':
            raise serializers.ValidationError(
                {'is_confirmed': "회의가 종료 상태(status='2')인 경우에만 확정할 수 있습니다."}
            )
        return attrs

    @staticmethod
    def _extract_initial_list(initial_data, key):
        if hasattr(initial_data, 'getlist'):
            return initial_data.getlist(key, [])
        val = initial_data.get(key, []) if isinstance(initial_data, dict) else []
        if val is None:
            return []
        return list(val) if isinstance(val, (list, tuple)) else [val]

    @transaction.atomic
    def create(self, validated_data):
        attendees = validated_data.pop('attendees', [])
        meeting = Meeting.objects.create(**validated_data)
        meeting.attendees.set(attendees)
        creator = self.context['request'].user

        # File 처리
        FileService.manage_files(
            instance=meeting,
            initial_data=self.initial_data,
            creator=creator,
            file_model=MeetingFile,
            related_name='meeting'
        )

        # Link 처리
        new_links = self._extract_initial_list(self.initial_data, 'newLinks')
        new_link_names = self._extract_initial_list(self.initial_data, 'newLinkNames')
        if not new_link_names:
            new_link_names = self._extract_initial_list(self.initial_data, 'newLinkDescs')
        for i, link in enumerate(new_links):
            if link and str(link).strip():
                safe_url = _validate_safe_meeting_url(str(link))
                name_val = new_link_names[i] if i < len(new_link_names) else ''
                MeetingLink.objects.create(meeting=meeting, link=safe_url, name=name_val, creator=creator)

        return meeting

    @transaction.atomic
    def update(self, instance, validated_data):
        attendees = validated_data.pop('attendees', None)
        instance = super().update(instance, validated_data)
        if attendees is not None:
            instance.attendees.set(attendees)
        creator = self.context['request'].user

        # File 처리
        FileService.manage_files(
            instance=instance,
            initial_data=self.initial_data,
            creator=creator,
            file_model=MeetingFile,
            related_name='meeting'
        )

        # Link 처리
        old_links = self._extract_initial_list(self.initial_data, 'links')
        for json_link in old_links:
            if not json_link or not str(json_link).strip():
                continue
            try:
                link_data = json.loads(json_link) if isinstance(json_link, str) else json_link
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"MeetingLink JSON 파싱 오류: {e}")
                continue
            link_pk = link_data.get('pk')
            if link_data.get('del'):
                MeetingLink.objects.filter(pk=link_pk, meeting=instance).delete()
            else:
                try:
                    link_obj = MeetingLink.objects.get(pk=link_pk, meeting=instance)
                except MeetingLink.DoesNotExist:
                    continue
                if 'link' in link_data:
                    link_obj.link = _validate_safe_meeting_url(link_data['link'])
                if 'name' in link_data:
                    link_obj.name = link_data['name']
                elif 'description' in link_data:
                    link_obj.name = link_data['description']
                link_obj.save()

        new_links = self._extract_initial_list(self.initial_data, 'newLinks')
        new_link_names = self._extract_initial_list(self.initial_data, 'newLinkNames')
        if not new_link_names:
            new_link_names = self._extract_initial_list(self.initial_data, 'newLinkDescs')
        for i, link in enumerate(new_links):
            if link and str(link).strip():
                safe_url = _validate_safe_meeting_url(str(link))
                name_val = new_link_names[i] if i < len(new_link_names) else ''
                MeetingLink.objects.create(meeting=instance, link=safe_url, name=name_val, creator=creator)

        return instance
