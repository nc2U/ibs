from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from _utils.push_service import send_push_notification
from work.models.meeting import Meeting
from work.models.issue import Issue

User = get_user_model()


@shared_task
def send_meeting_mail_task(meeting_pk, user_pk, mail_type):
    """Celery task to send meeting-related emails & push notifications asynchronously"""
    try:
        instance = Meeting.objects.select_related('project', 'creator__profile').get(pk=meeting_pk)
        user = User.objects.get(pk=user_pk)

        # 참석자 및 작성자 수신자 구성
        creator = instance.creator
        attendees = list(instance.attendees.select_related('profile').all())
        candidate_users = set([creator] + attendees)

        recipients = set()
        recipient_user_ids = set()
        for u in candidate_users:
            profile = getattr(u, 'profile', None)
            if mail_type == "create":
                if profile is None or getattr(profile, 'meeting_created_notification', True):
                    recipients.add(u.email)
                    recipient_user_ids.add(u.pk)
            elif mail_type == "confirm":
                if profile is None or getattr(profile, 'meeting_confirmed_notification', True):
                    recipients.add(u.email)
                    recipient_user_ids.add(u.pk)

        addresses = list(recipients)

        if mail_type == "create":
            subject = f'『 {instance.project} 』 - 새 회의록 :: "{instance.title}"'
            template = 'mail/meeting_create.html'
            push_title = f'[회의 등록] {instance.project}'
            push_body = f'새 회의록이 등록되었습니다: "{instance.title}"'
        elif mail_type == "confirm":
            subject = f'『 {instance.project} 』 - 회의 확정 :: "{instance.title}"'
            template = 'mail/meeting_confirm.html'
            push_title = f'[회의 확정] {instance.project}'
            push_body = f'회의록이 확정되었습니다: "{instance.title}"'
        else:
            return

        context = {
            'instance': instance,
            'settings': settings,
            'user': user,
        }
        message = render_to_string(template, context)

        # 1. 이메일 발송
        if addresses:
            send_mail(
                subject=subject,
                message=message,
                html_message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=addresses
            )

        # 2. 모바일 푸시 및 인앱 알림 발송
        if recipient_user_ids:
            send_push_notification(
                user_ids=list(recipient_user_ids),
                title=push_title,
                body=push_body,
                category='meeting',
                target_type='meeting',
                target_id=str(instance.pk),
                extra_data={'meeting_id': str(instance.pk), 'project_id': str(instance.project_id)},
            )
    except Exception as e:
        print(f"❌ Async meeting notification task failed: {e}")


@shared_task
def send_issue_mail_task(issue_pk, user_pk, mail_type, old_status_name=None, old_assigned_to=None):
    """Celery task to send issue-related emails & push notifications asynchronously"""
    try:
        instance = Issue.objects.select_related('project', 'tracker', 'status', 'assigned_to').get(pk=issue_pk)
        user = User.objects.get(pk=user_pk)
        watchers = list(instance.watchers.all())

        recipient_user_ids = set()

        # 수신자 목록 구성
        if mail_type == "create":
            addresses = []
            creator_profile = getattr(user, 'profile', None)
            if getattr(creator_profile, 'auto_watch_created', True) if creator_profile else True:
                addresses.append(user.email)
                recipient_user_ids.add(user.pk)
            if instance.assigned_to:
                assignee = instance.assigned_to
                assignee_profile = getattr(assignee, 'profile', None)
                if getattr(assignee_profile, 'auto_watch_assigned', True) if assignee_profile else True:
                    addresses.append(assignee.email)
                    recipient_user_ids.add(assignee.pk)
            subject = f'『 {instance.project} 』 - 새 업무 :: [#{instance.pk}] "{instance.subject}"이(가) 할당되었습니다.' if instance.assigned_to else f'『 {instance.project} 』 - 새 업무 :: [#{instance.pk}] "{instance.subject}"이(가) 생성되었습니다.'
            template = 'mail/issue_create.html'
            push_title = f'[업무 할당] {instance.project}' if instance.assigned_to else f'[새 업무] {instance.project}'
            push_body = f'[#{instance.pk}] {instance.subject}'
        elif mail_type == "progress":
            addresses = [watcher.email for watcher in watchers]
            recipient_user_ids = set(w.pk for w in watchers)
            subject = f'『 {instance.project} 』 - 업무 :: [#{instance.pk}] "{instance.subject}"의 상태가 {instance.status}(으)로 변경되었습니다.'
            template = 'mail/issue_progress.html'
            push_title = f'[업무 진행] {instance.project}'
            push_body = f'[#{instance.pk}] 상태가 "{instance.status}"(으)로 변경되었습니다.'
        elif mail_type == "reassign":
            addresses = [watcher.email for watcher in watchers]
            recipient_user_ids = set(w.pk for w in watchers)
            subject = f'『 {instance.project} 』 - 업무 :: [#{instance.pk}] "{instance.subject}"의 담당자가 변경되었습니다.'
            template = 'mail/issue_reassign.html'
            push_title = f'[담당자 변경] {instance.project}'
            push_body = f'[#{instance.pk}] 담당자가 "{instance.assigned_to}"(으)로 변경되었습니다.'
        else:
            return

        context = {
            'instance': instance,
            'settings': settings,
            'user': user,
            'old_status_name': old_status_name,
            'old_assigned_to': old_assigned_to,
            'watchers': watchers if mail_type != "create" else None,
        }
        message = render_to_string(template, context)

        # 1. 이메일 발송
        if addresses:
            send_mail(
                subject=subject,
                message=message,
                html_message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=addresses
            )

        # 2. 모바일 푸시 및 인앱 알림 발송
        if recipient_user_ids:
            send_push_notification(
                user_ids=list(recipient_user_ids),
                title=push_title,
                body=push_body,
                category='work',
                target_type='issue',
                target_id=str(instance.pk),
                extra_data={'issue_id': str(instance.pk), 'project_id': str(instance.project_id)},
            )
    except Exception as e:
        print(f"❌ Async issue notification task failed: {e}")

