from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    # Private 버킷: Pre-signed URL로 임시 접근 (기본값 True)
    # URL 유효기간은 settings.py의 AWS_QUERYSTRING_EXPIRE로 제어
    querystring_auth = True
    custom_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)

    def url(self, name, parameters=None, expire=None, http_method=None):
        # custom_domain이 있어도 querystring_auth (Pre-signed 서명)을 강제로 생성하도록 보장
        saved_custom_domain = self.custom_domain
        self.custom_domain = None
        generated_url = super().url(name, parameters=parameters, expire=expire, http_method=http_method)
        self.custom_domain = saved_custom_domain

        if saved_custom_domain and '?' in generated_url:
            query = generated_url.split('?', 1)[1]
            return f"https://{saved_custom_domain}/{self.location}/{name}?{query}"
        return generated_url
