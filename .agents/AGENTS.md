# AGENTS.md

이 파일은 이 저장소의 코드를 다룰 때 개발 에이전트(Antigravity 등)에게 지침을 제공합니다.

## 프로젝트 개요

IBS는 Django 6.* 백엔드와 Vue 3.5 프론트엔드로 구축된 종합 건설 관리 시스템입니다.
건설 회사의 건설 프로젝트, 계약, 기납부/미납금, 자금 흐름(캐시플로우) 및 문서 관리를 수행합니다.

## 개발 명령어

### Docker 개발 환경 (권장)

```bash
# Docker를 통한 Django 명령어 실행
docker compose -f deploy/docker-compose.yml exec web python manage.py <command>

# 예시:
docker compose -f deploy/docker-compose.yml exec web python manage.py check
docker compose -f deploy/docker-compose.yml exec web python manage.py showmigrations
docker compose -f deploy/docker-compose.yml exec web python manage.py test <app_name>
docker compose -f deploy/docker-compose.yml exec web sh migrate.sh
```

### Django 백엔드 (app/django/)

```bash
# 마이그레이션 실행 (모든 앱의 마이그레이션을 생성하고 마이그레이트 실행)
sh migrate.sh -m # sh migrate.sh => 마이그레이트 실행, -m => 마이그레이션 + 마이그레이트 실행

# 정적 파일 수집 (static files)
python manage.py collectstatic

# 개발 서버 실행
python manage.py runserver

# 슈퍼유저(관리자) 생성
python manage.py createsuperuser

# 시드 데이터 로드
cd ibs/fixtures && sh loaddata.sh

# 테스트 실행
python manage.py test
python manage.py test <app_name>

# 시스템 검사
python manage.py check
```

### Vue 프론트엔드 (app/vue/)

```bash
# 의존성 패키지 설치
pnpm install

# 개발 서버 실행
pnpm dev

# 프로덕션 빌드
pnpm build

# 테스트 실행
pnpm test:unit
pnpm test:e2e

# 린트 및 포맷팅
pnpm lint
pnpm format

# 타입 검사
pnpm type-check
```

## 아키텍처 개요

### 백엔드 구조

- **Django 앱**: 각 비즈니스 영역을 독립적인 Django 앱으로 구성하여 관리합니다.
    - `accounts` - 사용자 관리 및 인증 (커스텀 User 모델)
    - `apiV1` - 프론트엔드 연동을 위한 REST API 엔드포인트
    - `book` - 도서 / 문서 관리
    - `company` - 회사 및 회사 정보 관리
    - `contract` - 계약 및 계약자 관리
    - `docs` - 문서 등록 시스템
    - `forum` - 게시판 기능
    - `ibs` - 기초 회계 계정 / 대시보드 설정 / 캘린더 / 오늘의 한마디
    - `items` - 분양 계약 유니트 및 타입 / 속성 관리
    - `ledger` - 재무 거래 및 자금 흐름 관리
    - `notice` - 고객 고지 및 알림 관리
    - `payment` - 수납 처리 및 수납 청구 관리
    - `project` - 건설 프로젝트(현장) 관리
    - `work` - 레드마인 기반 업무(Issue) 및 회의 연동 관리

### 데이터베이스 아키텍처

- `DATABASE_TYPE` 환경 변수를 통해 PostgreSQL를 지원합니다.
- `_config/database_router.py`에 마스터-슬레이브(Read/Write 분리) 라우팅이 설정되어 있습니다.
- `KUBERNETES_SERVICE_HOST` 환경 변수가 감지되면 읽기 전용 복제본(Replica) 데이터베이스를 사용하여 조회 작업을 분산합니다.
- 모든 쓰기 작업은 default 데이터베이스로 전송되며, 읽기 작업은 복제본으로 분산 가능합니다.
- 개발/프로덕션 등 환경에 따른 멀티 데이터베이스 설정이 적용되어 있습니다.

### API 구조

- REST API 엔드포인트는 `apiV1/` 앱에 통합 관리됩니다.
- `django-rest-framework-simplejwt`를 사용한 JWT 인증을 수행합니다.
- 도메인 단위 코드 구성:
    - Serializer 정의: `apiV1/serializers/` (accounts, company, project 등)
    - ViewSet 정의: `apiV1/views/` (각 도메인에 대응)
- 자동으로 URL을 생성하기 위해 `DefaultRouter`를 사용합니다.

### 프론트엔드 통합

- **Vue 3.5**: Vite 6.3 빌드 시스템, TypeScript 5.8, Vuetify 3.10 UI 프레임워크 기반의 메인 SPA입니다.
    - 풍부한 컴포넌트 생태계 활용 (d3, 차트, 마크다운 에디터, 데이트 피커 등)
    - Pinia를 활용한 전역 상태 관리
    - Vitest 및 Cypress를 사용한 테스트 코드 작성

### 핵심 아키텍처 개념

이 시스템은 건설 프로젝트의 전 생애주기 데이터를 **'프로젝트 기반의 협업 환경'**으로 통합하여 관리하는 것을 목표로 합니다.

* **현장 중심(Field-Centric) 설계**: 모든 정보는 '건설 프로젝트(현장)'를 기준으로 계층화되어, 권한과 데이터가 하위로 상속되거나 상위로 통합되어 조회됩니다.
* **데이터 무결성 및 이력 관리**: 모든 비즈니스 활동은 변경 이력(`log`)과 권한 체계를 통해 관리되며, 단순히 현재 상태뿐만 아니라 진행 과정을 투명하게 공개합니다.
* **결합된 도메인 관리**: 독립적인 도메인(계약, 수납, 문서 등)이 프로젝트라는 공통 분모를 통해 하나의 맥락으로 연결되어 작동합니다.

## 업무 관리 시스템 (work 앱) 아키텍처

부동산 시행 및 개발 프로세스를 '업무(Issue)'와 '회의(Meeting)' 단위로 관리하는 핵심 도메인입니다. 개발 및 수정 시 다음 규칙을 준수하십시오.

#### 1. 데이터 모델 및 비즈니스 흐름

* **프로젝트(IssueProject) 및 회의(Meeting) 중심 협업**: 프로젝트는 최상위 관리 단위이며, 회의는 프로젝트 내 의사결정을 자산화하는 핵심 도구입니다. 단순 회의 기록 작성을 넘어 의제(
  `agenda`), 결정 사항(`decisions`), 후속 조치(`action_items`)를 자산화합니다. 외부인 참석자는 `other_attendees` 텍스트 필드로 기록합니다.
* **회의와 업무의 유기적 매핑**: `Issue` 모델은 `meeting`을 외래키로 참조합니다. 회의 중 생성된 액션 아이템은 관련 업무(`Issue`)로 자동/수동 할당되어 진척률(`done_ratio`)과
  완료율이 실시간 모니터링됩니다.
* **통합 이력 추적**: `ActivityLogEntry`를 통해 프로젝트 내 전체 활동을 로깅하며, `IssueLogEntry`를 활용해 업무의 상태 변경 정보와 텍스트 차이점(`diff`)을 보관하여 변경
  이력을 투명하게 보관합니다.

#### 2. 백엔드 API & 권한 통제

* **액션 기반 권한 매핑**: 각 ViewSet에는 `@property`로 `required_permission`을 정의하여 DRF 액션별 권한 코드(예: `meeting.read`, `issue.create`)
  를 명시합니다. 이 코드는 `ProjectPermission` 등의 커스텀 권한 클래스에서 요청 유저의 역할(`Role`)과 비교 검증됩니다.
* **행 단위 데이터 보안 (Row-Level Security)**: 권한 검증과 별개로 목록 조회(`list`) 시 권한 없는 프로젝트의 데이터 유출을 막기 위해, `get_queryset()` 메서드에서 반드시
  슈퍼유저/work_manager가 아닐 경우 **"공개 프로젝트이거나, 사용자가 속한 프로젝트이거나, 작성자/담당자인 데이터"**로만 필터링해야 합니다.
* **Eager Loading 최적화**: N+1 쿼리 문제를 원천 차단하기 위해 `select_related` 및 `prefetch_related`를 통해 관계 테이블을 미리 로딩해야 합니다.

#### 3. 프론트엔드 Pinia & 타입 연동

* **상태 동기화**: Pinia 스토어(`useIssue`, `useMeeting` 등)에서 CRUD 완료 시, 연관된 타 스토어(`useLogging`, `useWork` 등)의 액션을 재조회하여 화면의
  일관성을 맞춥니다. 파일이 첨부된 폼을 전송할 때는 `multipart/form-data` 헤더를 설정합니다.
* **타입 안전성**: 프론트엔드 `store/types/work_*.ts` 파일 내 인터페이스는 백엔드 Serializer가 반환하는 필드 및 Nullable 옵션과 100% 일치하도록 일원화되어야 합니다.

### 설정 아키텍처 (Configuration)

- `_config/settings.py` - 환경 변수 로드를 위해 `python-decouple`을 사용하는 Django 설정 파일
- `_config/urls.py` - 헬스 체크(Health check) 및 API 엔드포인트를 포함한 메인 URL 라우팅
- `_config/database_router.py` - 마스터-슬레이브 설정을 위한 데이터베이스 라우팅 로직
- Django 루트 디렉토리의 `.env` 파일로부터 환경 변수를 로드합니다.
- Docker 환경 변수는 `deploy/docker-compose.yml`에 정의되어 있습니다.

## 배포 (Deployment)

### Docker 배포 (운영 환경 대응)

- **멀티 컨테이너 설정**: 5개 컨테이너 아키텍처
    - `ibs-nginx` - Nginx 리버스 프록시 (포트 80)
    - `ibs-web` - uWSGI 구동 Django 애플리케이션 (포트 8000)
    - `ibs-postgres` - PostgreSQL 데이터베이스 (포트 5432)
    - `ibs-redis` - 캐싱 및 세션 저장을 위한 Redis 7
    - `ibs-celery` - 비동기 작업을 처리하는 Celery 워커
- **구성**: 서비스 정의가 포함된 `deploy/docker-compose.yml`
- **볼륨**: 영구 데이터(Persistent data), 정적/미디어 파일, DB 백업, Redis 데이터를 볼륨으로 유지
- **환경 설정**: 타임존 `Asia/Seoul`, 한국어 지원 설정

### Kubernetes 배포 및 인프라 아키텍처

- **하드웨어 및 노드 구성**:
    - **Master 노드** (`Ubuntu 26.04 LTS`, 4 vCPU / 4GB RAM / NVMe 50 GB / Traffic 620GB / Network 2.5Gbps)
        - 역할: 관리 서버 겸 컨트롤 플레인.
        - 내장 NFS 서버 역할 수행: `CNPG` 데이터베이스 영구 볼륨, Django 정적 파일(`static`), Django 비밀 설정 파일(`.env`) 보관.
        - 관리 기능: K3s 및 기본 인프라 패키지(Ingress-Nginx, Cert-Manager 등)의 **설치/재시작 스크립트들을 내부에 직접 보관 및 관리**함.
    - **Worker 노드 1** (`Ubuntu 26.04 LTS`, 4 vCPU / 4GB RAM / NVMe 50 GB / Traffic 620GB / Network 2.5Gbps)
        - 역할: 컨테이너 실행 및 트래픽 처리.
    - **시놀로지 NAS** (외부 NFS 서버)
        - 역할: Django 미디어 파일(`media`) 보관 및 데이터베이스 정기 백업 파일 저장.
- **실제 서비스 배포 경로**:
    - 모든 애플리케이션 및 헬름 차트 배포는 **`.github/workflows/` 기반의 GitHub Actions 자동 배포(Git Push 트리거)**와 **로컬/마스터 서버 내 배포 스크립트를 통한
      수동 배포** 방식을 병행하여 지원함.
- **Helm 차트**: `deploy/helm/` 내에 전체 배포 설정 위치
- **CI/CD**: 자동 배포를 위한 종합적인 GitHub Actions 워크플로우 구성
    - Django 백엔드 및 Vue 컴포넌트 각각을 위한 워크플로우 분리
- **스토리지**: 영구 스토리지를 위한 NFS 서브디렉토리 외부 프로비저너 사용 (`nfs-subdir-external-provisioner`)
- **보안**: SSL 인증서 관리를 위한 `cert-manager` 적용
- **수신 트래픽**: 트래픽 제어를 위한 `ingress-nginx` 설정
- **데이터베이스**: 백업 및 복제를 지원하는 CloudNative-PG (`cnpg`) 오퍼레이터 기반 PostgreSQL 설정들

## 테스트

### Django 테스트

```bash
# 모든 테스트 실행
python manage.py test

# 특정 앱 테스트 실행
python manage.py test accounts
python manage.py test contract
```

### Vue 테스트

```bash
# Vitest를 사용한 유닛 테스트
pnpm test:unit

# Cypress를 사용한 E2E 테스트
pnpm test:e2e
```

## CI/CD 및 자동화

### GitHub Actions 배포 자동화 구조

이 프로젝트는 GitHub Actions와 Kubernetes(Helm)를 결합하여 개발(Dev) 및 운영(Prod) 환경으로의 자동화된 빌드 및 무중단 배포를 지원합니다.

* **개발 환경 (Dev)**: `develop` 브랜치에 코드가 push되면 `ibs-dev` 네임스페이스에 자동 배포됩니다.
* **운영 환경 (Prod)**: `master` 브랜치에 코드가 push되면 `ibs-prod` 네임스페이스에 자동 배포됩니다.

#### 1. 백엔드 배포 (`django_dev.yml`, `django_prod.yml`)

* **컨테이너 이미지 빌드**: Git SHA 값을 태그(`dev-${SHA}` / `${SHA}`)로 지정하여 Dockerfile 기반 이미지를 빌드하고 Docker Hub(`nc2u/django`)에
  푸시합니다.
* **K8s 리소스 충돌 관리**: 배포 전 보류 중인 Helm 업그레이드 작업을 클리닝하고, 기존 PV/PVC를 Helm 릴리즈에 자동 편입(Adoption)합니다.
* **Helm 배포**: `deploy/helm/` 차트를 사용하여 지정된 네임스페이스에 배포 및 마이그레이션 작업을 수행하며, 완료 시 롤아웃 상태를 검증합니다.

#### 2. 프론트엔드 배포 (`vue_dev.yml`, `vue_prod.yml`)

* **정적 파일 빌드**: Node.js와 pnpm을 사용하여 Vue.js SPA를 빌드하며, 빌드 무결성을 자동 검증합니다.
* **무중단 원자적 배포**: 빌드 폴더(`dist_${TIMESTAMP}`)를 CI/CD 서버로 복사(SCP)한 뒤, `dist` 심볼릭 링크를 원자적으로 교체(Symlink Swap)하여 중단 없는 서비스를
  실현합니다.
* **리소싱 효율성**: 성공한 최신 3개의 빌드 디렉토리만 서버에 유지하고 이전 빌드는 자동 삭제합니다.
* **캐시 갱신**: 프론트엔드 배포 후 Django 템플릿과 Nginx의 파일 변경이 즉시 반영되도록 관련 Pod를 재시작(`rollout restart`)합니다.

#### 3. 헬름 배포 (`helm_dev.yml`, `helm_prod.yml`)

* **인프라 변경**: `deploy/helm/**` 경로 수정 시 트리거되어 Helm 차트 구성을 서버와 동기화합니다.
* **커스텀 설정 유지**: 서버에 보관된 커스텀 설정 파일(`values-dev-custom.yaml` / `values-prod-custom.yaml`)을 배포 시 백업 및 복원하여 설정 유실을 방지합니다.
* **NFS 스토리지**: `nfs-subdir-external-provisioner` Helm 리포지토리를 추가 및 설치하여 NFS 스토리지 공유 볼륨 설정을 자동 연동합니다.

#### 4. 기타 워크플로우 및 통합

* **데이터베이스 작업**: `db_backup.yml`(백업), `db_sync.yml`(동기화) 등을 통해 정기 및 수동 데이터베이스 관리 스크립트 실행이 가능합니다.
* **보안 검증**: `codeql-analysis.yml`을 통한 취약점 스캔을 지원합니다.
* **Slack 연동**: 모든 주요 배포 워크플로우의 성공/실패 상태를 Slack 수신 웹훅(`secrets.SLACK_INCOMING_URL`)으로 즉시 알립니다.

## 중요 유의사항

### 핵심 설정

- 커스텀 사용자 모델 적용: `AUTH_USER_MODEL = 'accounts.User'`
- 정적 파일은 `_assets/` 디렉토리에서 서비스됨
- 미디어 파일 지원: 로컬 스토리지 및 S3 클라우드 스토리지 연동
- 기본 언어/국가: 한국어(`ko`), 타임존 `Asia/Seoul`
- SMTP 설정을 통한 이메일 연동

### 개발 프랙티스

- 모든 데이터베이스 마이그레이션이 항상 최신으로 반영되어야 함
- 확장을 고려한 마스터-슬레이브 데이터베이스 라우팅
- Redis 기반 캐싱 및 세션 관리 사용
- 비동기 태스크 처리를 위한 Celery 사용

### 파일 구조 요약

- Django 백엔드: `app/django/`
- Vue 프론트엔드: `app/vue/` (TypeScript, Vuetify)
- 배포 설정 파일: `deploy/`
- 영구 보관용 볼륨 데이터: `volume/`