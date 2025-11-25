from django.apps import AppConfig


class PaymentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payment'
    verbose_name = '수납 관련 정보 설정 [payment]'

    def ready(self):
        """앱이 준비되었을 때 실행 - signals 등록"""
        import payment.signals  # signals.py 로드
