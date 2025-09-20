export interface PayOrder {
  pk?: number | null
  project?: number
  __str__?: string
  type_sort?: '1' | '2' | '3' | '4' | '5' | '6' | ''
  pay_sort?: '1' | '2' | '3' | '4' | '5' | '6' | '7' | ''
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
  down_pay: number | null
  biz_agency_fee: number | null
  is_included_baf: false
  middle_pay: number | null
  remain_pay: number | null
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
