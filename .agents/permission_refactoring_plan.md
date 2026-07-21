# IBS 권한 관리 시스템 일원화 최종 계획서

> **핵심 원칙**: `StaffAuth`는 리팩터링 완전 완료 시까지 **존속** 유지. 신·구 시스템 병존 후 최종 단계에서 폐기.

---

## 1. 현 시스템 전체 메뉴 vs pageAuth 함수 매핑

| Vue 뷰 디렉토리 | 실제 메뉴 | 현재 pageAuth 함수 | 신규 Permission 모듈 |
|---|---|---|---|
| `views/projects/List` | 프로젝트 기본 정보 | `write_project` | `project` (기존) |
| `views/projects/Building` | 동·호수 관리 | `write_project` | `project` |
| `views/projects/Floor` | 층 정보 관리 | `write_project` | `project` |
| `views/projects/Type`, `Unit` | 타입/유닛 관리 | `write_project` | `project` |
| `views/projects/OrderGroup` | 차수 관리 | `write_project` | `project` |
| `views/projects/PayOrder` | 납부 순서 관리 | `write_project` | `project` |
| `views/projects/Price` | 분양 가격 관리 | `write_project` | `project` |
| `views/projects/DownPay` | 계약금 옵션 | `write_project` | `project` |
| `views/projects/PaidOption` | 유상 옵션 | `write_project` | `project` |
| `views/projects/Required` | 필수 서류 관리 | `write_project` | `project` |
| `views/projects/IncBudget` | 수입 예산 | `write_project` | `project` |
| `views/projects/OutBudget` | 지출 예산 | `write_project` | `project` |
| `views/projects/SiteList` | 사업 부지 목록 | `write_project_site` | **`site`** (신규) |
| `views/projects/SiteOwner` | 사업 부지 소유자 | `write_project_site` | **`site`** |
| `views/projects/SiteContract` | 부지 매입 계약 | `write_project_site` | **`site`** |
| `views/contracts/List` | 계약 목록/등록 | `write_contract` | **`contract`** (신규) |
| `views/contracts/Manage` | 계약 상세 관리 | `write_contract` | **`contract`** |
| `views/contracts/Succession` | 계약 승계 | `write_contract` | **`contract`** |
| `views/contracts/Release` | 계약 해지 | `write_contract` | **`contract`** |
| `views/contracts/Status` | 계약 현황 | `read_contract` | **`contract`** |
| `views/payment/List` | 수납 목록 | `write_payment` | **`payment`** (신규) |
| `views/payment/Register` | 수납 등록 | `write_payment` | **`payment`** |
| `views/notices/Bill` | 분양 대금 고지 | `write_notice` | **`notice`** (신규) |
| `views/notices/Label` | 고지 라벨 출력 | `write_notice` | **`notice`** |
| `views/notices/Mailing` | 우편 발송 관리 | `write_notice` | **`notice`** |
| `views/notices/Sms` | SMS 발송 관리 | `write_notice` | **`notice`** |
| `views/notices/Log` | 고지 발송 이력 | `read_notice` | **`notice`** |
| `views/proLedger/Manage` | 사업비 자금 관리 | `write_project_cash` | **`ledger`** (신규) |
| `views/proLedger/Imprest` | 소액 운영비 관리 | `write_project_cash` | **`ledger`** |
| `views/proLedger/Status` | 자금 현황 | `read_project_cash` | **`ledger`** |
| `views/comLedger/Manage` | 본사 회계 관리 | `write_company_cash` | **`ledger`** |
| `views/comLedger/Status` | 본사 회계 현황 | `read_project_cash` | **`ledger`** |
| `views/proDocs/GeneralDocs` | 사업지 일반 문서 | `write_project_docs` | `docs` (기존) |
| `views/proDocs/LawsuitCase` | 소송 사건 | `write_project_docs` | `docs` |
| `views/proDocs/LawsuitDocs` | 소송 문서 | `write_project_docs` | `docs` |
| `views/comDocs/*` | 본사 문서 전반 | `write_company_docs` | `docs` |
| `views/hrManage/Staff` | 직원 관리 | `write_human_resource` | **`hr_work`** (신규) |
| `views/hrManage/Department` | 부서 관리 | `write_human_resource` | **`hr_work`** |
| `views/hrManage/Duty` | 업무 분장 | `write_human_resource` | **`hr_work`** |
| `views/hrManage/Grade` | 직급 관리 | `write_human_resource` | **`hr_work`** |
| `views/hrManage/Position` | 직위 관리 | `write_human_resource` | **`hr_work`** |
| `views/settings/Authorization` | 권한 설정 | `write_auth_manage` | `project` (기존) |
| `views/settings/Company` | 회사 설정 | `write_company_settings` | `project` (기존) |

---

## 2. Permission 모듈 신구 대응표

### 기존 모듈 (유지/재사용)

| 모듈 코드 | 설명 | 해당 StaffAuth 필드 |
|---|---|---|
| `project` | 건설 프로젝트 설정/관리 + 시스템 설정 | `project`, `project_site`(일부), `company_settings`, `auth_manage` |
| `meeting` | 회의 관리 (업무시스템) | *(StaffAuth 없음, 기존 work 권한)* |
| `issue` | 업무(이슈) 관리 | *(StaffAuth 없음, 기존 work 권한)* |
| `news` | 업무 공지 | *(StaffAuth 없음, 기존 work 권한)* |
| `docs` | 문서 관리 (사업지 + 본사) | `project_docs`, `company_docs` |
| `forum` | 게시판 | *(StaffAuth 없음, 기존 work 권한)* |
| `calendar` | 캘린더 | *(StaffAuth 없음, 기존 work 권한)* |

### 신규 추가 모듈

| 모듈 코드 | 설명 | 해당 StaffAuth 필드 |
|---|---|---|
| **`contract`** | 분양 계약 관리 전반 | `contract` |
| **`payment`** | 분양 수납 관리 | `payment` |
| **`notice`** | 고객 고지 관리 | `notice` |
| **`ledger`** | 자금/회계 원장 (사업비 + 본사) | `project_ledger`, `company_ledger` |
| **`site`** | 사업 부지 정보 관리 | `project_site` |
| **`hr_work`** | 인사 관리 (직원/부서/직급) | `human_resource` |

---

## 3. 전체 Permission 코드 정의 (DB Insert 목록)

### 신규 모듈: `contract`

| code | name | is_default | 비고 |
|---|---|---|---|
| `contract.read` | 계약 조회 | False | 계약 목록/상세/현황 조회 |
| `contract.create` | 계약 등록 | False | 신규 계약 생성 |
| `contract.update` | 계약 수정 | False | 계약 정보 수정 |
| `contract.delete` | 계약 삭제 | False | 계약 삭제 |
| `contract.release` | 계약 해지 처리 | False | 해지 신청~확정 처리 |
| `contract.succession` | 계약 승계 처리 | False | 승계 신청~완료 처리 |

### 신규 모듈: `payment`

| code | name | is_default | 비고 |
|---|---|---|---|
| `payment.read` | 수납 조회 | False | 수납 내역 조회 |
| `payment.create` | 수납 등록 | False | 수납 등록 |
| `payment.update` | 수납 수정 | False | 수납 정보 수정 |
| `payment.delete` | 수납 삭제 | False | 수납 삭제 |

### 신규 모듈: `notice`

| code | name | is_default | 비고 |
|---|---|---|---|
| `notice.read` | 고지 조회 | False | 고지 내역 조회 |
| `notice.create` | 고지 발송 | False | 고지서 발송/라벨/SMS |
| `notice.update` | 고지 수정 | False | 발송 내역 수정 |
| `notice.delete` | 고지 삭제 | False | 발송 내역 삭제 |

### 신규 모듈: `ledger`

| code | name | is_default | 비고 |
|---|---|---|---|
| `ledger.read` | 원장 조회 | False | 자금 현황 조회 |
| `ledger.create` | 원장 등록 | False | 회계 분개 생성 |
| `ledger.update` | 원장 수정 | False | 회계 분개 수정 |
| `ledger.delete` | 원장 삭제 | False | 회계 분개 삭제 |

### 신규 모듈: `site`

| code | name | is_default | 비고 |
|---|---|---|---|
| `site.read` | 부지 조회 | False | 부지/소유자/계약 조회 |
| `site.create` | 부지 등록 | False | 부지 정보 등록 |
| `site.update` | 부지 수정 | False | 부지 정보 수정 |
| `site.delete` | 부지 삭제 | False | 부지 정보 삭제 |

### 신규 모듈: `hr_work`

| code | name | is_default | 비고 |
|---|---|---|---|
| `hr_work.read` | 인사 조회 | False | 직원/부서/직급 조회 |
| `hr_work.create` | 인사 등록 | False | 직원/부서 등록 |
| `hr_work.update` | 인사 수정 | False | 직원/부서 수정 |
| `hr_work.delete` | 인사 삭제 | False | 직원/부서 삭제 |

---

## 4. pageAuth.ts 함수 ↔ Permission 코드 최종 매핑

```
기존 함수명 (유지)              → 신규 Permission 코드
─────────────────────────────────────────────────
read_contract               →  contract.read
write_contract              →  contract.create  (OR contract.update 포함)

read_payment                →  payment.read
write_payment               →  payment.create

read_notice                 →  notice.read
write_notice                →  notice.create

read_project_cash           →  ledger.read
write_project_cash          →  ledger.create

read_company_cash           →  ledger.read        ← 동일 모듈, 컨텍스트(본사 프로젝트)로 분리
write_company_cash          →  ledger.create

read_project_docs           →  docs.read
write_project_docs          →  docs.create

read_company_docs           →  docs.read          ← 동일 모듈, 컨텍스트로 분리
write_company_docs          →  docs.create

read_project_site           →  site.read
write_project_site          →  site.create

read_human_resource         →  hr_work.read
write_human_resource        →  hr_work.create

read_project                →  project.read (기존)
write_project               →  project.update (기존)

read_company_settings       →  project.update (기존, 관리자 수준)
write_company_settings      →  project.update

read_auth_manage            →  project.member (기존, 멤버 관리 권한)
write_auth_manage           →  project.member
```

---

## 5. 단계별 실행 계획

### Phase 1 — Permission 모델 확장 및 데이터 삽입

**변경 파일**: `app/django/work/models/project.py`

```diff
  MODULE_CHOICES = (
      ('project', '프로젝트'), ('meeting', '회의'), ('issue', '업무'),
      ('news', '공지'), ('docs', '문서'), ('forum', '게시판'), ('calendar', '캘린더'),
+     ('contract', '계약 관리'), ('payment', '수납 관리'), ('notice', '고지 관리'),
+     ('ledger', '자금/원장 관리'), ('site', '사업 부지 관리'), ('hr_work', '인사 관리'),
  )
```

이후 Django admin 또는 픽스처로 위 3절의 Permission 코드들을 DB에 INSERT합니다.

> [!IMPORTANT]
> **기존 코드 전혀 수정 없음.** 데이터 추가만 일어납니다. 서비스 무중단.

---

### Phase 2 — 백엔드 ibs_perms.py 신규 작성

`app/django/apiV1/permissions/ibs_perms.py` 신규 생성.  
기존 `auth_perms.py`는 **건드리지 않습니다.**

```python
# apiV1/permissions/ibs_perms.py
from apiV1.permissions.work_perms import ProjectPermission

class IbsModulePermission(ProjectPermission):
    """
    project.Project → work.IssueProject 역추적을 통해
    contract/payment/notice/ledger/site/hr_work 모듈 권한을 검증합니다.
    """

    def _resolve_issue_project(self, request, view):
        """request 에서 project.Project.id를 추출해 IssueProject를 반환"""
        project_id = (
            view.kwargs.get('project') or
            request.data.get('project') or
            request.query_params.get('project')
        )
        if not project_id:
            return None
        from project.models import Project
        try:
            return Project.objects.select_related('issue_project').get(pk=project_id).issue_project
        except (Project.DoesNotExist, AttributeError):
            return None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or getattr(request.user, 'work_manager', False):
            return True

        required_perm = getattr(view, 'required_permission', None)
        if not required_perm:
            return True  # 명시적 권한 선언 없으면 기존 동작 유지

        issue_project = self._resolve_issue_project(request, view)
        if not issue_project:
            return False

        user_perms = set(issue_project.get_user_permissions(request.user))
        return required_perm in user_perms
```

---

### Phase 3 — ViewSet에 required_permission 점진적 추가

각 앱 ViewSet에 `permission_classes`와 `required_permission` 추가.  
**적용 순서**: contract → payment → notice → ledger → site → hr_work

```python
# 예시: ContractViewSet
from apiV1.permissions.ibs_perms import IbsModulePermission

class ContractViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IbsModulePermission)

    @property
    def required_permission(self):
        action_map = {
            'list':           'contract.read',
            'retrieve':       'contract.read',
            'create':         'contract.create',
            'update':         'contract.update',
            'partial_update': 'contract.update',
            'destroy':        'contract.delete',
        }
        return action_map.get(self.action, 'contract.read')
```

> [!TIP]
> ViewSet 하나씩 적용 후 테스트 → 문제 없으면 다음 ViewSet으로 이동.
> 기존 `IsProjectStaffOrReadOnly`는 **제거하지 않고 병렬 유지**.

---

### Phase 4 — 데이터 이관: StaffAuth → Role/Member

#### 권한 매핑 전략

```
StaffAuth.contract == '1'  → contract.read 권한을 가진 Role 부여
StaffAuth.contract == '2'  → contract.read + create + update + delete + release + succession 부여

StaffAuth.payment == '2'   → payment.read + create + update + delete 부여

StaffAuth.notice == '2'    → notice.read + create + update + delete 부여

StaffAuth.project_ledger == '2' → ledger.read + create + update + delete 부여
StaffAuth.company_ledger == '2' → ledger.read + create + update + delete (본사 IssueProject)

StaffAuth.project_site == '2'  → site.read + create + update + delete 부여

StaffAuth.human_resource == '2' → hr_work.read + create + update + delete 부여
```

#### 관리 커맨드로 실행

```bash
# 개발 환경 검증
docker compose exec web python manage.py migrate_staffauth_to_roles --dry-run

# 실제 이관
docker compose exec web python manage.py migrate_staffauth_to_roles
```

---

### Phase 5 — 프론트엔드: permissions.ts + pageAuth.ts 교체

#### 5-1. permissions.ts 상수 추가

```typescript
// store/constants/permissions.ts 에 추가
  // Contract
  CONTRACT_READ:       'contract.read',
  CONTRACT_CREATE:     'contract.create',
  CONTRACT_UPDATE:     'contract.update',
  CONTRACT_DELETE:     'contract.delete',
  CONTRACT_RELEASE:    'contract.release',
  CONTRACT_SUCCESSION: 'contract.succession',

  // Payment
  PAYMENT_READ:   'payment.read',
  PAYMENT_CREATE: 'payment.create',
  PAYMENT_UPDATE: 'payment.update',
  PAYMENT_DELETE: 'payment.delete',

  // Notice
  NOTICE_READ:   'notice.read',
  NOTICE_CREATE: 'notice.create',
  NOTICE_UPDATE: 'notice.update',
  NOTICE_DELETE: 'notice.delete',

  // Ledger
  LEDGER_READ:   'ledger.read',
  LEDGER_CREATE: 'ledger.create',
  LEDGER_UPDATE: 'ledger.update',
  LEDGER_DELETE: 'ledger.delete',

  // Site
  SITE_READ:   'site.read',
  SITE_CREATE: 'site.create',
  SITE_UPDATE: 'site.update',
  SITE_DELETE: 'site.delete',

  // HR Work
  HR_WORK_READ:   'hr_work.read',
  HR_WORK_CREATE: 'hr_work.create',
  HR_WORK_UPDATE: 'hr_work.update',
  HR_WORK_DELETE: 'hr_work.delete',
```

#### 5-2. Pinia 스토어 확장 (account.ts)

로그인 시 현재 선택된 프로젝트의 권한 코드 배열을 API에서 수신하여 저장:

```typescript
// store/pinia/account.ts
interface AccountState {
  ...
  projectPermissions: string[]  // ['contract.read', 'ledger.create', ...]
}
```

#### 5-3. pageAuth.ts 내부 로직 교체 (함수명 완전 유지)

```typescript
// utils/pageAuth.ts (리팩터링 완료 버전)
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { PERM } from '@/store/constants/permissions'

export const isSuperUser = computed(() => useAccount().superAuth)
const perms = computed(() => new Set(useAccount().projectPermissions))
const has = (code: string) => isSuperUser.value || perms.value.has(code)

// ── 기존 함수명 완전 유지 ── 내부 구현만 교체 ──────────────────────

export const read_contract    = computed(() => has(PERM.CONTRACT_READ))
export const write_contract   = computed(() => has(PERM.CONTRACT_CREATE))

export const read_payment     = computed(() => has(PERM.PAYMENT_READ))
export const write_payment    = computed(() => has(PERM.PAYMENT_CREATE))

export const read_notice      = computed(() => has(PERM.NOTICE_READ))
export const write_notice     = computed(() => has(PERM.NOTICE_CREATE))

export const read_project_cash  = computed(() => has(PERM.LEDGER_READ))
export const write_project_cash = computed(() => has(PERM.LEDGER_CREATE))
export const read_company_cash  = computed(() => has(PERM.LEDGER_READ))
export const write_company_cash = computed(() => has(PERM.LEDGER_CREATE))

export const read_project_docs  = computed(() => has(PERM.DOCS_READ))
export const write_project_docs = computed(() => has(PERM.DOCS_CREATE))
export const read_company_docs  = computed(() => has(PERM.DOCS_READ))
export const write_company_docs = computed(() => has(PERM.DOCS_CREATE))

export const read_project_site  = computed(() => has(PERM.SITE_READ))
export const write_project_site = computed(() => has(PERM.SITE_CREATE))

export const read_human_resource  = computed(() => has(PERM.HR_WORK_READ))
export const write_human_resource = computed(() => has(PERM.HR_WORK_CREATE))

export const read_project          = computed(() => has(PERM.PROJECT_UPDATE))
export const write_project         = computed(() => has(PERM.PROJECT_UPDATE))
export const read_company_settings = computed(() => has(PERM.PROJECT_UPDATE))
export const write_company_settings= computed(() => has(PERM.PROJECT_UPDATE))
export const read_auth_manage      = computed(() => has(PERM.PROJECT_MEMBER))
export const write_auth_manage     = computed(() => has(PERM.PROJECT_MEMBER))
```

> [!IMPORTANT]
> **Vue 컴포넌트 파일은 단 한 줄도 수정 불필요.**
> `pageAuth.ts` 함수명이 완전히 유지되므로 모든 import가 그대로 동작합니다.

---

### Phase 6 — StaffAuth 폐기 (최종, 충분한 검증 후)

모든 Phase 완료 및 검증 후 진행:

1. `accounts/models.py`에서 `StaffAuth` 권한 필드 제거 (또는 모델 전체 폐기)
2. `apiV1/permissions/auth_perms.py`의 `StaffAuth` 참조 제거
3. `apiV1/views/accounts.py`의 `StaffAuthViewSet` 제거
4. 프론트엔드 `StaffAuth` 관련 Pinia 스토어 코드 제거
5. 마이그레이션 실행

---

## 6. 전체 진행 체크리스트

```
Phase 1  □ Permission.MODULE_CHOICES에 6개 모듈 추가
         □ 마이그레이션 실행
         □ Permission 코드 26개 DB INSERT (픽스처 작성)

Phase 2  □ apiV1/permissions/ibs_perms.py 신규 작성
         □ 기존 auth_perms.py 무변경 확인

Phase 3  □ contract 앱 ViewSet 적용 + 테스트
         □ payment 앱 ViewSet 적용 + 테스트
         □ notice 앱 ViewSet 적용 + 테스트
         □ ledger 앱 ViewSet 적용 + 테스트
         □ site 앱 ViewSet 적용 + 테스트
         □ hr_work 앱 ViewSet 적용 + 테스트

Phase 4  □ migrate_staffauth_to_roles 커맨드 작성
         □ dry-run으로 결과 검증
         □ 개발 DB 이관 실행
         □ 프로덕션 이관 실행

Phase 5  □ permissions.ts 상수 추가 (26개 신규 코드)
         □ Pinia account 스토어에 projectPermissions 배열 추가
         □ 로그인 API 응답에 권한 코드 배열 포함
         □ pageAuth.ts 내부 로직 교체 (함수명 유지)
         □ 프론트엔드 빌드 및 동작 검증

Phase 6  □ Phase 1~5 완료 및 충분한 검증 확인
         □ StaffAuth 모델 및 관련 코드 폐기
         □ 최종 마이그레이션
         □ 프론트엔드 StaffAuth Pinia 코드 제거
```

---

## 7. 주요 위험 요소 및 대응

| 위험 요소 | 대응 방안 |
|---|---|
| `project.Project`와 `IssueProject`가 연결 안 된 경우 | Phase 4 이관 스크립트에서 누락 감지 및 로그 출력 |
| `company_cash` / `project_cash` 동일 모듈 사용 | 두 경우 모두 `ledger.*` 사용하되, **본사 IssueProject** 컨텍스트로 분리 |
| `docs` 모듈 - 사업지/본사 혼용 | 마찬가지로 컨텍스트(IssueProject)로 분리, 코드는 동일 사용 |
| StaffAuth 즉시 폐기 시 권한 공백 | 원칙: Phase 6은 Phase 1~5 **완전 완료 후** 단독 배포 |
| `write_project_site` 일부 파일에서 `write_project`와 혼용 | Phase 5 pageAuth.ts 교체 시 두 함수 모두 `site.*`로 일관 처리 |
