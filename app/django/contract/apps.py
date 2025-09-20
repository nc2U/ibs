from django.apps import AppConfig


class ContractConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contract'
    verbose_name = '분양 계약 관련 정보 (contract)'

    def ready(self):
        import contract.signals
