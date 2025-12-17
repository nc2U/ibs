from django.apps import AppConfig


class LedgerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ledger'
    verbose_name = '회계 원장 정보 [LEDGER]'

    def ready(self):
        import ledger.signals
