import type {
  ApprovalContent,
  DocumentStatus,
  DocumentType,
  SecurityLevel,
  SimpleUser,
  StepStatus,
} from '@/store/types/approval'
import type { User } from '@/store/types/accounts'
import { addDaysToDate, getToday } from '@/utils/baseMixins'
import { sanitizeExternalUrl } from '@/utils/helper'

export interface SelectOption {
  value: string
  label: string
}

// ── 타입 안전 콘텐츠 접근 헬퍼 ───────────────────────────
export const asStr = (val: unknown, fallback = ''): string => {
  if (val === null || val === undefined) return fallback
  return String(val)
}

export const asNum = (val: unknown, fallback = 0): number => {
  if (val === null || val === undefined || val === '') return fallback
  const n = Number(val)
  return Number.isFinite(n) ? n : fallback
}

export const asOptNum = (val: unknown): number | null => {
  if (val === null || val === undefined || val === '') return null
  const n = Number(val)
  return Number.isFinite(n) ? n : null
}

export const asBool = (val: unknown, fallback = false): boolean => {
  if (typeof val === 'boolean') return val
  return fallback
}

export const asList = <T>(val: unknown): T[] => {
  return Array.isArray(val) ? (val as T[]) : []
}

export const firstStr = (...vals: unknown[]): string => {
  for (const v of vals) {
    if (v !== null && v !== undefined && String(v) !== '') return String(v)
  }
  return ''
}

export const firstNum = (...vals: unknown[]): number => {
  for (const v of vals) {
    if (v !== null && v !== undefined && v !== '') {
      const n = Number(v)
      if (Number.isFinite(n)) return n
    }
  }
  return 0
}

export const parseSignedNumberInput = (raw: string): number | '' => {
  const trimmed = raw.trim()
  if (!trimmed || trimmed === '-' || trimmed === '+') return ''
  const parsed = Number(trimmed)
  return Number.isFinite(parsed) ? parsed : ''
}

export const parseNonNegativeNumberInput = (raw: string): number | '' => {
  const parsed = parseSignedNumberInput(raw)
  if (parsed === '') return ''
  return Math.max(0, parsed)
}

export const APPROVAL_AMOUNT_KEYS = [
  'amount',
  'total_amount',
  'contract_amount',
  'advance_amount',
  'requested_amount',
  'approval_budget',
  'financial_impact',
  'dispute_amount',
  'action_budget',
  'total_cost',
  'total_budget',
  'settlement_amount',
  'budget',
  'congratulation_amount',
  'estimated_amount',
  'price',
  'cost',
  'expense_amount',
  'payment_amount',
] as const

export const extractApprovalAmount = (content?: ApprovalContent | null): number | null => {
  if (!content) return null
  for (const key of APPROVAL_AMOUNT_KEYS) {
    const val = content[key]
    if (val !== undefined && val !== null && val !== '') {
      const n = Number(val)
      if (Number.isFinite(n)) return n
    }
  }
  return null
}

export const resolveRegistryEntry = <T>(
  registry: Record<string, T>,
  docType?: Pick<DocumentType, 'form_template_key' | 'code'> | null,
): T | undefined => {
  if (!docType) return undefined
  for (const raw of [docType.form_template_key, docType.code]) {
    const key = (raw ?? '').trim().toUpperCase()
    if (key && registry[key]) return registry[key]
  }
  return undefined
}

// ── 공통 날짜 / 포맷 / URL / 사용자 헬퍼 ──────────────────
/** KST(UTC+9) 기준 오늘 날짜(YYYY-MM-DD) 반환 */
export const getLocalToday = (): string => getToday()

/** KST 기준 오늘로부터 N일 후(YYYY-MM-DD) 반환 */
export const addLocalDays = (days: number): string => addDaysToDate(getToday(), days)

/** 두 YYYY-MM-DD 날짜 간 포함 일수 계산 (종료일 < 시작일이면 0) */
export const calcInclusiveDays = (startDate: string, endDate: string): number => {
  if (!startDate || !endDate) return 0
  const sMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(startDate)
  const eMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(endDate)
  if (!sMatch || !eMatch) return 0
  const d1 = new Date(Number(sMatch[1]), Number(sMatch[2]) - 1, Number(sMatch[3]))
  const d2 = new Date(Number(eMatch[1]), Number(eMatch[2]) - 1, Number(eMatch[3]))
  if (d2 < d1) return 0
  return Math.round((d2.getTime() - d1.getTime()) / (1000 * 60 * 60 * 24)) + 1
}

export const fmtDate = (d: string | null | undefined): string => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('ko-KR')
}

export const fmtDatetime = (d: string | null | undefined): string => {
  if (!d) return '-'
  return new Date(d).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export const formatFileSize = (bytes: number | null | undefined): string => {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export const toSafeUrl = (url: string | null | undefined): string => sanitizeExternalUrl(url)

export const getSafeExternalUrl = (url: string | null | undefined): string => {
  const safe = toSafeUrl(url)
  return safe === '#' ? '' : safe
}

export const getUserDisplayName = (user?: SimpleUser | null): string =>
  user?.full_name || user?.username || '-'

export const filterStaffUserOptions = (users: User[], excludeUserId?: number | null) =>
  users
    .filter(
      u =>
        u.pk !== excludeUserId && u.is_active && (u.has_staff || u.is_superuser),
    )
    .map(u => ({
      value: u.pk as number,
      title: u.profile?.name ? `${u.profile.name} (${u.username})` : u.username,
    }))

// ── 문서/단계 상태 및 보안등급 메타 ──────────────────────
export const DOC_STATUS_LABEL: Record<DocumentStatus, string> = {
  draft: '임시저장',
  pending: '결재중',
  approved: '승인완료',
  rejected: '반려',
  cancelled: '취소',
}

export const DOC_STATUS_DETAIL_LABEL: Record<DocumentStatus, string> = {
  ...DOC_STATUS_LABEL,
  approved: '최종승인',
}

export const DOC_STATUS_CHIP_COLOR: Record<DocumentStatus, string> = {
  draft: 'blue-grey-lighten-2',
  pending: 'warning',
  approved: 'success',
  rejected: 'error',
  cancelled: 'grey-darken-2',
}

export const STEP_STATUS_LABEL: Record<StepStatus, string> = {
  pending: '대기',
  approved: '승인',
  rejected: '반려',
  skipped: '건너뜀',
}

export const STEP_STATUS_CHIP_COLOR: Record<StepStatus, string> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'error',
  skipped: 'secondary',
}

export const SECURITY_LEVEL_META: Record<
  SecurityLevel,
  { label: string; shortLabel: string; color: string; icon: string }
> = {
  '1': { label: '1등급 (비공개)', shortLabel: '🔒 1등급', color: 'error', icon: 'mdi-lock' },
  '2': {
    label: '2등급 (부서공개)',
    shortLabel: '👥 2등급',
    color: 'primary',
    icon: 'mdi-account-group',
  },
  '3': { label: '3등급 (전사공개)', shortLabel: '🌐 3등급', color: 'success', icon: 'mdi-earth' },
}

const findOptionLabel = (
  options: SelectOption[],
  val: unknown,
  fallback = '-',
): string => {
  const key = asStr(val)
  if (!key) return fallback
  return options.find(o => o.value === key)?.label ?? key
}

// ── 양식별 옵션 및 라벨 매핑 ─────────────────────────────
export const LEAVE_TYPE_OPTIONS: SelectOption[] = [
  { value: 'ANNUAL', label: '연차' },
  { value: 'HALF_AM', label: '오전 반차 (0.5일)' },
  { value: 'HALF_PM', label: '오후 반차 (0.5일)' },
  { value: 'SPECIAL', label: '경조사 휴가' },
  { value: 'SICK', label: '병가' },
  { value: 'REWARD', label: '포상 휴가' },
  { value: 'OTHER', label: '기타 휴가' },
]
export const getLeaveTypeLabel = (code: unknown): string =>
  findOptionLabel(LEAVE_TYPE_OPTIONS, code, '연차')

export const EXPENSE_TYPE_OPTIONS: SelectOption[] = [
  { value: 'CARD', label: '법인카드' },
  { value: 'TAX_INVOICE', label: '세금계산서' },
  { value: 'RECEIPT', label: '현금영수증/간이영수증' },
  { value: 'TRANSFER', label: '일반 계좌이체' },
]
export const getExpenseTypeLabel = (code: unknown): string =>
  findOptionLabel(EXPENSE_TYPE_OPTIONS, code, '법인카드')

export const BUDGET_ACCOUNT_OPTIONS: SelectOption[] = [
  { value: 'NONE', label: '예산 비소요 (0원)' },
  { value: 'GENERAL_EXPENSE', label: '일반관리비 / 경상운영비' },
  { value: 'PROJECT_COST', label: '사업비 / 현장 직접비' },
  { value: 'OUTSOURCING', label: '외주 용역비' },
  { value: 'MARKETING', label: '홍보 및 마케팅비' },
  { value: 'ASSET_PURCHASE', label: '자산 취득비' },
  { value: 'OTHER', label: '기타 예산' },
]
export const getBudgetAccountLabel = (code: unknown): string =>
  findOptionLabel(BUDGET_ACCOUNT_OPTIONS, code, '-')

export const TRIP_TYPE_OPTIONS: SelectOption[] = [
  { value: 'DOMESTIC', label: '국내 출장' },
  { value: 'OVERSEAS', label: '해외 출장' },
]
export const getTripTypeLabel = (code: unknown): string =>
  findOptionLabel(TRIP_TYPE_OPTIONS, code, '국내 출장')

export const TRANSPORT_METHOD_OPTIONS: SelectOption[] = [
  { value: 'CORP_CAR', label: '법인 차량' },
  { value: 'PRIVATE_CAR', label: '개인 차량 (유류비/통행료 청구)' },
  { value: 'TRAIN', label: 'KTX / SRT / 열차' },
  { value: 'AIRPLANE', label: '항공편 (국내/국제선)' },
  { value: 'BUS', label: '고속 / 시외버스' },
  { value: 'PUBLIC', label: '시내 대중교통' },
  { value: 'OTHER', label: '기타' },
]
export const getTransportMethodLabel = (code: unknown): string =>
  findOptionLabel(TRANSPORT_METHOD_OPTIONS, code, '법인 차량')

export const WORK_TYPE_OPTIONS: SelectOption[] = [
  { value: 'OVERTIME', label: '평일 연장근무' },
  { value: 'NIGHT', label: '야간근무 (22시 이후)' },
  { value: 'HOLIDAY', label: '휴일 (주말/공휴일) 근무' },
]
export const getWorkTypeLabel = (code: unknown): string =>
  findOptionLabel(WORK_TYPE_OPTIONS, code, '평일 연장근무')

export const COMPENSATION_TYPE_OPTIONS: SelectOption[] = [
  { value: 'ALLOWANCE', label: '연장/휴일 수당 지급' },
  { value: 'COMP_LEAVE', label: '대체휴무 (보상휴가) 적립' },
]
export const getCompensationTypeLabel = (code: unknown): string =>
  findOptionLabel(COMPENSATION_TYPE_OPTIONS, code, '연장/휴일 수당 지급')

export const APPOINTMENT_TYPE_OPTIONS: SelectOption[] = [
  { value: 'PROMOTION', label: '승진 / 승격' },
  { value: 'TRANSFER', label: '부서이동 / 전보' },
  { value: 'APPOINT', label: '보직 임명 / 해임' },
  { value: 'HIRE', label: '신규 채용 / 입사' },
  { value: 'LEAVE_RETURN', label: '휴직 / 복직' },
  { value: 'RETIRE', label: '퇴직 / 면직' },
  { value: 'DISPATCH', label: '현장 파견 / 복귀' },
  { value: 'ORGANIZATION', label: '조직 개편 발령' },
  { value: 'OTHER', label: '기타 발령' },
]
export const getAppointmentTypeLabel = (code: unknown): string =>
  findOptionLabel(APPOINTMENT_TYPE_OPTIONS, code, '승진 / 승격')

export const HR_REQUEST_TYPE_OPTIONS: SelectOption[] = [
  { value: 'CERTIFICATE', label: '제증명서 발급 신청' },
  { value: 'CONGRATULATION_CONDOLENCE', label: '경조사 지원 / 경조금 신청' },
  { value: 'LEAVE_OF_ABSENCE', label: '휴직 신청원' },
  { value: 'REINSTATEMENT', label: '복직원 제출' },
  { value: 'ACCOUNT_CHANGE', label: '급여계좌 / 개인정보 변경' },
  { value: 'BENEFIT', label: '기타 복리후생 신청' },
  { value: 'OTHER', label: '기타 인사 신청' },
]
export const getHrRequestTypeLabel = (code: unknown): string =>
  findOptionLabel(HR_REQUEST_TYPE_OPTIONS, code, '제증명서 발급 신청')

export const CERT_TYPE_OPTIONS: SelectOption[] = [
  { value: 'EMPLOYMENT', label: '재직증명서' },
  { value: 'CAREER', label: '경력증명서' },
  { value: 'RETIREMENT', label: '퇴직증명서' },
  { value: 'WITHHOLDING_TAX', label: '원천징수영수증' },
  { value: 'PAY_SLIP', label: '급여명세확인서' },
  { value: 'OTHER', label: '기타 증명서' },
]
export const getCertTypeLabel = (code: unknown): string =>
  findOptionLabel(CERT_TYPE_OPTIONS, code, '재직증명서')

export const EVENT_TYPE_OPTIONS: SelectOption[] = [
  { value: 'MARRIAGE_SELF', label: '본인 결혼' },
  { value: 'MARRIAGE_CHILD', label: '자녀 결혼' },
  { value: 'CHILSOON_PARENT', label: '부모 칠순/팔순' },
  { value: 'DEATH_PARENT', label: '부모/배우자부모 사망' },
  { value: 'DEATH_GRANDPARENT', label: '조부모 사망' },
  { value: 'CHILDBIRTH', label: '출산 축하' },
  { value: 'OTHER', label: '기타 경조사' },
]
export const getEventTypeLabel = (code: unknown): string =>
  findOptionLabel(EVENT_TYPE_OPTIONS, code, '-')

export const RECEIVE_METHOD_OPTIONS: SelectOption[] = [
  { value: 'PDF_EMAIL', label: '전자문서 (PDF 이메일 수신)' },
  { value: 'PRINT_DIRECT', label: '실물 원본 직접 수령' },
  { value: 'POST', label: '우편(등기) 수령' },
]
export const getReceiveMethodLabel = (code: unknown): string =>
  findOptionLabel(RECEIVE_METHOD_OPTIONS, code, '전자문서 (PDF 이메일 수신)')

export const SETTLEMENT_TYPE_OPTIONS: SelectOption[] = [
  { value: 'CORP_CARD', label: '법인카드 사용 내역 정산' },
  { value: 'PERSONAL_EXPENSE', label: '개인비용 실비 환급 청구' },
  { value: 'BUSINESS_TRIP', label: '출장 경비 사후 정산' },
  { value: 'ADVANCE_PAY', label: '가지급금 사후 정산' },
  { value: 'OTHER', label: '기타 경비 정산' },
]
export const getSettlementTypeLabel = (code: unknown): string =>
  findOptionLabel(SETTLEMENT_TYPE_OPTIONS, code, '법인카드 사용 내역 정산')

export const EXPENSE_CATEGORIES = [
  '복리후생비(식대/음료)',
  '여비교통비(택시/대중교통/유류)',
  '회의비/접대비',
  '소모품비/사무용품',
  '도서인쇄비/교육훈련비',
  '지급수수료/통신비',
  '기타',
]

export const ADVANCE_TYPE_OPTIONS: SelectOption[] = [
  { value: 'ADVANCE_PAY', label: '가지급금 (업무용 선지급 경비)' },
  { value: 'PREPAYMENT', label: '선급금 (계약상 대금 선지급)' },
  { value: 'IMPREST_FUND', label: '전도금 (현장/부서 상비 운영비)' },
  { value: 'EVENT_FUND', label: '행사 / 프로젝트 진행비' },
  { value: 'OTHER', label: '기타 선급금' },
]
export const getAdvanceTypeLabel = (code: unknown): string =>
  findOptionLabel(ADVANCE_TYPE_OPTIONS, code, '가지급금 (업무용 선지급 경비)')

export const RECEIVER_TYPE_OPTIONS: SelectOption[] = [
  { value: 'EMPLOYEE', label: '임직원 계좌' },
  { value: 'VENDOR', label: '거래처 직접지급' },
  { value: 'OTHER', label: '기타 계좌' },
]
export const getReceiverTypeLabel = (code: unknown): string =>
  findOptionLabel(RECEIVER_TYPE_OPTIONS, code, '임직원 계좌')

export const CONTRACT_TYPE_OPTIONS: SelectOption[] = [
  { value: 'CONSTRUCTION', label: '공사 도급 / 하도급 계약' },
  { value: 'SERVICE', label: '용역 / 설계 / 감리 / PM 계약' },
  { value: 'PURCHASE', label: '물품 공급 / 자재 구매 계약' },
  { value: 'LEASE', label: '부동산 임대차 / 시설물 계약' },
  { value: 'MOU_NDA', label: '업무협약(MOU) / 비밀유지(NDA)' },
  { value: 'OTHER', label: '기타 일반 계약' },
]
export const getContractTypeLabel = (code: unknown): string =>
  findOptionLabel(CONTRACT_TYPE_OPTIONS, code, '기타 일반 계약')

export const CONTRACT_KIND_OPTIONS: SelectOption[] = [
  { value: 'NEW', label: '신규 계약' },
  { value: 'CHANGE', label: '변경 (증액 / 감액 / 연장)' },
  { value: 'RENEWAL', label: '갱신 / 연장 계약' },
]
export const getContractKindLabel = (code: unknown): string =>
  findOptionLabel(CONTRACT_KIND_OPTIONS, code, '신규 계약')

export const VAT_TYPE_OPTIONS: SelectOption[] = [
  { value: 'EXCLUDED', label: 'VAT 별도' },
  { value: 'INCLUDED', label: 'VAT 포함' },
  { value: 'ZERO_TAX', label: '면세 / 영세율' },
]
export const getVatTypeLabel = (code: unknown): string =>
  findOptionLabel(VAT_TYPE_OPTIONS, code, 'VAT 별도')

export const CONTRACT_CHANGE_TYPE_OPTIONS: SelectOption[] = [
  { value: 'COMPREHENSIVE', label: '복합 변경 (금액 + 기간 변경)' },
  { value: 'AMOUNT_CHANGE', label: '금액 변경 (증액 / 감액)' },
  { value: 'PERIOD_CHANGE', label: '기간 변경 (공기 / 과업기간 연장)' },
  { value: 'SCOPE_CHANGE', label: '과업 범위 및 조건 변경' },
  { value: 'TERMINATION', label: '계약 중도 해지 / 합의 해제' },
]
export const getContractChangeTypeLabel = (code: unknown): string =>
  findOptionLabel(CONTRACT_CHANGE_TYPE_OPTIONS, code, '복합 변경 (금액 + 기간 변경)')

export const LEGAL_REVIEW_TYPE_OPTIONS: SelectOption[] = [
  { value: 'CONTRACT_REVIEW', label: '계약서 / 협약서 사전 법률 검토' },
  { value: 'LITIGATION_DISPUTE', label: '소송 / 지급명령 / 분쟁 대응 검토' },
  { value: 'REGULATORY_COMPLIANCE', label: '법령 해석 / 규제 및 인허가 자문' },
  { value: 'INTERNAL_RULE', label: '사규 / 취업규칙 / 내부규정 검토' },
  { value: 'CLAIM_NOTICE', label: '내용증명 / 공문 / 대외 발송문 검토' },
  { value: 'OTHER', label: '기타 법률 자문' },
]
export const getLegalReviewTypeLabel = (code: unknown): string =>
  findOptionLabel(LEGAL_REVIEW_TYPE_OPTIONS, code, '기타 법률 자문')

export const LEGAL_URGENCY_OPTIONS: SelectOption[] = [
  { value: 'NORMAL', label: '보통 (3~5영업일)' },
  { value: 'URGENT', label: '긴급 (1~2영업일)' },
  { value: 'VERY_URGENT', label: '당일 긴급' },
]
export const getLegalUrgencyLabel = (code: unknown): string =>
  findOptionLabel(LEGAL_URGENCY_OPTIONS, code, '보통 (3~5영업일)')

export const RISK_LEVEL_OPTIONS: SelectOption[] = [
  { value: 'LOW', label: '낮음 (원안 체결/진행 가능)' },
  { value: 'MEDIUM', label: '중간 (수정 권고 조항 반영 후 진행)' },
  { value: 'HIGH', label: '높음 (중대한 불리 조항 존재 / 진행 재검토)' },
]
export const getRiskLevelLabel = (code: unknown): string =>
  findOptionLabel(RISK_LEVEL_OPTIONS, code, '낮음 (원안 체결/진행 가능)')

export const BIZ_TYPE_OPTIONS: SelectOption[] = [
  { value: 'DEV_SELF', label: '자체 개발사업 (토지 매입 시행)' },
  { value: 'DEV_TRUST', label: '토지신탁 / 관리형 토지신탁' },
  { value: 'CONTRACT_CIVIL', label: '단순 도급 공사 (시공/수주)' },
  { value: 'REDEVELOPMENT', label: '재개발 / 재건축 정비사업' },
  { value: 'PF_INVEST', label: '지분 투자 / 공동 개발' },
  { value: 'OTHER', label: '기타 신규 사업' },
]
export const getBizTypeLabel = (code: unknown): string =>
  findOptionLabel(BIZ_TYPE_OPTIONS, code, '기타 신규 사업')

export const BIZ_APPROVAL_TYPE_OPTIONS: SelectOption[] = [
  { value: 'NEW_LAUNCH', label: '신규 사업 공식 론칭 / 부지 매입 착수 승인' },
  { value: 'LAND_ACQUISITION', label: '토지 매매계약 체결 및 계약금 집행 승인' },
  { value: 'SPC_ESTABLISH', label: '시행 법인(SPC / PFV) 설립 및 출자 승인' },
  { value: 'PF_EXECUTION', label: '본 PF 금융약정 체결 및 사업비 인출 승인' },
  { value: 'CONSTRUCTION_START', label: '시공사 도급계약 및 본 착공 승인' },
  { value: 'OTHER', label: '기타 주요 사업 마일스톤 승인' },
]
export const getBizApprovalTypeLabel = (code: unknown): string =>
  findOptionLabel(BIZ_APPROVAL_TYPE_OPTIONS, code, '기타 주요 사업 마일스톤 승인')

export const PROJECT_DECISION_TYPE_OPTIONS: SelectOption[] = [
  { value: 'DESIGN_SPEC', label: '설계 변경 / 마감재 / 상품 스펙 결정' },
  { value: 'SALES_PRICING', label: '분양가 책정 / 분양 시기 및 조건 결정' },
  { value: 'CONSTRUCTION_METHOD', label: '시공 공법 / 가설 / 주요 자재 선정' },
  { value: 'FINANCIAL_STRUCTURING', label: '금융 구조 / PF 대주단 조건 / 자금 조달 변경' },
  { value: 'CLAIM_DISPUTE', label: '중대 민원 / 행정처분 / 소송·분쟁 대응 방향' },
  { value: 'CONTRACTOR_TERMINATION', label: '주요 협력업체 선정 및 타절·대체 결정' },
  { value: 'OTHER', label: '기타 프로젝트 주요 의사결정' },
]
export const getProjectDecisionTypeLabel = (code: unknown): string =>
  findOptionLabel(PROJECT_DECISION_TYPE_OPTIONS, code, '기타 프로젝트 주요 의사결정')

export const PROJECT_DECISION_URGENCY_OPTIONS: SelectOption[] = [
  { value: 'NORMAL', label: '보통 (정기 검토)' },
  { value: 'URGENT', label: '긴급 (금주 내 결정)' },
  { value: 'CRITICAL', label: '즉시 결정 (공정/인허가 지연 임박)' },
]
export const getProjectDecisionUrgencyLabel = (code: unknown): string =>
  findOptionLabel(PROJECT_DECISION_URGENCY_OPTIONS, code, '보통 (정기 검토)')

export const INBOUND_ACTION_TYPE_OPTIONS: SelectOption[] = [
  { value: 'REPLY_LETTER', label: '대외 회신(답신) 공문 발송 필요' },
  { value: 'INTERNAL_ACTION', label: '내부 조치 및 처리 (회신 불필요)' },
  { value: 'RECEIPT_ONLY', label: '단순 접수 및 부서 공람 / 보고' },
  { value: 'BUDGET_ACTION', label: '예산 집행 및 시정·보수 조치 수반' },
  { value: 'OTHER', label: '기타' },
]
export const getInboundActionTypeInfo = (code: unknown): { label: string; color: string } => {
  const key = asStr(code)
  const colorMap: Record<string, string> = {
    REPLY_LETTER: 'primary',
    INTERNAL_ACTION: 'success',
    RECEIPT_ONLY: 'info',
    BUDGET_ACTION: 'warning',
    OTHER: 'secondary',
  }
  return {
    label: findOptionLabel(INBOUND_ACTION_TYPE_OPTIONS, key, '대외 회신(답신) 공문 발송 필요'),
    color: colorMap[key] ?? 'primary',
  }
}

export const INBOUND_URGENCY_OPTIONS: SelectOption[] = [
  { value: 'NORMAL', label: '보통' },
  { value: 'URGENT', label: '긴급' },
  { value: 'VERY_URGENT', label: '당일/익일 긴급' },
]
export const getInboundUrgencyInfo = (code: unknown): { label: string; color: string } | null => {
  const key = asStr(code)
  if (!key) return null
  const colorMap: Record<string, string> = {
    NORMAL: 'secondary',
    URGENT: 'warning',
    VERY_URGENT: 'error',
  }
  return {
    label: findOptionLabel(INBOUND_URGENCY_OPTIONS, key, key),
    color: colorMap[key] ?? 'secondary',
  }
}

export const SEND_METHOD_OPTIONS: SelectOption[] = [
  { value: 'EMAIL', label: '전자우편 (이메일)' },
  { value: 'POST', label: '등기우편' },
  { value: 'DIRECT', label: '인편 (직접전달)' },
  { value: 'FAX', label: '팩스 (FAX)' },
  { value: 'OTHER', label: '기타' },
]
export const getSendMethodLabel = (code: unknown): string =>
  findOptionLabel(SEND_METHOD_OPTIONS, code, '전자우편 (이메일)')

export const FALLBACK_SEAL_TYPE_OPTIONS: SelectOption[] = [
  { value: 'CORP_SEAL', label: '법인인감 (대표이사 직인)' },
  { value: 'USAGE_SEAL', label: '사용인감' },
  { value: 'DEPT_SEAL', label: '부서/사업소 직인' },
  { value: 'SIGN', label: '서명 (Sign)' },
  { value: 'OMIT', label: '직인생략' },
]
export const getSealTypeLabel = (code: unknown): string =>
  findOptionLabel(FALLBACK_SEAL_TYPE_OPTIONS, code, '법인인감 (대표이사 직인)')
