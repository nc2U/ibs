from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from work.models.meeting import Meeting
from work.models.issue import Issue

User = get_user_model()


@shared_task
def send_meeting_mail_task(meeting_pk, user_pk, mail_type):
    """Celery task to send meeting-related emails asynchronously"""
    try:
        instance = Meeting.objects.select_related('project', 'creator').get(pk=meeting_pk)
        user = User.objects.get(pk=user_pk)

        # 참석자 및 작성자 수신자 구성
        attendees = list(instance.attendees.all())
        recipients = set([instance.creator.email] + [a.email for a in attendees])
        if user.email in recipients:
            recipients.remove(user.email)  # 보낸 사람은 제외

        addresses = list(recipients)

        if mail_type == "create":
            subject = f'『 {instance.project} 』 - 새 회의록 :: "{instance.title}"'
            template = 'mail/meeting_create.html'
        elif mail_type == "confirm":
            subject = f'『 {instance.project} 』 - 회의 확정 :: "{instance.title}"'
            template = 'mail/meeting_confirm.html'
        else:
            return

        context = {
            'instance': instance,
            'settings': settings,
            'user': user,
        }
        message = render_to_string(template, context)

        send_mail(
            subject=subject,
            message=message,
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=addresses
        )
    except Exception as e:
        print(f"❌ Async meeting email task failed: {e}")


@shared_task
def send_issue_mail_task(issue_pk, user_pk, mail_type, old_status_name=None, old_assigned_to=None):
    """Celery task to send issue-related emails asynchronously"""
    try:
        instance = Issue.objects.select_related('project', 'tracker', 'status', 'assigned_to').get(pk=issue_pk)
        user = User.objects.get(pk=user_pk)
        watchers = list(instance.watchers.all())

        # 수신자 목록 구성
        if mail_type == "create":
            addresses = [user.email]
            if instance.assigned_to:
                addresses.append(instance.assigned_to.email)
            subject = f'『 {instance.project} 』 - 새 업무 :: [#{instance.pk}] "{instance.subject}"이(가) 할당되었습니다.' if instance.assigned_to else f'『 {instance.project} 』 - 새 업무 :: [#{instance.pk}] "{instance.subject}"이(가) 생성되었습니다.'
            template = 'mail/issue_create.html'
        elif mail_type == "progress":
            addresses = [watcher.email for watcher in watchers]
            subject = f'『 {instance.project} 』 - 업무 :: [#{instance.pk}] "{instance.subject}"의 상태가 {instance.status}(으)로 변경되었습니다.'
            template = 'mail/issue_progress.html'
        elif mail_type == "reassign":
            addresses = [watcher.email for watcher in watchers]
            subject = f'『 {instance.project} 』 - 업무 :: [#{instance.pk}] "{instance.subject}"의 담당자가 변경되었습니다.'
            template = 'mail/issue_reassign.html'
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

        send_mail(
            subject=subject,
            message=message,
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=addresses
        )
    except Exception as e:
        # Logging here if needed
        print(f"❌ Async email task failed: {e}")
