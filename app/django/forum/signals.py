from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from forum.models import Post
from work.models.logging import ActivityLogEntry


import html
from django.utils.html import strip_tags


@receiver(post_save, sender=Post, dispatch_uid="post_activity_log_changes")
def post_log_changes(sender, instance, created, **kwargs):
    project = instance.forum.project
    if created and project and project.status == '1':
        clean_text = html.unescape(strip_tags(instance.content or ''))
        clean_text = ' '.join(clean_text.split())
        ActivityLogEntry.objects.create(
            sort='6', project=project, target_id=instance.pk, parent_id=instance.forum.pk,
            title=f"[게시물] {instance.title}", summary=clean_text[:150], creator=instance.creator
        )


@receiver(pre_delete, sender=Post, dispatch_uid="post_activity_log_delete")
def post_log_delete(sender, instance, **kwargs):
    ActivityLogEntry.objects.filter(sort='6', target_id=instance.pk).delete()
