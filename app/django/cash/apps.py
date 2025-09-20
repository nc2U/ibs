from django.apps import AppConfig


class CashConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cash'
    verbose_name = '자금 관리 관련 정보 [cash]'

    def ready(self):
        import cash.signals
