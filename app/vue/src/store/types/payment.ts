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

export interface DownPay {
  pk: number
  project: number
  order_group: number
  unit_type: number
  payment_amount: number
}

export interface PaySumByType {
  order_group: number
  unit_type: number
  paid_sum: number
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

export interface ContractNum {
  unit_type: number
  num_cont: number
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

export interface PaymentPerInstallmentPayload {
  pk?: number
  sales_price: number
  pay_order: number | null
  amount: number | null
}

export interface AllPayment {
  pk: number
  deal_date: string
  contract: {
    pk: number
    order_group: {
      pk: number
      sort: string
      name: string
    }
    unit_type: {
      pk: number
      name: string
      color: string
      average_price: number | null
    }
    serial_number: string
    contractor: string
  }
  income: number
  installment_order: {
    pk: number
    pay_sort: string
    pay_time: number
    pay_name: string
    __str__: string
  }
  bank_account: {
    pk: number
    alias_name: string
  }
  trader: string
  note: string
}
