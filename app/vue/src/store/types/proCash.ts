export interface ProjectAccountD2 {
  pk: number
  d1: string
  code: string
  name: string
  description: string
}

export interface ProjectAccountD3 {
  pk: number
  d2: number
  code: string
  is_related_contract: boolean
  name: string
  description: string
}

export interface ProBankAcc {
  pk: number | null
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

export interface BalanceByAccount {
  bank_acc: string
  bank_num: string
  date_inc: number
  date_out: number
  inc_sum: number | null
  out_sum: number | null
}

export interface ProSepItems {
  pk?: number | null
  project_account_d2: number | null
  project_account_d2_desc?: string
  project_account_d3: number | null
  project_account_d3_desc?: string
  separated?: number | null
  is_imprest?: boolean
  contract?: number | null
  installment_order?: number | null
  content: string
  trader: string
  income?: number | null
  outlay?: number | null
  evidence?: '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | ''
  evidence_desc?: string
  note: string
}

export interface ProjectCashBook extends ProSepItems {
  project: number | null
  sort: number | null
  sort_desc?: string
  is_separate?: boolean
  sepItems: Array<ProSepItems>
  rmCont?: boolean
  refund_contractor?: number | null
  bank_account: number | null
  bank_account_desc?: string
  deal_date: string
}

export type CashBookFilter = {
  project?: number | null
  page?: number
  from_date?: string
  to_date?: string
  order_group?: string
  unit_type?: string
  sort?: number | null
  account_d1?: number | null
  pro_acc_d2?: number | null
  pro_acc_d3?: number | null
  is_imprest?: '' | '0' | 'false'
  bank_account?: number | null
  pay_order?: string
  pay_account?: string
  contract?: number
  no_contract?: boolean
  no_install?: boolean
  ordering?: string
  search?: string
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
    order_group_name: string
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
