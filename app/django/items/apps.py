from django.apps import AppConfig


class ItemsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'items'
    verbose_name = '개발 상품 정보(items)'
