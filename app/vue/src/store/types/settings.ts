export interface Company {
  pk: number | null
  name: string
  en_name?: string
  short_name?: string
  ceo: string
  representative_name?: string
  tax_number: string
  org_number: string
  business_cond: string
  business_even: string
  es_date: string
  op_date: string
  zipcode: string
  address1: string
  address2: string
  address3: string
  phone?: string
  fax?: string
  email?: string
  departments?: Department[]
  positions?: Positions[]
  com_issue_project?: number | null
  is_default?: boolean
}

export interface Logo {
  pk: number
  company: number
  generic_logo: string
  dark_logo: string
  simple_logo: string
}

export interface CompanySeal {
  pk: number
  company: number
  seal_type: 'CORP_SEAL' | 'USAGE_SEAL' | 'DEPT_SEAL' | 'OMIT'
  seal_type_desc?: string
  name: string
  purpose?: string
  seal_image: string | null
  custody_type?: 'internal' | 'external'
  custody_type_desc?: string
  custodian?: string
  internal_manager?: number | null
  internal_manager_name?: string | null
  valid_from?: string | null
  valid_until?: string | null
  manager?: string
  final_approval_duty?: number | null
  final_approval_duty_name?: string | null
  final_dept_level?: number | null
  is_active: boolean
  description?: string
  created?: string
}

interface Department {
  name: string
  task: string
}

interface Positions {
  pk: number
  rank: string
  title: string
  description: string
}
