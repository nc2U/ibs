import json

from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from work.models.issue import Issue
from work.models.meeting import MeetingCategory, Meeting, MeetingFile
from _utils.file_service import FileService


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


class IssueInMeetingSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(read_only=True, slug_field='slug')
    status = serializers.SlugRelatedField(read_only=True, slug_field='name')
    assigned_to = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Issue
        fields = ('pk', 'project', 'subject', 'status', 'assigned_to', 'closed')


class MeetingSerializer(serializers.ModelSerializer):
    project_desc = SimpleIssueProjectSerializer(source='project', read_only=True)
    category_desc = MeetingCategorySerializer(source='category', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    attendees_desc = SimpleUserSerializer(source='attendees', many=True, read_only=True)
    files = MeetingFileSerializer(many=True, read_only=True)
    issues = IssueInMeetingSerializer(many=True, read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updater = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Meeting
        fields = ('pk', 'project', 'project_desc', 'title', 'category', 'category_desc',
                  'status', 'status_display', 'is_confirmed', 'agenda', 'content', 'decisions',
                  'action_items', 'meeting_date', 'attendees', 'attendees_desc', 'other_attendees',
                  'files', 'issues', 'created', 'updated', 'creator', 'updater')

    def validate(self, attrs):
        is_confirmed = attrs.get('is_confirmed', getattr(self.instance, 'is_confirmed', False) if self.instance else False)
        status = attrs.get('status', getattr(self.instance, 'status', '1') if self.instance else '1')

        if is_confirmed and status != '2':
            raise serializers.ValidationError(
                {'is_confirmed': "회의가 종료 상태(status='2')인 경우에만 확정할 수 있습니다."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        attendees = validated_data.pop('attendees', [])
        meeting = Meeting.objects.create(**validated_data)
        meeting.attendees.set(attendees)

        # File 처리
        FileService.manage_files(
            instance=meeting,
            initial_data=self.initial_data,
            creator=self.context['request'].user,
            file_model=MeetingFile,
            related_name='meeting'
        )
        return meeting

    @transaction.atomic
    def update(self, instance, validated_data):
        attendees = validated_data.pop('attendees', None)
        instance = super().update(instance, validated_data)
        if attendees is not None:
            instance.attendees.set(attendees)

        # File 처리
        FileService.manage_files(
            instance=instance,
            initial_data=self.initial_data,
            creator=self.context['request'].user,
            file_model=MeetingFile,
            related_name='meeting'
        )

        return instance
