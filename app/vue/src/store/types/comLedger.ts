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

export interface CashBook {
  pk: number | null
  company: number | null
  sort: number | null
  sort_desc?: string
  account_d1: number | null
  account_d1_desc?: string
  account_d2: number | null
  account_d2_desc?: string
  account_d3: number | null
  account_d3_desc?: string
  project: number | null
  project_desc?: string | null
  is_return: boolean
  is_separate: boolean
  separated: number | null
  sepItems?: SepItems[]
  has_children?: boolean
  is_balanced?: boolean
  balance_info?: {
    parent_income: number
    parent_outlay: number
    children_income: number
    children_outlay: number
  }
  content: string
  trader: string
  bank_account: number | null
  bank_account_desc?: string
  income?: number | null
  outlay?: number | null
  evidence: '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | ''
  evidence_desc?: string
  note: string
  deal_date: string
}

export interface SepItems {
  pk: number | null
  account_d1: number | null
  account_d2: number | null
  account_d3: number | null
  project: number | null
  is_return: boolean
  separated?: number | null
  content: string
  trader: string
  income?: number | null
  outlay?: number | null
  evidence: '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | ''
  note: string
}

export interface ComCalculated {
  pk?: number
  company: number
  calculated: string
  creator?: { pk: number; username: string }
}
