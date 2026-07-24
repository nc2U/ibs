from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    # Private 버킷: Pre-signed URL로 임시 접근 (기본값 True)
    # URL 유효기간은 settings.py의 AWS_QUERYSTRING_EXPIRE로 제어
    querystring_auth = True
