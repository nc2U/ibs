# IBS 프로젝트 문서 및 가이드라인

이 문서는 IBS 프로젝트의 지식 기반 역할을 하며, 팀원과 AI 에이전트의 개발을 가이드합니다.

## 1. 프로젝트 개요

- **백엔드** : Django (Python 3.x)
- **프론트엔드** : Vue.js (TypeScript)
- **인프라** : Docker, Kubernetes (Helm), Nginx, PostgreSQL
- **목적** :
  [이 프로젝트는 부동산 개발(시행) 프로젝트의 전 과정에서 발생하는 자금, 계약, 고객, 문서, 소송 등 핵심 데이터를 통합 관리하고 이를 수행하는 디벨로퍼의 협업을 위한 통합 업무 지원을 목표로 합니다. 특히 프로젝트 내 work 앱은 글로벌 협업 표준인 Redmine 엔진을 기반으로 설계되었으며 단순한 데이터 기록을 넘어, 모든 비즈니스 프로세스를 '업무(Issue)' 단위로 연결합니다. 이를 통해 팀원들 간의 소통을 원활하게 하고, 모든 의사결정의 근거를 체계적으로 자산화 할 수 있도록 지원합니다.]

## 2. 디렉토리 구조 및 핵심 아키텍처
- `/app/django/`: 백엔드 핵심 코드. 
  - **API 구조**: `apiV1/` 내에서 `serializers/`와 `views/`를 분리하여 데이터 직렬화 및 비즈니스 로직을 모듈화합니다.
  - **기능 앱**: `accounts`, `book`, `company` 등 도메인별로 앱을 분리하여 관리합니다.
- `/app/vue/`: 프론트엔드 핵심 코드 (Vite/TypeScript). 
  - **데이터 관리**: Pinia를 사용하여 상태(State)를 관리하며, TypeScript를 활용해 데이터 타입 안정성을 보장합니다.
- `/deploy/`: 인프라 코드 (K8s/Helm 차트, Docker 설정, 배포 스크립트).
- `/volume/`: 데이터베이스 유지보수 (백업, 복원 스크립트, 초기화 스크립트).

## 3. 워크플로우 및 표준

### 3.1. 백엔드

- **의존성 관리**: 가상환경을 사용합니다.
- **마이그레이션**: DB 변경 사항 적용 시 반드시 `cd deploy && docker compose exec web sh migrate.sh -m`를 실행하세요.
- **테스트**: `cd deploy && docker compose exec web python manage.py test`를 통해 테스트를 실행합니다.

### 3.2. 프론트엔드

- **의존성 관리**: `pnpm`을 사용합니다.
- **설정**: `.eslintrc.cjs` 및 `.prettierrc.json`의 엄격한 ESLint/Prettier 규칙을 따릅니다.
- **테스트**: 유닛 테스트는 Vitest, E2E 테스트는 Cypress를 사용합니다.

### 3.3. 배포

- **Helm**: 설정은 `/deploy/helm/`에 위치합니다.
- **검증**: 배포 마무리 전 `deploy/scripts/verify_vue_build.sh`와 같은 검증 스크립트를 반드시 실행하세요.

## 4. AI 에이전트 운영 원칙

- **안전 제일**: 인프라/DB 수정(`/deploy`, `/volume`) 시에는 실행 전 반드시 수동 검토를 거쳐야 합니다.
- **검증 필수**: 모든 코드 변경 후에는 반드시 관련 테스트를 실행해야 합니다.
- **청결 유지**: 임시 파일(`.tmp`, `debug.log` 등)을 커밋하지 마세요.
- **커뮤니케이션**: Conventional Commits 형식(`type(scope): description`)을 준수하세요.
- **문서화**: 코드 변경 시, 이 파일이나 관련 모듈의 README를 반드시 업데이트하세요.

---
*최종 업데이트: 2026-06-27*
