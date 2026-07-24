# MinIO S3 미디어 스토리지 마이그레이션 결과

## 1. 이관 및 설정 매핑 상태

- **MinIO 미디어 버킷**: `ibs-media` (Private 모드, 비공개로 생성 완료)
- **NFS 미디어 데이터 이관**:
  * `/volume1/mnt/ibs/prod/app/django/media/` 디렉토리를 `mc mirror`를 통해 `minio/ibs-media/media/`로 100% 정상 전송 완료.
- **접근 방식**:
  * 업무용 프로그램의 특성에 맞춰 **Private + Pre-signed 임시 보안 URL**로 접근하도록 설정 (기본 만료 시간 1시간).

---

## 2. 코드 및 환경 설정 변경 이력 (2026-07-25)

### Django 설정
- **`asset_storage.py`**: `MediaStorage`의 `querystring_auth` 옵션을 명시적으로 활성화.
- **`settings.py`**:
  * `AWS_S3_ENDPOINT_URL` (MinIO API 주소) 지원.
  * `AWS_QUERYSTRING_EXPIRE` (Pre-signed 만료기간) 옵션 추가.
  * MinIO 호환을 위해 `AWS_S3_ADDRESSING_STYLE = 'path'` 지정 및 S3 custom domain 비활성화.

### Docker Compose 설정
- **`deploy/docker-compose.yml`**: 로컬 `web` 및 `celery` 컨테이너 환경 변수에 MinIO 연동 값 주입 완료 (YAML $ 문자 탈출 `$$` 적용).
- **`deploy/.docker-compose.yml`**: 깃허브용 목업 Compose 파일의 환경변수 영역 동기화 완료.

### Helm values 설정
- **`deploy/helm/charts/web/templates/configmap.yaml`**: `AWS_S3_ENDPOINT_URL`, `AWS_REGION`, `AWS_QUERYSTRING_EXPIRE` 환경변수 매핑 템플릿 추가.
- **`deploy/helm/values-prod-custom.yaml`**: 실제 서버용 `web.imageConfigMaps` 설정 값 추가 완료.
- **`deploy/helm/values-prod.yaml`**: 깃허브 배포용 `web.imageConfigMaps` 및 `cnpg.backup` 스펙을 목업 데이터로 동기화 완료.
