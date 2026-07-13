from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver

from work.models.inform import News
from work.models.issue import Issue, IssueRelation, IssueComment
from work.models.logging import ActivityLogEntry, IssueLogEntry
from work.models.meeting import Meeting
from work.services.work_services import MeetingService, IssueService


@receiver(pre_save, sender=Meeting)
def meeting_track_changes(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Meeting.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                setattr(instance, 'old_status', old_instance.status)
            if old_instance.is_confirmed != instance.is_confirmed:
                setattr(instance, 'old_is_confirmed', old_instance.is_confirmed)
        except Meeting.DoesNotExist:
            pass


@receiver(post_save, sender=Meeting)
def meeting_log_changes(sender, instance, created, **kwargs):
    user = (instance.updater if not created else instance.creator) or instance.creator
    old_is_confirmed = getattr(instance, 'old_is_confirmed', None)

    if created:
        ActivityLogEntry.objects.create(sort='3', project=instance.project,
                                        meeting=instance, creator=instance.creator)
    elif hasattr(instance, 'old_status'):
        ActivityLogEntry.objects.create(sort='3', project=instance.project,
                                        meeting=instance, status_log=instance.get_status_display(),
                                        creator=user)

    # 메일 알림 서비스 호출
    MeetingService.notify_meeting_changes(instance, created, user, old_is_confirmed)


@receiver(pre_delete, sender=Meeting)
def meeting_log_delete(sender, instance, **kwargs):
    ActivityLogEntry.objects.filter(meeting=instance).delete()


@receiver(pre_save, sender=Issue)
def issue_track_changes(sender, instance, **kwargs):
    IssueService.track_changes(instance)


@receiver(post_save, sender=Issue)
def issue_log_changes(sender, instance, created, **kwargs):
    user = instance.creator if created else instance.updater
    if user:
        IssueService.log_and_notify(instance, created, user)


@receiver(pre_delete, sender=Issue)
def issue_log_delete(sender, instance, **kwargs):
    IssueLogEntry.objects.filter(issue=instance).delete()
    ActivityLogEntry.objects.filter(issue=instance).delete()


@receiver(post_save, sender=IssueRelation)
def issue_relation_create(sender, instance, created, **kwargs):
    if created:
        details = f"|- **연결된 업무** : 에 \
        *{instance.target.tracker} {instance.target.pk} {instance.target}*이(가) 추가되었습니다."
        IssueLogEntry.objects.create(issue=instance.source, action='Updated',
                                     details=details, creator=instance.creator)


@receiver(pre_delete, sender=IssueRelation)
def issue_relation_delete(sender, instance, **kwargs):
    details = f"|- **연결된 업무** : 값이 삭제되었습니다. \
    (*{instance.target.tracker} {instance.target.pk} {instance.target}*)"
    IssueLogEntry.objects.create(issue=instance.source, action='Updated',
                                 details=details, creator=instance.creator)


@receiver(post_save, sender=IssueComment)
def comment_log_changes(sender, instance, created, **kwargs):
    if created:
        IssueLogEntry.objects.create(issue=instance.issue, action='Comment', comment=instance, creator=instance.creator)
        ActivityLogEntry.objects.create(sort='2', project=instance.issue.project, issue=instance.issue,
                                        comment=instance, creator=instance.creator)


@receiver(pre_delete, sender=IssueComment)
def comment_log_delete(sender, instance, **kwargs):
    IssueLogEntry.objects.filter(comment=instance).delete()
    ActivityLogEntry.objects.filter(comment=instance).delete()


@receiver(post_save, sender=News)
def news_log_changes(sender, instance, created, **kwargs):
    if created:
        ActivityLogEntry.objects.create(sort='4', project=instance.project,
                                        news=instance, creator=instance.author)


@receiver(pre_delete, sender=News)
def news_log_delete(sender, instance, **kwargs):
    ActivityLogEntry.objects.filter(news=instance).delete()
