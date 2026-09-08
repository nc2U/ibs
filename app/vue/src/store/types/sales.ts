export interface SalesAgency {
  id: number
  project: number
  name: string
  is_direct_managed: boolean
  business_number: string
  ceo_name: string
  phone: string
  order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SalesTeam {
  id: number
  agency: number
  agency_name?: string
  parent: number | null
  parent_name?: string | null
  name: string
  order: number
  is_active: boolean
  members_count?: number
  created_at: string
}

export type SalesDuty = '1' | '2' | '3' | '4' | '5' // 1:상담사, 2:팀장, 3:본부장, 4:총괄본부장, 5:지원/기타
export type SalesPersonStatus = '1' | '2' | '3' // 1:재직, 2:휴직, 3:해촉
export type TaxType = '1' | '2' | '3' | '4' // 1:3.3%사업소득, 2:근로소득, 3:사업자, 4:기타
export type SalesDocType = '1' | '2' | '3' | '4' | '5' | '9' // 1:등본, 2:통장, 3:신분증, 4:위촉계약서, 5:각종서약서, 9:기타

export interface SalesPersonDocument {
  id: number
  sales_person: number
  sales_person_name?: string
  doc_type: SalesDocType
  doc_type_display?: string
  title: string
  file: string
  file_name: string
  file_type: string
  file_size: number | null
  is_verified: boolean
  verified_at: string | null
  verified_by: number | null
  verified_by_name?: string | null
  uploader: number | null
  uploader_name?: string | null
  created_at: string
  updated_at: string
}

export interface SalesPerson {
  id: number
  team: number
  team_name?: string
  agency_name?: string
  user: number | null
  name: string
  duty: SalesDuty
  duty_display?: string
  status: SalesPersonStatus
  status_display?: string
  phone: string
  id_number: string
  tax_type: TaxType
  tax_type_display?: string
  bank_name: string
  account_number: string
  account_holder: string
  join_date: string | null
  quit_date: string | null
  notes: string
  documents_count?: number
  documents?: SalesPersonDocument[]
  created_at: string
  updated_at: string
}

export interface CommissionPolicy {
  id: number
  project: number
  order_group: number | null
  order_group_name?: string
  unit_type: number | null
  unit_type_name?: string
  name: string
  agent_fee: number
  leader_fee: number
  director_fee: number
  agency_fee: number
  pay_condition: '1' | '2' | '3' | '4'
  pay_condition_display?: string
  start_date: string
  end_date: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ContractSalesAgent {
  id: number
  contract: number
  contract_serial?: string
  contractor_name?: string
  order_group_name?: string
  unit_type_name?: string
  unit_info?: string
  agency?: number | null
  agency_name?: string
  is_direct_managed?: boolean
  sales_person: number | null
  sales_person_name?: string
  team: number | null
  team_name?: string
  policy: number | null
  policy_name?: string
  contract_date: string | null
  mgm_name: string
  mgm_phone: string
  mgm_fee: number
  note: string
  is_settlement_approved: boolean
  approval_note?: string
  approved_by?: number | null
  approved_by_name?: string | null
  approved_at?: string | null
  is_settled?: boolean
  settled_period_title?: string | null
  created_at: string
  updated_at: string
}

export interface PayoutContractDetail {
  id: number
  payout: number
  contract: number
  contract_serial?: string
  contractor_name?: string
  role_type: 'agent' | 'leader' | 'director' | 'mgm'
  role_type_display?: string
  unit_fee: number
}

export interface CommissionPayout {
  id: number
  period: number
  sales_person: number
  sales_person_name?: string
  duty_display?: string
  team_name?: string
  base_pay: number
  contract_count: number
  commission_amount: number
  bonus_amount: number
  deduction_amount: number
  gross_amount: number
  income_tax: number
  local_income_tax: number
  total_tax: number
  net_amount: number
  pay_status: '1' | '2' | '3' | '4' // 1:대기, 2:승인, 3:지급완료, 4:지급보류
  pay_status_display?: string
  paid_date: string | null
  bank_name: string
  account_number: string
  account_holder: string
  note: string
  contract_details?: PayoutContractDetail[]
  created_at: string
  updated_at: string
}

export interface SettlementPeriod {
  id: number
  project: number
  title: string
  start_date: string
  end_date: string
  payout_date: string | null
  status: '1' | '2' | '3' // 1:작성중, 2:확정, 3:지급완료
  status_display?: string
  total_contracts: number
  total_gross_amount: number
  total_tax_amount: number
  total_net_amount: number
  agency_fee_total?: number
  billing_supply_price?: number
  billing_vat?: number
  billing_total_amount?: number
  payout_count?: number
  agency_payout_count?: number
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface AgencyPayoutContractDetail {
  id: number
  payout: number
  contract: number
  contract_serial?: string
  contractor_name?: string
  unit_fee: number
}

export interface AgencyPayout {
  id: number
  period: number
  agency: number
  agency_name?: string
  is_direct_managed?: boolean
  contract_count: number
  agency_fee_sum: number
  vat_amount: number
  total_amount: number
  pay_status: '1' | '2' | '3' | '4'
  pay_status_display?: string
  paid_date: string | null
  business_number: string
  bank_name: string
  account_number: string
  account_holder: string
  note: string
  contract_details?: AgencyPayoutContractDetail[]
  created_at: string
  updated_at: string
}

export interface CommissionClawback {
  id: number
  contract: number
  contract_serial?: string
  sales_person: number
  sales_person_name?: string
  amount: number
  reason: string
  is_settled: boolean
  settled_payout: number | null
  created_at: string
}
