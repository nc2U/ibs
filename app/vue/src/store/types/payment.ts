export interface Price {
  pk: number
  project: number
  order_group: number
  unit_type: number
  unit_floor_type: number
  price_build: number
  price_land: number
  price_tax: number
  price: number
}

export interface PayOrder {
  pk?: number | null
  project?: number
  __str__?: string
  pay_sort?: string
  pay_code?: number
  pay_time?: number
  pay_name?: string
  alias_name?: string
  is_pm_cost?: boolean
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

export interface AllPayment {
  pk: number
  deal_date: string
  contract: {
    pk: number
    order_group: {
      pk: number
      sort: string
      order_group_name: string
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
