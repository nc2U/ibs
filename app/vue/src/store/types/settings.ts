export interface Company {
  pk: number | null
  name: string
  ceo: string
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
  seal_type: 'CORP_SEAL' | 'USAGE_SEAL' | 'DEPT_SEAL' | 'SIGN' | 'OMIT'
  seal_type_desc?: string
  name: string
  seal_image: string | null
  manager?: string
  is_active: boolean
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
