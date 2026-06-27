from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from work.models.meeting import Meeting, MeetingCategory, MeetingFile
from work.models.project import IssueProject
from company.models import Company
from apiV1.serializers.work.meeting import MeetingSerializer

User = get_user_model()

class MeetingSerializerTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.company = Company.objects.create(name='Test Company')
        self.project = IssueProject.objects.create(
            company=self.company,
            name='Test Project',
            slug='test-project',
            creator=self.user
        )
        self.category = MeetingCategory.objects.create(
            project=self.project,
            name='Regular Meeting',
            color='#FF0000',
            order=1
        )

    def test_meeting_creation_with_files(self):
        # Create request context
        request = self.factory.post('/')
        request.user = self.user
        
        # Prepare data
        file_content = b"file content"
        test_file = SimpleUploadedFile("test.txt", file_content)
        
        data = {
            'project': self.project.pk,
            'category': self.category.pk,
            'title': 'Test Meeting',
            'meeting_date': '2026-06-28T10:00:00Z',
        }
        
        serializer = MeetingSerializer(data=data, context={'request': request})
        
        from django.http import QueryDict
        qdict = QueryDict('', mutable=True)
        qdict.update(data)
        qdict.appendlist('new_files', test_file)
        qdict.appendlist('descriptions', 'Test description')
        
        serializer.initial_data = qdict
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # Manually set creator as the view normally does
        meeting = serializer.save(creator=self.user)
        
        self.assertEqual(Meeting.objects.count(), 1)
        self.assertEqual(meeting.title, 'Test Meeting')
        self.assertEqual(meeting.creator, self.user)
        self.assertEqual(MeetingFile.objects.filter(meeting=meeting).count(), 1)
        self.assertEqual(MeetingFile.objects.first().description, 'Test description')

    def test_meeting_update_file_logic(self):
        # Setup existing meeting with file
        meeting = Meeting.objects.create(
            project=self.project,
            category=self.category,
            title='Old Title',
            creator=self.user
        )
        
        old_file_content = b"old content"
        old_file = SimpleUploadedFile("old.txt", old_file_content)
        meeting_file = MeetingFile.objects.create(
            meeting=meeting,
            file=old_file,
            creator=self.user
        )
        
        # Update request
        request = self.factory.put('/')
        request.user = self.user
        
        # Prepare data for update
        data = {
            'title': 'New Title',
        }
        
        from django.http import QueryDict
        qdict = QueryDict('', mutable=True)
        qdict.update(data)
        
        # Simulate deleting the old file and adding a new one
        file_json = f'{{"pk": {meeting_file.pk}, "del": true}}'
        qdict.appendlist('files', file_json)
        
        new_file = SimpleUploadedFile("new.txt", b"new content")
        qdict.appendlist('new_files', new_file)
        qdict.appendlist('descriptions', 'New description')
        
        serializer = MeetingSerializer(instance=meeting, data=qdict, partial=True, context={'request': request})
        serializer.initial_data = qdict
        
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_meeting = serializer.save(updater=self.user)
        
        self.assertEqual(updated_meeting.title, 'New Title')
        
        # Check files
        files = MeetingFile.objects.filter(meeting=updated_meeting)
        self.assertEqual(files.count(), 1)
        # Check that the file was created (the name is renamed by Django)
        self.assertTrue(files.first().file.name.endswith('.txt'))
