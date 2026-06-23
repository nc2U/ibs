import json

from django.db import transaction
from rest_framework import serializers

from apiV1.serializers.accounts import SimpleUserSerializer
from apiV1.serializers.work.project import SimpleIssueProjectSerializer
from work.models.issue import Issue
from work.models.meeting import MeetingCategory, Meeting, MeetingFile


class MeetingCategorySerializer(serializers.ModelSerializer):
    project_slug = serializers.ReadOnlyField(source='project.slug')

    class Meta:
        model = MeetingCategory
        fields = ('pk', 'project', 'project_slug', 'name', 'color', 'order')


class MeetingFileSerializer(serializers.ModelSerializer):
    creator = SimpleUserSerializer(read_only=True)

    class Meta:
        model = MeetingFile
        fields = ('pk', 'meeting', 'file', 'file_name', 'file_type', 'file_size', 'description', 'created', 'creator')


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
        fields = ('pk', 'project', 'project_desc', 'category', 'category_desc',
                  'status', 'status_display', 'title', 'agenda', 'content', 'decisions',
                  'action_items', 'meeting_date', 'attendees', 'attendees_desc',
                  'other_attendees', 'files', 'issues', 'created', 'updated', 'creator', 'updater')

    @transaction.atomic
    def create(self, validated_data):
        attendees = validated_data.pop('attendees', [])
        meeting = Meeting.objects.create(**validated_data)
        meeting.attendees.set(attendees)

        # File 처리
        creator = self.context['request'].user
        new_files = self.initial_data.getlist('new_files', [])
        descriptions = self.initial_data.getlist('descriptions', [])
        if new_files:
            for i, file in enumerate(new_files):
                meeting_file = MeetingFile(meeting=meeting, file=file,
                                           description=descriptions[i], creator=creator)
                meeting_file.save()
        return meeting

    @transaction.atomic
    def update(self, instance, validated_data):
        attendees = validated_data.pop('attendees', None)
        instance = super().update(instance, validated_data)
        if attendees is not None:
            instance.attendees.set(attendees)

        # File 처리
        creator = self.context['request'].user

        # 신규 파일 추가
        new_files = self.initial_data.getlist('new_files', [])
        descriptions = self.initial_data.getlist('descriptions', [])

        for i, upload_file in enumerate(new_files):
            MeetingFile.objects.create(
                meeting=instance,
                file=upload_file,
                description=descriptions[i] if i < len(descriptions) else None,
                creator=creator)

        # 기존 파일 수정/삭제
        old_files = self.initial_data.getlist('files', [])

        for json_file in old_files:
            file_data = json.loads(json_file)

            if file_data.get('del'):
                MeetingFile.objects.filter(
                    pk=file_data.get('pk'),
                    meeting=instance
                ).delete()

        # 단일 파일 수정
        edit_file = self.initial_data.get('edit_file')
        cng_file = self.initial_data.get('cng_file')
        edit_file_desc = self.initial_data.get('edit_file_desc')

        if edit_file:
            meeting_file = MeetingFile.objects.get(pk=edit_file, meeting=instance)
            old_file = None
            if cng_file:
                old_file = meeting_file.file

                # 새 파일 등록
                meeting_file.file = cng_file

            if edit_file_desc is not None:
                meeting_file.description = edit_file_desc

            meeting_file.save()

            # DB 커밋 성공 후 기존 파일 삭제
            if old_file and old_file.name:
                transaction.on_commit(lambda f=old_file: f.delete(save=False))

        # 단일 파일 삭제
        del_file = self.initial_data.get('del_file')
        if del_file:
            MeetingFile.objects.get(pk=del_file, meeting=instance).delete()

        # 다중 파일 삭제
        files_del = self.initial_data.getlist('files_del')
        if files_del:
            MeetingFile.objects.filter(pk__in=files_del, meeting=instance).delete()

        return instance
