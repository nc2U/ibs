from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from forum.models import Post
from work.models.logging import ActivityLogEntry


@receiver(post_save, sender=Post, dispatch_uid="post_activity_log_changes")
def post_log_changes(sender, instance, created, **kwargs):
    project = instance.forum.project
    if created and project and project.status == '1':
        ActivityLogEntry.objects.create(sort='6', project=project,
                                        post=instance, creator=instance.creator)


@receiver(pre_delete, sender=Post, dispatch_uid="post_activity_log_delete")
def post_log_delete(sender, instance, **kwargs):
    ActivityLogEntry.objects.filter(post=instance).delete()
