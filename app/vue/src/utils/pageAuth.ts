import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePermission } from '@/store/pinia/work_permission'
import { PERM, type PermissionCode } from '@/store/constants/permissions'

export const isSuperUser = computed(() => useAccount().superAuth)

/**
 * usePermission 스토어의 can() 메서드와 연동하여 권한을 체크합니다.
 * (하위 호환) StaffAuth 존속 기간 동안 staffAuth 폴백 검사를 함께 지원합니다.
 */
const hasPermission = (code: PermissionCode, fallbackStaffAuthCheck?: () => boolean) => {
  if (isSuperUser.value) return true

  // 1. work_permission 스토어의 can() 권한 검사
  const permStore = usePermission()
  if (permStore.can(code)) return true

  // 2. (StaffAuth 존속 기간) staffAuth 폴백 검사
  if (fallbackStaffAuthCheck && fallbackStaffAuthCheck()) return true

  return false
}

// ── 계약 관리 ──────────────────────────────────────────────────────────
export const read_contract = computed(() =>
  hasPermission(
    PERM.CONTRACT_READ,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.contract !== '0',
  ),
)

export const write_contract = computed(() =>
  hasPermission(
    PERM.CONTRACT_CREATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.contract === '2',
  ),
)

// ── 수납 관리 ──────────────────────────────────────────────────────────
export const read_payment = computed(() =>
  hasPermission(
    PERM.PAYMENT_READ,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.payment !== '0',
  ),
)

export const write_payment = computed(() =>
  hasPermission(
    PERM.PAYMENT_CREATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.payment === '2',
  ),
)

// ── 고지 관리 ──────────────────────────────────────────────────────────
export const read_notice = computed(() =>
  hasPermission(
    PERM.NOTICE_READ,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.notice !== '0',
  ),
)

export const write_notice = computed(() =>
  hasPermission(
    PERM.NOTICE_CREATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.notice === '2',
  ),
)

// ── 사업비 자금/회계 원장 ──────────────────────────────────────────────
export const read_project_cash = computed(() =>
  hasPermission(
    PERM.LEDGER_READ,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.project_ledger !== '0',
  ),
)

export const write_project_cash = computed(() =>
  hasPermission(
    PERM.LEDGER_CREATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.project_ledger === '2',
  ),
)

// ── 사업지 문서 ────────────────────────────────────────────────────────
export const read_project_docs = computed(() =>
  hasPermission(
    PERM.DOCS_READ,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.project_docs !== '0',
  ),
)

export const write_project_docs = computed(() =>
  hasPermission(
    PERM.DOCS_CREATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.project_docs === '2',
  ),
)

// ── 신규 프로젝트 ──────────────────────────────────────────────────────
export const read_project = computed(() =>
  hasPermission(
    PERM.PROJECT_UPDATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.project !== '0',
  ),
)

export const write_project = computed(() =>
  hasPermission(
    PERM.PROJECT_UPDATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.project === '2',
  ),
)

// ── 부지 관리 ──────────────────────────────────────────────────────────
export const read_project_site = computed(() =>
  hasPermission(
    PERM.SITE_READ,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.project_site !== '0',
  ),
)

export const write_project_site = computed(() =>
  hasPermission(
    PERM.SITE_CREATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.project_site === '2',
  ),
)

// ── 본사 회계 관리 ──────────────────────────────────────────────────────
export const read_company_cash = computed(() =>
  hasPermission(
    PERM.LEDGER_READ,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.company_ledger !== '0',
  ),
)

export const write_company_cash = computed(() =>
  hasPermission(
    PERM.LEDGER_CREATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.company_ledger === '2',
  ),
)

// ── 본사 문서 관리 ──────────────────────────────────────────────────────
export const read_company_docs = computed(() =>
  hasPermission(
    PERM.DOCS_READ,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.company_docs !== '0',
  ),
)

export const write_company_docs = computed(() =>
  hasPermission(
    PERM.DOCS_CREATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.company_docs === '2',
  ),
)

// ── 인사 관리 ──────────────────────────────────────────────────────────
export const read_human_resource = computed(() =>
  hasPermission(
    PERM.HR_WORK_READ,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.human_resource !== '0',
  ),
)

export const write_human_resource = computed(() =>
  hasPermission(
    PERM.HR_WORK_CREATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.human_resource === '2',
  ),
)

// ── 회사 관련 설정 ──────────────────────────────────────────────────────
export const read_company_settings = computed(() =>
  hasPermission(
    PERM.PROJECT_UPDATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.company_settings !== '0',
  ),
)

export const write_company_settings = computed(() =>
  hasPermission(
    PERM.PROJECT_UPDATE,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.company_settings === '2',
  ),
)

// ── 권한 설정 관리 ──────────────────────────────────────────────────────
export const read_auth_manage = computed(() =>
  hasPermission(
    PERM.PROJECT_MEMBER,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.auth_manage !== '0',
  ),
)

export const write_auth_manage = computed(() =>
  hasPermission(
    PERM.PROJECT_MEMBER,
    () => !!useAccount().staffAuth && useAccount().staffAuth?.auth_manage === '2',
  ),
)
