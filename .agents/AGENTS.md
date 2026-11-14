# AGENTS.md

이 파일은 이 저장소의 코드를 다룰 때 개발 에이전트(Antigravity 등)에게 적용되는 공통 핵심 지침입니다.

## 프로젝트 개요 및 구조

IBS는 부동산 개발·건설 프로젝트, 계약, 수납, 자금 흐름(캐시플로우), 전자결재, 사내 메신저 및 업무를 통합 관리하는 시스템입니다.

* **백엔드 (`app/django/`)**: Django 6.1.* (`Python 3.14`), DRF + SimpleJWT, Daphne(ASGI + Channels WebSocket), Celery + Redis, PostgreSQL
  * 도메인 앱: `accounts`, `approval`, `book`, `chat`, `company`, `contract`, `docs`, `forum`, `ibs`, `items`, `ledger`, `notice`, `payment`, `project`, `sales`, `work`
  * API/공통: `apiV1`, `_excel`, `_pdf`, `_utils`, `_config`
* **웹 프론트엔드 (`app/vue/`)**: Vue 3.5, Vite 7.*, TypeScript 5.8, Vuetify 4.*, CoreUI, Pinia, Vitest/Cypress
* **모바일 앱 (`app/flutter/`)**: Flutter (`mobile_ibs`, Dart `>=3.9.2 <4.0.0`), Riverpod + GoRouter
* **사용자 매뉴얼 (`app/vue/docs/`)**: VitePress 기반 운영 매뉴얼
* **배포/인프라 (`deploy/`, `volume/`)**: Docker Compose, Dockerfile, K3s Helm 차트(`deploy/helm/`), 배포/백업 스크립트

---

## 개발 및 검증 명령어 (CI 게이트 기준)

### Docker 개발 환경 (권장)

```bash
docker compose -f deploy/docker-compose.yml exec web python manage.py check
docker compose -f deploy/docker-compose.yml exec web python manage.py showmigrations
docker compose -f deploy/docker-compose.yml exec web python manage.py test <app_name>
docker compose -f deploy/docker-compose.yml exec web sh migrate.sh
```

### Django 백엔드 (`app/django/`)

```bash
python manage.py check                              # 시스템 검사 (CI 필수)
python manage.py makemigrations --check --dry-run   # 누락 마이그레이션 검사 (CI 필수)
python manage.py test --noinput                     # 전체 테스트 (또는 <app_name>)
python manage.py runserver                          # 개발 서버 (로컬 ASGI/Channels 테스트 시 daphne 사용)
python manage.py collectstatic                      # _assets/ -> static/ 정적 파일 수집
cd ibs/fixtures && sh loaddata.sh                   # 시드 데이터 로드
```

* **마이그레이션 주의**: `sh migrate.sh -m`은 스크립트 내부에 하드코딩된 16개 앱 목록에 대해 `makemigrations`를 실행하므로(`_excel`, `_pdf` 등 제외), 모델 변경이 의도된 경우에만 사용하고 검증 시에는 `makemigrations --check --dry-run`을 우선 실행합니다.
* **PostgreSQL `pg_trgm` 확장**: `GinIndex`를 사용하므로 로컬/테스트 PostgreSQL(`template1` 및 대상 DB)에 `CREATE EXTENSION IF NOT EXISTS pg_trgm;`이 적용되어 있어야 합니다.

### Vue 프론트엔드 (`app/vue/`)

```bash
pnpm install              # 의존성 설치 (CI: pnpm install --frozen-lockfile)
pnpm dev                  # Vite 개발 서버
pnpm lint:check           # ESLint 비수정 검사 (CI 필수) — pnpm lint 는 --fix 자동 수정 실행
pnpm type-check           # TypeScript 검사 (vue-tsc --noEmit)
pnpm exec vitest run      # 유닛 테스트 단발 실행 (⚠️ pnpm test:unit 은 watch 모드이므로 에이전트/CI에서 사용 금지)
pnpm build-only           # Vite 프로덕션 빌드 (../django/static/dist 로 출력됨)
pnpm build                # type-check + build-only 병렬 실행
pnpm format               # Prettier 포맷팅
pnpm docs:dev             # VitePress 매뉴얼 로컬 서버 (빌드: pnpm docs:build)
```

### Flutter 모바일 (`app/flutter/`)

```bash
flutter pub get && flutter analyze && flutter test
```

---

## 도메인 용어 체계 (Domain Terminology Architecture)

백엔드 모델과 클라이언트(Vue / Flutter) UI 용어의 개념 일관성을 위해 아래 매핑을 반드시 준수합니다.

| 구분              | 백엔드 모델                                         | 비즈니스 도메인 범위                                                     | 클라이언트(Vue / Flutter) UI 표출 용어 |
|:------------------|:----------------------------------------------------|:-------------------------------------------------------------------------|:---------------------------------------|
| **Work Space**    | `work.Role/Permission` (`category='work_space'`)    | 본사관리(1) / 부동산개발(2) / 기타(3) 통합 협업 공간                     | **`워크스페이스` (Workspace)**         |
| **IBS HQ Manage** | `work.Role/Permission` (`category='ibs_hq_manage'`) | 본사 회계/자금, 인사/조직, 법무, 감사 등 본사 경영 직무 (보안 격리 지원) | **`본사 관리` (HQ Manage)**            |
| **IBS PR Manage** | `work.Role/Permission` (`category='ibs_pr_manage'`) | 분양, 수납, 사업부지, 사업비 등 부동산 개발 전용 사업지                  | **`프로젝트` (Project)**               |

* **'현장' 용어 지양 (시스템/도메인 영역)**: 메뉴명, 아키텍처, DB 모델에서 협업 공간이나 사업지를 지칭할 때는 '현장' 대신 **'워크스페이스'** 또는 **'프로젝트'**를 사용합니다. 단, `"현장 사진/동영상 첨부"`, `"현장 외근/실사"`, `"공사 현장 상황"`처럼 물리적 작업 현장을 직접 가리키는 실무 표현은 허용합니다.

---

## 핵심 개발 원칙

### 백엔드 (`app/django/`)

* **인증 및 API**: `AUTH_USER_MODEL = 'accounts.User'`, 한국어(`ko-kr`) / `Asia/Seoul`, JWT(`djangorestframework-simplejwt`), `apiV1/` 아래 도메인별 `serializers/`·`views/` 분리 및 `DefaultRouter` 등록.
* **ASGI & 비동기**: `ibs-web`은 **Daphne**(`_config.asgi:application`)로 HTTP와 `channels` WebSocket(`chat`)을 동시에 서빙하며, 비동기 작업은 Celery(`_config`)와 Redis를 사용합니다.
* **DB 라우팅 (`_config/database_router.py`)**: `KUBERNETES_SERVICE_HOST` 환경에서 읽기를 `replica`로 분산합니다(`atomic()` 블록 내부와 저장 직후 인스턴스는 `default` 사용 — 트랜잭션 외부 즉시 재조회 시 Replica Lag 주의).
* **정적/미디어 파일**: 원본 정적 파일은 `_assets/`(`STATICFILES_DIRS`), 수집 및 Nginx 서빙 경로는 `static/`(`STATIC_ROOT`), Vue 빌드 산출물은 `static/dist/`입니다. 미디어는 MinIO/S3 Pre-signed URL을 사용하며 미설정 시 `FileSystemStorage`로 폴백됩니다.
* **마이그레이션 및 보안**: 마이그레이션을 항상 최신 상태로 유지하고, `work`/`approval`/`chat`/`sales` 등 뷰셋은 액션 권한(`required_permission`)과 `get_queryset()` 행 단위 보안(Row-Level Security) 및 `select_related`/`prefetch_related` 최적화를 준수합니다.

### 프론트엔드 (`app/vue/`, 엄수 ⭐️)

* **개행 코드 표준**: 모든 프론트엔드 소스(`.vue`, `.ts`, `.js`, `.json` 등)는 **LF (Line Feed)** 개행 코드를 엄수합니다.
* **Bootstrap 5 표준 클래스 준수** (단, Vuetify 전용 컴포넌트 유틸리티 예: `mr-n2` 음수 마진 등은 예외):
  * `text-left`/`text-right` ➔ `text-start`/`text-end`
  * `ml-*`/`mr-*`, `pl-*`/`pr-*` ➔ `ms-*`/`me-*`, `ps-*`/`pe-*`
  * `font-weight-bold`/`font-weight-normal` ➔ `fw-bold`/`fw-normal`
  * `icon="mdi mdi-*"` ➔ `icon="mdi-*"`
* **공통 모달 사용**: `window.confirm()`, `window.alert()` 금지 ➔ `src/components/Modals/`의 `ConfirmModal.vue`, `AlertModal.vue`, `FormModal.vue` 사용.
* **이중 API 호출(Race Condition) 방지**: `ContentHeader`의 `@proj-select`/`@com-select` 핸들러와 `watch(project)`/`watch(comId)` 간 중복 조회를 피하고 `watch`로 단일화합니다.
* **웹 표준 및 폼 검증**: `href="javascript:void(0);"` 대신 `@click.prevent` 사용, 폼 유효성 검사는 `@/utils/helper`의 `isValidate(event)` 사용.
* **TypeScript 엄격성**: Props에 `PropType<T>` 명시, 템플릿 ref 호출 시 `?.` 옵셔널 체이닝 적용, `store/types/*.ts`를 백엔드 Serializer 스키마와 일치시킵니다(`pnpm gen:api-types` 사용 시 먼저 `python manage.py spectacular --file schema.yml` 생성 필요).

---

## 상세 참조 문서 (해당 영역 작업 시 필독)

* [`.agents/docs/backend-domains.md`](docs/backend-domains.md) — `work`·`sales` 앱 상세 비즈니스 흐름, 권한, Pinia 연동 규칙
* [`.agents/docs/infra-deploy.md`](docs/infra-deploy.md) — Docker, K3s/Helm, `.github/workflows/` CI/CD 파이프라인 및 설정 상세
* [`.agents/docs/vitepress-manual.md`](docs/vitepress-manual.md) — `app/vue/docs/` 사용자 매뉴얼 작성 규칙 (이미지 플레이스홀더, `##` 앞 `---` 금지 등)
* `.agents/artifacts/` — 도메인별 설계 로드맵 및 백업/보안 운영 아카이브
