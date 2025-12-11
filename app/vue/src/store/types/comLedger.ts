export interface BankCode {
  pk: number
  code: string
  name: string
}

export interface BalanceByAccount {
  bank_acc: string
  bank_num: string
  date_inc: number
  date_out: number
  inc_sum: number | null
  out_sum: number | null
}

// 기존 comLedger 타입 (CashManage 페이지에서 사용)
export interface CompanyBank {
  pk?: number
  company?: number
  depart: number | null
  bankcode: number | null
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
  depth: number
  category: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense' | 'transfer' | 'cancel'
  category_display: '자산' | '부채' | '자본' | '수익' | '비용' | '대체' | '취소'
  direction: 'deposit' | 'withdraw'
  direction_display: '입금' | '출금'
  computed_direction: 'deposit' | 'withdraw'
  computed_direction_display: '입금' | '출금'
  is_category_only: boolean
  is_active: boolean
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
  affiliated: number | null
  affiliated_display: string | null
  amount: number
  trader: string
  evidence_type: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
  evidence_type_display:
    | ''
    | '증빙없음'
    | '세금계산서'
    | '계산서(면세)'
    | '신용/체크카드 매출전표'
    | '현금영수증'
    | '원천징수영수증/지급명세서'
    | '지로용지 및 청구서'
  created_at: string
  updated_at: string
}

// Ledger 전용 타입 (새로운 ledger 앱)
export interface CompanyBankAccount {
  pk: number
  company: number
  depart: number | null
  depart_name?: string
  bankcode: number
  bankcode_name?: string
  order: number | null
  alias_name: string
  number: string
  holder: string
  open_date: string | null
  note: string
  is_hide: boolean
  inactive: boolean
}

export interface CompanyBankTransaction {
  pk: number
  transaction_id: string
  company: number
  bank_account: number
  bank_account_name?: string
  deal_date: string
  amount: number
  sort: number // 1=입금, 2=출금
  sort_name?: string
  content: string
  note: string
  creator?: number
  creator_name?: string
  created_at?: string
  updated_at?: string
  accounting_entries?: CompanyAccountingEntry[]
}

export interface CompanyAccountingEntry {
  pk: number
  transaction_id: string
  company: number
  sort: number
  sort_name?: string
  account: number
  account_name?: string
  account_code?: string
  amount: number
  trader: string
  evidence_type: string
}

// UI 표시용 어댑터 타입 (CashBook 구조 모방)
export interface LedgerTransactionForDisplay {
  pk: number
  company: number
  sort: number
  sort_desc?: string
  account_d1: null
  account_d2: null
  account_d3: null
  content: string
  trader: string
  bank_account: number
  bank_account_desc?: string
  income: number | null
  outlay: number | null
  deal_date: string
  note: string
}

export interface ComCalculated {
  pk?: number
  company: number
  calculated: string
  creator?: { pk: number; username: string }
}
