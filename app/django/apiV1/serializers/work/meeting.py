from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from work.models.meeting import MeetingCategory, Meeting, MeetingFile


class MeetingCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingCategory
        fields = ('pk', 'company', 'project', 'name', 'color', 'order')


class MeetingFileSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = MeetingFile
        fields = ('pk', 'meeting', 'file', 'file_name', 'file_type', 'file_size', 'description', 'created', 'creator')


class MeetingSerializer(serializers.ModelSerializer):
    project_desc = SimpleIssueProjectSerializer(source='project', read_only=True)
    category_desc = MeetingCategorySerializer(source='category', read_only=True)
    attendees_desc = SimpleUserSerializer(source='attendees', many=True, read_only=True)
    files = MeetingFileSerializer(many=True, read_only=True)
    creator = SimpleUserSerializer(read_only=True)
    updater = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Meeting
        fields = ('pk', 'project', 'project_desc', 'company', 'category', 'category_desc',
                  'title', 'content', 'meeting_date', 'attendees', 'attendees_desc',
                  'other_attendees', 'files', 'created', 'updated', 'creator', 'updater')
        read_only_fields = ('company',)

    def create(self, validated_data):
        # project가 있으면 company를 자동 설정 (모델 save에서도 처리하지만 시리얼라이저에서도 보강)
        project = validated_data.get('project')
        if project:
            validated_data['company'] = project.company
        
        attendees = validated_data.pop('attendees', [])
        meeting = Meeting.objects.create(**validated_data)
        meeting.attendees.set(attendees)
        return meeting

    def update(self, instance, validated_data):
        attendees = validated_data.pop('attendees', None)
        if attendees is not None:
            instance.attendees.set(attendees)
        return super().update(instance, validated_data)
