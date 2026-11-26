export interface AccountPicker {
  value: number
  label: string
  parent: number | null
  is_cate_only: boolean
  depth: number
  category: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense' | 'transfer' | 'cancel'
  direction: '입금' | '출금'
  req_affiliate?: boolean
  is_payment?: boolean
  requires_contract?: boolean
  is_related_contractor?: boolean
}

export interface BankCode {
  pk: number
  code: string
  name: string
}

export interface Affiliate {
  pk: number
  sort: 'company' | 'project'
  sort_display: string
  company: number | null
  company_name: string | null
  project: number | null
  project_name: string | null
  description: string
  created_at: string
  updated_at: string
}

export interface BalanceByAccount {
  bank_acc: string
  bank_num: string
  date_inc: number
  date_out: number
  inc_sum: number | null
  out_sum: number | null
  balance?: number
}

// 기존 comLedger 타입 (Manage 페이지에서 사용)
export interface CompanyBank {
  pk?: number
  company?: number
  depart: number | null
  depart_name?: string
  bankcode: number | null
  bankcode_name?: string
  order?: number | null
  alias_name: string
  number: string
  holder: string
  open_date: string | null
  note: string
  is_hide: boolean
  inactive: boolean
  balance?: number
}

export interface CompanyAccount {
  pk?: number
  code: string
  name: string
  description: string
  parent: number | null
  parent_name?: string | null
  depth: number
  category: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense' | 'transfer' | 'cancel'
  category_display: '자산' | '부채' | '자본' | '수익' | '비용' | '대체' | '취소'
  direction: 'deposit' | 'withdraw'
  direction_display: '입금' | '출금'
  computed_direction: 'deposit' | 'withdraw' | 'both'
  computed_direction_display: '입금' | '출금' | '입금/출금'
  is_category_only: boolean
  is_transfer_fee: boolean
  is_active: boolean
  requires_affiliate: boolean
  order: number
  full_path: string
  children_count: number
}

export interface BankTransaction {
  pk?: number
  transaction_id?: string
  company: number
  bank_account: number
  bank_account_name: string
  deal_date: string
  amount: number
  sort: 1 | 2
  sort_name: '입금' | '출금'
  content: string
  note: string
  creator: number | null
  creator_name: string | null
  created_at: string
  updated_at: string
  is_balanced: boolean
  accounting_entries: AccountingEntry[]
}

export type EvidenceTypeCode = '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'

export interface AccountingEntry {
  pk: number
  transaction_id: string
  company: number
  sort: 1 | 2
  sort_name: '입금' | '출금'
  account: number
  account_name: string
  account_code: string
  account_full_path: string
  affiliate: number | null
  affiliate_display: string | null
  amount: number
  trader: string | null
  evidence_type: EvidenceTypeCode | null
  evidence_type_display:
    | ''
    | '증빙없음'
    | '세금계산서'
    | '계산서(면세)'
    | '신용/체크카드 매출전표'
    | '현금영수증'
    | '원천징수영수증/지급명세서'
    | '지로용지 및 청구서'
    | null
  created_at: string
  updated_at: string
}

export interface CompositeAccountingEntryPayload {
  pk?: number
  account: number
  affiliate?: number | null
  amount: number
  trader?: string | null
  evidence_type?: EvidenceTypeCode | null
}

export type CompositeAccountingEntryPatchPayload = Partial<CompositeAccountingEntryPayload> & {
  pk: number
}

export interface CompositeTransactionPayload {
  company: number
  bank_account: number
  deal_date: string
  amount: number
  sort: 1 | 2
  content: string
  note?: string
  accounting_entries?: CompositeAccountingEntryPayload[]
}

export type CompositeTransactionPatchPayload = Partial<
  Omit<CompositeTransactionPayload, 'accounting_entries'>
> & {
  pk: number
  accounting_entries?: (CompositeAccountingEntryPatchPayload | CompositeAccountingEntryPayload)[]
}

// UI 표시용 어댑터 타입 (CashBook 구조 모방)
export interface LedgerTransactionForDisplay {
  pk: number
  company: number
  sort: number
  sort_desc: string
  account: string | null
  content: string
  trader: string
  bank_account: number
  bank_account_desc: string
  amount: number
  deal_date: string
  note: string
}

export interface ComCalculated {
  pk?: number
  company: number
  calculated: string
  creator?: number | null
  creator_name?: string
  created_at?: string
  updated_at?: string
}

// 월별 자금 집계
export interface PeriodAmounts {
  prev: number
  cur: number
  ytd: number
}

export interface MonthlySummaryRow extends PeriodAmounts {
  account: number
  code: string
  name: string
  category: string
}

export interface MonthlySummaryGroup extends PeriodAmounts {
  name: string
  rows: MonthlySummaryRow[]
}

export interface MonthlySummaryBlock {
  groups: MonthlySummaryGroup[]
  total: PeriodAmounts
}

export interface MonthlySummaryAffiliatePeriod {
  lend: number
  collect: number
  borrow: number
  repay: number
  other_in: number
  other_out: number
  net: number
}

export interface MonthlySummaryAffiliate {
  affiliate: number
  label: string
  sort: 'company' | 'project'
  cur: MonthlySummaryAffiliatePeriod
  ytd: MonthlySummaryAffiliatePeriod
}

export interface ComMonthlySummary {
  company: number
  from_date: string
  to_date: string
  periods: Record<'prev' | 'cur' | 'ytd', { from: string; to: string }>
  opening_balance: number
  closing_balance: number
  income: { revenue: MonthlySummaryBlock; other: MonthlySummaryBlock; total: PeriodAmounts }
  expense: { cost: MonthlySummaryBlock; other: MonthlySummaryBlock; total: PeriodAmounts }
  operating_net: PeriodAmounts
  net: PeriodAmounts
  transfer: { in: PeriodAmounts; out: PeriodAmounts }
  cancel: { in: PeriodAmounts; out: PeriodAmounts }
  unclassified: { in: PeriodAmounts; out: PeriodAmounts }
  bank_flow: { in: PeriodAmounts; out: PeriodAmounts }
  affiliates: MonthlySummaryAffiliate[]
}
