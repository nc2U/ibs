export interface PayOrder {
  pk?: number | null
  project?: number
  __str__?: string
  type_sort?: '1' | '2' | '3' | '4' | '5' | '6' | ''
  pay_sort?: '1' | '2' | '3' | '4' | '5' | '6' | '7' | ''
  calculation_method?: 'auto' | 'ratio' | 'downpayment'
  is_except_price?: boolean
  pay_code?: number | null
  pay_time?: number | null
  pay_name?: string
  alias_name?: string
  pay_amt?: number | null
  pay_ratio?: number | null
  pay_due_date?: string | null
  days_since_prev?: number | null
  is_prep_discount?: boolean
  prep_discount_ratio?: number | null
  prep_ref_date?: string | null
  is_late_penalty?: boolean
  late_penalty_ratio?: number | null
  extra_due_date?: string | null
}

export interface Price {
  pk: number
  project: number
  order_group: number
  unit_type: number
  price_setting: '1' | '2' | '3'
  unit_floor_type: number
  price_build: number
  price_land: number
  price_tax: number
  price: number
}

export interface PriceFilter {
  project?: number | null
  order_group?: number | null
  unit_type?: number | null
}

export interface DownPay {
  pk: number
  project: number
  order_group: number
  unit_type: number
  payment_amount: number
}

export interface DownPayFilter {
  project: number
  order_group?: number
  unit_type?: number
}

export interface PaymentSummaryComponent {
  unit_type_id: number
  unit_type_name: string
  unit_type_color: string
  total_budget: number
  total_contract_amount: number
  total_paid_amount: number
  unpaid_amount: number
  unsold_amount: number
}

export interface PayOrderCollection {
  collected_amount: number
  discount_amount: number
  overdue_fee: number
  actual_collected: number
  collection_rate: number
}

export interface PayOrderDuePeriod {
  contract_amount: number
  unpaid_amount: number
  unpaid_rate: number
  overdue_fee: number
  subtotal: number
}

export interface OverallSummaryPayOrder extends PayOrder {
  contract_amount: number
  non_contract_amount: number
  contract_rate: number
  collection: PayOrderCollection
  due_period: PayOrderDuePeriod
  not_due_unpaid: number
  total_unpaid: number
  total_unpaid_rate: number
}

export interface OverallSummaryAggregate {
  conts_num: number
  non_conts_num: number
  total_units: number
  contract_rate: number
}

export interface OverallSummary {
  pay_orders: OverallSummaryPayOrder[]
  aggregate: OverallSummaryAggregate
}

export interface PaymentStatusByUnitType {
  order_group_id: number
  order_group_name: string
  unit_type_id: number
  unit_type_name: string
  unit_type_color: string
  total_sales_amount: number
  planned_units: number
  contract_units: number
  contract_amount: number
  paid_amount: number
  unpaid_amount: number
  non_contract_amount: number
  total_budget: number
}

export interface PaymentPerInstallment {
  pk: number
  sales_price: number
  sales_price_info: {
    project: string
    order_group: string
    unit_type: string
    unit_floor_type: string
    price: number
  }
  pay_order: number | null
  pay_order_info: {
    pay_sort: string
    pay_name: string
    pay_code: number
    pay_time: number
  }
  amount: number | null
}

export interface PaymentPerInstallmentFilter {
  sales_price?: number | null
  sales_price__project?: number | null
  sales_price__order_group?: number | null
  sales_price__unit_type?: number | null
  pay_order?: number | null
}

export interface PaymentPerInstallmentPayload {
  pk?: number
  sales_price: number
  pay_order: number | null
  amount: number | null
}

export interface ContractInPayment {
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

interface BasePayment {
  pk: number
  deal_date: string
  contract: ContractInPayment
  installment_order: {
    pk: number
    pay_sort: string
    pay_name: string
    pay_time: number
    __str__: string
  }
  bank_account: {
    pk: number
    alias_name: string
  }
  trader: string
  note: string
}

export interface AllPayment extends BasePayment {
  income: number
}

export interface OriginPayment extends BasePayment {
  amount: number
  bank_transaction_id: number | null // 수정/삭제용 은행거래 PK
  accounting_entry: number | any
}

export interface PaymentList {
  pk: number
  trans_id: number
  entry_id: number
  deal_date: string
  contract: ContractInPayment
  order_group: string
  type_color: string
  type_name: string
  serial_number: string
  contractor: string
  amount: number
  installment_order: string
  bank_account: string
  trader: string
  note: string
}

export type ContPayFilter = {
  project?: number | null
  page?: number
  from_date?: string
  to_date?: string
  order_group?: string
  unit_type?: string
  pay_order?: string
  pay_account?: number | null | ''
  contract?: number
  no_contract?: boolean
  no_install?: boolean
  ordering?: string
  search?: string
}

// ============================================
// ContractPayment CRUD Types (Ledger 기반)
// ============================================

/**
 * 회계 분개 입력 데이터
 * ProjectAccountingEntryInputSerializer와 매핑
 */
export interface PaymentAccEntryInput {
  pk?: number | null // 기존 분개 수정 시 사용
  account: number | null // 계정 과목 ID, 초기화용 null
  amount: number | null // 금액, 초기화용 null
  trader?: string // 거래처
  contract?: number | null // 계약 ID (계약 결제인 경우)
  installment_order?: number | null // 납부 회차 ID
}

/**
 * 복합 거래 생성/수정 페이로드
 * ProjectCompositeTransactionSerializer와 매핑
 */
export interface ContractPaymentPayload {
  // Bank Transaction 필드
  project: number | null // 초기화용 null
  bank_account: number | null // 초기화용 null
  deal_date: string // YYYY-MM-DD
  amount: number | null // 초기화용 null
  sort: number // 1=입금, 2=출금
  content: string // 적요
  note?: string // 비고

  // Accounting Entries (배열)
  accounting_entries: PaymentAccEntryInput[]
}

/**
 * 복합 거래 응답 데이터
 */
export interface ContractPaymentResponse {
  bank_transaction: {
    pk: number
    transaction_id: string
    project: number
    bank_account: number
    deal_date: string
    amount: number
    sort: number
    content: string
    note: string
    created_at: string
    updated_at: string
  }
  accounting_entries: Array<{
    pk: number
    transaction_id: string
    account: number
    amount: number
    trader: string
    evidence_type: string | null
    contract: number | null
    contractor: number | null
    installment_order: number | null
    created_at: string
    updated_at: string
  }>
  contract_payments?: Array<{
    pk: number
    contract: number
    installment_order: number | null
  }>
}
