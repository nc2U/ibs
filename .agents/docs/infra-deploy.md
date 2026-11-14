# 인프라, 배포 및 CI/CD 아키텍처

## 설정 및 데이터베이스 아키텍처

* **`_config/settings.py`**: `python-decouple`을 사용해 `app/django/.env`로부터 환경 변수를 로드합니다 (`deploy/docker-compose.yml`에서 환경별 오버라이드 가능).
* **`_config/urls.py`**: 헬스 체크, API 엔드포인트(`apiV1/`), Excel(`_excel`), PDF(`_pdf`) 라우팅.
* **`_config/asgi.py`**: Daphne ASGI 엔트리포인트(`ProtocolTypeRouter`). HTTP(`django_asgi_app`)와 `channels` WebSocket(`chat.routing.websocket_urlpatterns` + `JWTAuthMiddleware`)을 동시에 처리합니다.
* **`_config/database_router.py` (`MasterSlaveRouter`)**:
  * `DATABASE_TYPE` 환경 변수(PostgreSQL 기본, MariaDB/MySQL 설정 분기 포함)를 지원합니다.
  * `KUBERNETES_SERVICE_HOST`가 감지되고 `replica` 연결 확인이 성공하면(60초 TTL 캐시) 읽기 트래픽을 `replica` DB로 분산합니다.
  * 쓰기 작업, `atomic()` 블록 내부, 그리고 직전에 `default` DB에서 저장한 인스턴스의 관계 조회(`hints['instance']`)는 항상 `default`를 사용합니다. 단, 트랜잭션 외부에서 저장 직후 별도 쿼리로 즉시 재조회할 때는 Replication Lag에 유의합니다.
* **스토리지 및 캐시**:
  * `AWS_STORAGE_BUCKET_NAME` + `AWS_S3_ENDPOINT_URL`(MinIO/S3)이 설정되면 `_config.asset_storage.MediaStorage`로 Pre-signed URL 서빙, 미설정 시 로컬 `FileSystemStorage`(`MEDIA_ROOT = BASE_DIR / 'media'`)로 폴백됩니다.
  * Redis는 캐시(`django_redis`, `REDIS_URL`), Celery 브로커/백엔드(`CELERY_BROKER_URL`), Channels 레이어(`REDIS_CHANNEL_URL` 또는 `REDIS_URL`)에 사용됩니다.

---

## Docker 구성 (`deploy/docker-compose.yml`)

5개 컨테이너 아키텍처(`Asia/Seoul`, 한국어 지원)로 구성됩니다.

* **`ibs-nginx`** (`nginx:latest`): 리버스 프록시 (포트 80), `app/django/static` 및 `app/django/media` 볼륨 마운트
* **`ibs-web`** (`nc2u/django`, `deploy/docker/python/dev` 빌드): Python 3.14 + **Daphne** (`daphne -b 0.0.0.0 -p 8000 _config.asgi:application`)
* **`ibs-postgres`** (`postgres`): PostgreSQL 데이터베이스 (`5432`, `volume/backups`, `volume/initdb/postgres` 마운트)
* **`ibs-redis`** (`redis:7-alpine`): 캐시 / Celery / Channels (`6379`, `volume/redis` 마운트)
* **`ibs-celery`** (`nc2u/django`): `celery -A _config worker --loglevel=info --concurrency=4`

> 운영 이미지 Dockerfile(`deploy/docker/python/Dockerfile`) 역시 Python `3.14` 멀티스테이지(`python:3.14` → `python:3.14-slim`) 및 **Daphne** 엔트리포인트로 통일되어 있으며, `deploy/docker/python/requirements.txt`의 고정 버전을 설치하고 빌드 단계에서 `collectstatic --noinput --clear`를 수행합니다.

---

## Kubernetes(K3s) 배포 및 인프라

* **하드웨어 및 노드 구성**:
  * **Master 노드** (`Ubuntu 26.04 LTS`, 4 vCPU / 4GB RAM / NVMe 50 GB / Traffic 620GB / Network 2.5Gbps): 컨트롤 플레인 겸 관리 서버. 내장 NFS 서버(`CNPG` DB PV, Django `static`, 비밀 설정 `.env` 보관) 및 K3s/인프라 패키지 설치·재시작 스크립트 관리.
  * **Worker 노드 1** (`Ubuntu 26.04 LTS`, 4 vCPU / 4GB RAM / NVMe 50 GB / Traffic 620GB / Network 2.5Gbps): 컨테이너 실행 및 트래픽 처리.
  * **시놀로지 NAS** (외부 NFS 서버): Django 미디어 파일(`media`) 및 정기 데이터베이스 백업 저장.
* **Helm 차트 (`deploy/helm/`)**:
  * 서브 차트(`deploy/helm/charts/`): `cnpg`, `nginx`, `redis`, `web`
  * 스토리지 프로비저닝: `nfs-subdir-external-provisioner`
  * SSL 인증서: `cert-manager`, 인그레스: `ingress-nginx`
  * 데이터베이스: CloudNative-PG(`cnpg`) 오퍼레이터 기반 PostgreSQL (`-rw` 마스터 / `-ro` 읽기 복제본)
* **배포 스크립트**: `deploy/helm/scripts/` (`dev-deploy.sh`, `prod-deploy.sh`, `manual-backup.sh`, `manual-restore.sh` 등) 및 `deploy/scripts/` 지원

---

## CI/CD 및 GitHub Actions (`.github/workflows/`)

* **개발 환경 (Dev)**: `develop` 브랜치 푸시 시 `ibs-dev` 네임스페이스 배포
* **운영 환경 (Prod)**: `master` 브랜치 푸시 시 `ibs-prod` 네임스페이스 배포

1. **자동 검증 (`ci-verify.yml`)** — PR 및 `develop`·`master` 푸시 시 실행
   * **Django (`app/django`)**: PostgreSQL 17(`template1` + `ibs` DB에 `pg_trgm` 확장 설치) + Redis 7 서비스 기동 → `python manage.py check` → `python manage.py makemigrations --check --dry-run` → `python manage.py test --noinput`
   * **Vue (`app/vue`)**: `pnpm install --frozen-lockfile` → `pnpm lint:check` → `pnpm type-check` → `pnpm exec vitest run`
2. **백엔드 & Helm 배포 (`ci-cd-django-helm-dev.yml`, `ci-cd-django-helm-prod.yml`)**
   * `dorny/paths-filter`로 변경 경로(`app/django/**`, `deploy/docker/**`, `deploy/helm/**`)를 감지해 이미지 빌드 및/또는 Helm 배포 수행.
   * Docker Hub(`nc2u/django`)에 `dev-${SHORT_SHA}` / `${SHORT_SHA}`(및 `:dev-latest` / `:latest`) 태그 푸시.
   * K8s 배포 전 `pending-*` Helm Secret 정리 및 기존 PV/PVC·CNPG Cluster의 Helm 릴리즈 편입(Adoption) 수행, `values-*-custom.yaml` 보존.
3. **프론트엔드 정적 배포 (`ci-cd-vue-static-dev.yml`, `ci-cd-vue-static-prod.yml`)**
   * `pnpm build`로 `app/django/static/dist_${BUILD_TIMESTAMP}` 빌드 및 `/static/dist/assets/` 경로 검증.
   * CI/CD 서버로 전송 후 `dist` 심볼릭 링크를 원자적으로 교체(Symlink Swap).
   * **롤아웃 순서**: `deployment/nginx` 먼저 재시작 및 완료 대기 → 이후 `deployment/web` 재시작 → 최종적으로 활성 빌드를 제외한 최신 3개만 남기고 구 `dist_*` 디렉토리 정리(NFS stale handle 방지).
4. **모바일 앱 배포 (`ci-cd-flutter-dev.yml`, `ci-cd-flutter-prod.yml`)**
   * 수동(`workflow_dispatch`) 트리거. Dev는 APK 빌드 후 Firebase App Distribution 배포, Prod는 Android App Bundle/Play 스토어 트랙(`internal`/`production`) 배포 수행.
5. **기타 워크플로우**
   * `manual-image-build.yml`(수동 Django 이미지 빌드·배포), `manual-db-backup.yml`(수동 DB 백업), `sync-db-prod-dev.yml`(운영→개발 DB 동기화), `_init-install-setup-dev.yml` / `_init-install-setup-prod.yml`(초기 인프라 설치), `codeql-analysis.yml`(Python/JS 취약점 분석).
   * 주요 워크플로우는 `.github/actions/slack-notify`(`secrets.SLACK_INCOMING_URL`)로 Slack 알림 전송.
