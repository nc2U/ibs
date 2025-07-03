import os
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.db.models import FileField, ImageField


def delete_file_field(instance, field_name):
    """주어진 인스턴스의 파일 필드를 실제로 삭제"""
    field = getattr(instance, field_name, None)
    try:
        if field and hasattr(field, 'path') and os.path.isfile(field.path):
            os.remove(field.path)
    except (FileNotFoundError, OSError):
        pass


def file_cleanup_signals(model, file_field_names=None):
    """
    FileField/ImageField를 가진 모델에 대해 자동으로 파일 삭제 시그널 연결
    - file_field_names 생략 시 해당 모델에서 모든 FileField/ImageField 탐색
    """

    @receiver(pre_save, sender=model)
    def delete_old_files_on_update(sender, instance, **kwargs):
        if not instance.pk:
            return
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return

        fields_to_check = file_field_names or [
            f.name for f in sender._meta.get_fields()
            if isinstance(f, (FileField, ImageField))
        ]

        for field_name in fields_to_check:
            old_file = getattr(old_instance, field_name, None)
            new_file = getattr(instance, field_name, None)
            if old_file and old_file != new_file:
                delete_file_field(old_instance, field_name)

    @receiver(pre_delete, sender=model)
    def delete_files_on_delete(sender, instance, **kwargs):
        fields_to_check = file_field_names or [
            f.name for f in sender._meta.get_fields()
            if isinstance(f, (FileField, ImageField))
        ]
        for field_name in fields_to_check:
            delete_file_field(instance, field_name)


def related_file_cleanup(parent_model, related_name: str, file_field_name: str):
    """
    ManyToMany 관계의 연결된 모델 인스턴스의 파일을 삭제
    예: News → files → NewsFile(file 필드 삭제)
    """

    @receiver(pre_delete, sender=parent_model)
    def delete_related_files_on_parent_delete(sender, instance, **kwargs):
        related_manager = getattr(instance, related_name, None)
        if related_manager:
            for related_instance in related_manager.all():
                delete_file_field(related_instance, file_field_name)
