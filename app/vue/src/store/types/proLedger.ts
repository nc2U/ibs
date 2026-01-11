export interface ProjectBank {
  pk?: number | null
  project: number | null
  bankcode: number | null
  alias_name: string
  number: string
  holder: string
  open_date: string | null
  note: string
  is_hide: boolean
  inactive: boolean
  directpay: boolean
  is_imprest: boolean
  balance?: number
}

export interface ProjectAccount {
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
  computed_direction: 'deposit' | 'withdraw' | 'both'
  computed_direction_display: '입금' | '출금' | '입금/출금'
  is_category_only: boolean
  is_transfer_fee: boolean
  is_active: boolean
  order: number
  is_payment: boolean
  requires_contract: boolean
  is_related_contractor: boolean
  full_path: string
  children_count: number
}

export interface ProBankTrans {
  pk?: number
  transaction_id?: string
  project: number
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
  accounting_entries: ProAccountingEntry[]
}

export interface ProAccountingEntry {
  pk: number
  transaction_id: string
  project: number
  sort: 1 | 2
  sort_name: '입금' | '출금'
  account: number
  account_name: string
  account_code: string
  account_full_path: string
  contract: number | null
  contract_display: string | null
  contractor: number | null
  contractor_display: string | null
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
  contract_payment: {
    pk: number
    contract: number
    contract_serial: string | null
    installment_order: number | null
  } | null
  created_at: string
  updated_at: string
}

// UI 표시용 어댑터 타입 (CashBook 구조 모방)
export interface LedgerTransactionForDisplay {
  pk: number
  project: number
  sort: number
  sort_desc?: string
  account: null
  content: string
  trader: string
  bank_account: number
  bank_account_desc?: string
  amount: number
  deal_date: string
  note: string
}

export type DataFilter = {
  page?: number
  project?: number | null
  from_date?: string
  to_date?: string
  sort?: 1 | 2 | null
  bank_account?: number | null
  is_imprest?: 'true' | 'false' | 'all' | ''
  account?: number | null
  account_category?:
    | 'asset'
    | 'liability'
    | 'equity'
    | 'revenue'
    | 'expense'
    | 'transfer'
    | 'cancel'
    | ''
  account_name?: string
  contract?: number | null
  search?: string
  limit?: number
}

export type ProAccountFilter = {
  category?: string
  direction?: string
  parent?: number | null
  is_category_only?: boolean | ''
  is_active?: boolean | ''
  is_payment?: boolean | ''
  requires_contract?: boolean | ''
  is_related_contractor?: boolean | ''
  search?: string
}

// ----- old types ----------------------------------------

export interface BalanceByAccount {
  bank_acc: string
  bank_num: string
  date_inc: number
  date_out: number
  inc_sum: number | null
  out_sum: number | null
}

export interface PaymentPaid {
  pk: number
  deal_date: string
  contract: ContractInPayment
  order_group: string
  type_color: string
  type_name: string
  serial_number: string
  contractor: string
  income: number
  installment_order: string
  bank_account: string
  trader: string
  note: string
}

interface ContractInPayment {
  pk: number
  order_group: {
    pk: number
    sort: '1' | '2'
    name: string
  }
  unit_type: {
    pk: number
    name: string
    color: string
    average_price: number
  }
  serial_number: string
  contractor: string
}

export interface ProCalculated {
  pk?: number
  project: number
  calculated: string
  creator?: { pk: number; username: string }
}
