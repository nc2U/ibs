from django.apps import AppConfig


class DocsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'docs'
    verbose_name = '*** 문서관리'

    def ready(self):
        import docs.signals
