import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePermission } from '@/store/pinia/work_permission'
import { PERM, type PermissionCode } from '@/store/constants/permissions'

export const isSuperUser = computed(() => useAccount().superAuth)

/**
 * usePermission 스토어의 can() 메서드와 연동하여 권한을 체크합니다.
 * 단수 코드 혹은 코드 배열 중 하나라도 권한이 있는지 검사합니다.
 */
const hasPermission = (code: PermissionCode | PermissionCode[]) => {
  if (isSuperUser.value) return true

  const permStore = usePermission()
  if (Array.isArray(code)) {
    return code.some(c => permStore.can(c))
  }
  return permStore.can(code)
}

// ── 계약 관리 ──────────────────────────────────────────────────────────
export const read_contract = computed(() => hasPermission(PERM.CONTRACT_READ))
export const write_contract = computed(() =>
  hasPermission([PERM.CONTRACT_CREATE, PERM.CONTRACT_UPDATE, PERM.CONTRACT_DELETE]),
)

// ── 수납 관리 ──────────────────────────────────────────────────────────
export const read_payment = computed(() => hasPermission(PERM.PAYMENT_READ))
export const write_payment = computed(() =>
  hasPermission([PERM.PAYMENT_CREATE, PERM.PAYMENT_UPDATE, PERM.PAYMENT_DELETE]),
)

// ── 고지 관리 ──────────────────────────────────────────────────────────
export const read_notice = computed(() => hasPermission(PERM.NOTICE_READ))
export const write_notice = computed(() =>
  hasPermission([PERM.NOTICE_CREATE, PERM.NOTICE_UPDATE, PERM.NOTICE_DELETE]),
)

// ── 사업비 자금/회계 원장 ──────────────────────────────────────────────
export const read_project_cash = computed(() => hasPermission(PERM.LEDGER_READ))
export const write_project_cash = computed(() =>
  hasPermission([PERM.LEDGER_CREATE, PERM.LEDGER_UPDATE, PERM.LEDGER_DELETE]),
)

// ── 사업지 문서 ────────────────────────────────────────────────────────
export const read_project_docs = computed(() => hasPermission(PERM.DOCS_READ))
export const write_project_docs = computed(() =>
  hasPermission([PERM.DOCS_CREATE, PERM.DOCS_UPDATE, PERM.DOCS_DELETE]),
)

// ── 신규 프로젝트 ──────────────────────────────────────────────────────
export const read_project = computed(() => hasPermission(PERM.PROJECT_UPDATE))
export const write_project = computed(() =>
  hasPermission([PERM.PROJECT_CREATE, PERM.PROJECT_UPDATE, PERM.PROJECT_DELETE]),
)

// ── 부지 관리 ──────────────────────────────────────────────────────────
export const read_project_site = computed(() => hasPermission(PERM.SITE_READ))
export const write_project_site = computed(() =>
  hasPermission([PERM.SITE_CREATE, PERM.SITE_UPDATE, PERM.SITE_DELETE]),
)

// ── 본사 회계 관리 ──────────────────────────────────────────────────────
export const read_company_cash = computed(() => hasPermission(PERM.LEDGER_READ))
export const write_company_cash = computed(() =>
  hasPermission([PERM.LEDGER_CREATE, PERM.LEDGER_UPDATE, PERM.LEDGER_DELETE]),
)

// ── 본사 문서 관리 ──────────────────────────────────────────────────────
export const read_company_docs = computed(() => hasPermission(PERM.DOCS_READ))
export const write_company_docs = computed(() =>
  hasPermission([PERM.DOCS_CREATE, PERM.DOCS_UPDATE, PERM.DOCS_DELETE]),
)

// ── 인사 관리 ──────────────────────────────────────────────────────────
export const read_human_resource = computed(() => hasPermission(PERM.HR_WORK_READ))
export const write_human_resource = computed(() =>
  hasPermission([PERM.HR_WORK_CREATE, PERM.HR_WORK_UPDATE, PERM.HR_WORK_DELETE]),
)

// ── 회사 관련 설정 ──────────────────────────────────────────────────────
export const read_company_settings = computed(() => hasPermission(PERM.PROJECT_UPDATE))
export const write_company_settings = computed(() =>
  hasPermission([PERM.PROJECT_CREATE, PERM.PROJECT_UPDATE, PERM.PROJECT_DELETE]),
)

// ── 권한 설정 관리 ──────────────────────────────────────────────────────
export const read_auth_manage = computed(() => hasPermission(PERM.PROJECT_MEMBER))
export const write_auth_manage = computed(() => hasPermission(PERM.PROJECT_MEMBER))


