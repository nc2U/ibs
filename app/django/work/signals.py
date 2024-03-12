from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Issue, LogEntry


@receiver(post_save, sender=Issue)
def log_changes(sender, instance, created, **kwargs):
    action = 'CREATE' if created else 'UPDATE'
    details = f"{action} action occurred on {sender.__name__} with ID {instance.id}"
    LogEntry.objects.create(actction=action, user=instance.user, details=details)
