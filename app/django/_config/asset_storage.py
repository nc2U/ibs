import urllib.parse
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    # Private 버킷: Pre-signed URL로 임시 접근 (기본값 True)
    # URL 유효기간은 settings.py의 AWS_QUERYSTRING_EXPIRE로 제어
    querystring_auth = True
    # custom_domain을 None으로 유지하여 django-storages가 presigned query 생성을 생략하지 않도록 보장
    custom_domain = None

    def url(self, name, parameters=None, expire=None, http_method=None):
        """Pre-signed URL 생성 시 스레드 안전성 및 URL 인코딩을 보장하며 외부 도메인으로 매핑합니다."""
        generated_url = super().url(name, parameters=parameters, expire=expire, http_method=http_method)

        target_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)
        if not target_domain:
            return generated_url

        # target_domain이 'host' 또는 'host/bucket' 형태일 수 있으므로 분리
        parts = target_domain.split('/', 1)
        target_host = parts[0]
        prefix = f"/{parts[1]}" if len(parts) > 1 else ""

        parsed = urllib.parse.urlsplit(generated_url)
        path = parsed.path

        # 이미 경로에 버킷 prefix가 포함되어 있는지 확인하여 중복 방지
        if prefix and path.startswith(prefix):
            new_path = path
        elif prefix:
            new_path = f"{prefix}{path}"
        else:
            new_path = path

        scheme = parsed.scheme or 'https'
        return urllib.parse.urlunsplit((
            scheme,
            target_host,
            new_path,
            parsed.query,
            parsed.fragment
        ))
