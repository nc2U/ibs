from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from company.models import Company
from work.models.issue import Issue, Tracker, IssueStatus, CodeIssuePriority
from work.models.project import IssueProject, Role, Member
from work.services import IssueService

User = get_user_model()


class WorkAppTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.company = Company.objects.create(name='Test Company')

        self.project = IssueProject.objects.create(
            company=self.company,
            name='Test Project',
            slug='test-project',
            creator=self.user
        )

        self.status_open = IssueStatus.objects.create(name='Open', creator=self.user)
        self.status_closed = IssueStatus.objects.create(name='Closed', closed=True, creator=self.user)

        self.tracker = Tracker.objects.create(name='Bug', default_status=self.status_open, creator=self.user)
        self.priority = CodeIssuePriority.objects.create(name='Normal', creator=self.user)

    def test_issue_project_creation(self):
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(IssueProject.objects.count(), 1)

    def test_issue_creation_and_tracking(self):
        issue = Issue.objects.create(
            project=self.project,
            tracker=self.tracker,
            status=self.status_open,
            priority=self.priority,
            subject='Test Issue',
            start_date=timezone.now().date(),
            creator=self.user
        )
        self.assertEqual(issue.subject, 'Test Issue')
        self.assertEqual(Issue.objects.count(), 1)

    def test_issue_service_track_changes(self):
        issue = Issue.objects.create(
            project=self.project,
            tracker=self.tracker,
            status=self.status_open,
            priority=self.priority,
            subject='Original Subject',
            start_date=timezone.now().date(),
            creator=self.user
        )

        issue.subject = 'New Subject'
        IssueService.track_changes(issue)

        self.assertTrue(hasattr(issue, 'old_subject'))
        self.assertEqual(issue.old_subject, 'Original Subject')

    def test_project_all_members_optimization(self):
        role = Role.objects.create(name='Manager', creator=self.user)
        Member.objects.create(user=self.user, project=self.project)
        self.project.members.first().roles.add(role)

        members = self.project.all_members()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]['user']['username'], 'testuser')
        self.assertEqual(len(members[0]['roles']), 1)
        self.assertEqual(members[0]['roles'][0]['name'], 'Manager')

    def test_project_member_inheritance(self):
        parent_project = IssueProject.objects.create(
            company=self.company,
            name='Parent Project',
            slug='parent-project',
            creator=self.user
        )
        child_project = IssueProject.objects.create(
            company=self.company,
            name='Child Project',
            slug='child-project',
            parent=parent_project,
            is_inherit_members=True,
            creator=self.user
        )

        role = Role.objects.create(name='Manager', creator=self.user)
        Member.objects.create(user=self.user, project=parent_project)
        parent_project.members.first().roles.add(role)

        members = child_project.all_members()
        self.assertEqual(len(members), 1)
        self.assertTrue(members[0]['roles'][0]['inherited'])
