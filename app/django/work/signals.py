from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver

from work.models.inform import News
from work.models.issue import Issue, IssueRelation, IssueComment
from work.models.logging import ActivityLogEntry, IssueLogEntry
from work.services import IssueService


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
        details = f"|- **{instance.get_relation_type_display()}** : 에 \
        *{instance.issue_to.tracker} {instance.issue_to.pk} {instance.issue_to}*이(가) 추가되었습니다."
        IssueLogEntry.objects.create(issue=instance.issue, action='Updated',
                                     details=details, creator=instance.creator)


@receiver(pre_delete, sender=IssueRelation)
def issue_relation_delete(sender, instance, **kwargs):
    details = f"|- **{instance.get_relation_type_display()}** : 값이 삭제되었습니다. \
    (*{instance.issue_to.tracker} {instance.issue_to.pk} {instance.issue_to}*)"
    IssueLogEntry.objects.create(issue=instance.issue, action='Updated',
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
