export interface SimpleCont {
  pk: number
  project: number
  order_group: number
  unit_type: number
  serial_number: string
  activation: boolean
}

export interface ContractFile {
  pk: number
  file: string
  file_name: string
  file_size: number
  created: string
  creator: { pk: number; username: string }
  cngFile?: File | null
  del?: boolean
  edit?: boolean
}

interface ContractorInContract {
  pk: number
  name: string
  birth_date: string | null
  gender: 'M' | 'F' | ''
  qualification: '1' | '2' | '3' | '4'
  qualifi_display: '일반분양' | '미인가' | '인가' | '부적격'
  contractoraddress: AddressInContractor
  contractorcontact: ContractorContact
  status: '1' | '2' | '3' | '4' | '5'
  reservation_date: string | null
  contract_date: string | null
  is_active: boolean
  note: string
}

export interface Contract {
  pk: number
  project: number
  order_group_sort: '1' | '2' // '조합모집' | '일반분양'
  order_group: number
  unit_type: number
  unit_type_desc: UnitType
  serial_number: string
  activation: boolean
  is_sup_cont: boolean
  sup_cont_date: string | null
  key_unit: KeyUnit | null
  contractprice: ContPrice | null
  contractor: ContractorInContract | null
  payments: Payment[]
  total_paid: number
  last_paid_order: InstallmentOrder | null
  order_group_desc: {
    pk: number
    sort: string
    name: string
  }
  contract_files: ContractFile[]
}

export interface KeyUnit {
  pk: number
  unit_code: string
  houseunit: HouseUnit | null
}

export interface HouseUnit {
  pk: number
  __str__: string
  floor_type: number
}

export interface ContPrice {
  pk: number
  price: number
  price_build: number | null
  price_land: number | null
  price_tax: number | null
}

export interface Contractor {
  pk: number
  contract: number
  name: string
  __str__: string
  birth_date: string
  gender: 'M' | 'F' | ''
  qualification: '1' | '2' | '3' | '4' | ''
  qualifi_display: '일반분양' | '미인가' | '인가' | '부적격'
  status: '1' | '2' | '3' | '4' | '5' | ''
  reservation_date: string | null
  contract_date: string | null
  is_active: boolean
  note: string
  succession: Succession | null
  contractorrelease: number | null
}

export interface AddressInContractor {
  pk: number
  id_zipcode: string
  id_address1: string
  id_address2: string
  id_address3: string
  dm_zipcode: string
  dm_address1: string
  dm_address2: string
  dm_address3: string
}

export interface ContractorAddress {
  pk: number
  id_zipcode: string
  id_address1: string
  id_address2: string
  id_address3: string
  dm_zipcode: string
  dm_address1: string
  dm_address2: string
  dm_address3: string
  is_current: boolean
}

export interface ContractorContact {
  pk: number
  cell_phone: string
  home_phone: string
  other_phone: string
  email: string
}

export interface Payment {
  pk: number
  deal_date: string
  income: number
  bank_account: number
  trader: string
  installment_order: InstallmentOrder
}

interface InstallmentOrder {
  pk: number
  pay_sort: string
  pay_time: number
  pay_name: string
  __str__: string
}

export interface UnitType {
  pk: number
  name: string
  color: string
  average_price: number
}

export interface OrderGroup {
  pk: number
  project: number
  order_number: number
  sort: '1' | '2' // '조합모집' | '일반분양'
  sort_desc: string
  name: string
  is_default_for_uncontracted: boolean
}

export interface SalesPrice {
  pk: number
  project: number
  order_group: number
  unit_type: number
  unit_floor_type: number
  price_build: number | null
  price_land: number | null
  price_tax: number | null
  price: number
}

export interface DownPayment {
  pk: number
  project: number
  order_group: number
  unit_type: number
  number_payments: number
  payment_amount: number
}

interface SimpleSuccession {
  pk: number
  is_approval: boolean
}

export interface SubsSummary {
  order_group: number
  unit_type: number
  conts_num: number
  price_sum: number
}

export type ContSummary = SubsSummary

export interface Succession {
  pk?: number
  contract: {
    pk: number
    serial_number: string
  }
  seller: {
    pk: number
    name: string
  }
  buyer: Buyer
  apply_date: string
  trading_date: string
  is_approval: boolean
  approval_date: string | null
  note: string
}

export interface Buyer {
  pk?: number
  name: string
  birth_date: string
  gender: 'M' | 'F'
  contractoraddress: {
    pk?: number
    id_zipcode: string
    id_address1: string
    id_address2: string
    id_address3: string
    dm_zipcode: string
    dm_address1: string
    dm_address2: string
    dm_address3: string
  }
  contractorcontact: {
    pk?: number
    cell_phone: string
    home_phone: string
    other_phone: string
    email: string
  }
}

export interface BuyerForm {
  name: string
  birth_date: string
  gender: 'M' | 'F'
  id_zipcode: string
  id_address1: string
  id_address2: string
  id_address3: string
  dm_zipcode: string
  dm_address1: string
  dm_address2: string
  dm_address3: string
  cell_phone: string
  home_phone: string
  other_phone: string
  email: string
}

export interface ContractRelease {
  pk: number
  project: number
  contractor: number
  __str__?: string
  status: string
  refund_amount: number
  refund_account_bank: string
  refund_account_number: string
  refund_account_depositor: string
  request_date: string
  completion_date: string
  note: string
}

export interface ContractPaymentPlanItem {
  installment_order: {
    pk: number
    pay_sort: '1' | '2' | '3' | '4' | '5' | '6' | '7'
    pay_code: number
    pay_time: number
    pay_name: string
    alias_name: string | null
    pay_amt: number | null
    pay_ratio: number | null
    pay_due_date: string | null
    days_since_prev: number | null
    is_except_price: boolean
  }
  amount: number
  source: 'calculated' | 'payment_per_installment'
}

export type ContractPaymentPlan = ContractPaymentPlanItem[]

// ContractPrice with cached payment plan types
export interface ContractPriceWithPaymentPlan {
  pk: number
  price: number
  price_build: number | null
  price_land: number | null
  price_tax: number | null
  payment_amounts: Record<string, number> // { "1": 10000000, "2": 30000000, ... }
  calculated: string
  is_cache_valid: boolean
  payment_plan: ContractPricePaymentPlanItem[]
}

export interface ContractPricePaymentPlanItem {
  installment_order: {
    pk: number
    pay_sort: string
    pay_name: string
    pay_time: number
  }
  amount: number
  source: 'cached'
}
