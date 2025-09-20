from django.apps import AppConfig


class WorkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'work'
    verbose_name = '업무 협업 관리(work)'

    def ready(self):
        import work.signals
