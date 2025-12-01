export interface BankCode {
  pk: number
  code: string
  name: string
}

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

export interface BalanceByAccount {
  bank_acc: string
  bank_num: string
  date_inc: number
  date_out: number
  inc_sum: number | null
  out_sum: number | null
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
  sort_name: string
  content: string
  note: string
  creator: number
  creator_name: string
  created_at: string
  updated_at: string
  is_balanced: boolean
  accounting_entries: AccountingEntry[]
}

export interface AccountingEntry {
  pk?: number
  transaction_id: string
  company: number
  sort: number
  sort_name: string
  account_d1: number | null
  account_d1_name: string
  account_d2: number | null
  account_d2_name: string
  account_d3: number | null
  account_d3_name: string
  amount: number
  trader: string
  evidence_type: null | '0' | '1' | '2' | '3' | '4' | '5' | '6'
  evidence_type_display:
    | null
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

export interface ComCalculated {
  pk?: number
  company: number
  calculated: string
  creator?: { pk: number; username: string }
}
