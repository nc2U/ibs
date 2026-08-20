export interface StaffAssignment {
  id?: number
  pk?: number
  department: number
  department_name?: string
  duty?: number | null
  duty_name?: string | null
  is_primary: boolean
  assigned_tasks?: string
}

export interface Staff {
  pk?: number
  company?: string
  sort?: '1' | '2'
  sort_desc?: '임원' | '직원'
  name: string
  id_number: string
  personal_phone: string
  email: string
  department: string
  grade: string
  position: string
  duty: string
  date_join: string | null
  date_leave: string | null
  status: '1' | '2' | '3' | '4'
  status_desc?: '근무 중' | '휴직 중' | '퇴직신청' | '퇴사처리'
  user: number | null
  assignments?: StaffAssignment[]
  executive?: Executive | null
  is_hq_financial_officer?: boolean
  is_hq_hr_officer?: boolean
}

export type StaffFilter = {
  page?: number
  com?: number
  sort?: '' | '1' | '2'
  dep?: string
  gra?: string
  pos?: string
  dut?: string
  sts?: '1' | '2' | '3' | '4'
  q?: string
}

export interface Department {
  pk?: number
  company?: string
  upper_depart: number | null
  level: number
  name: string
  task: string
  manager?: number | null
  manager_name?: string | null
  staffs?: []
}

export type DepFilter = {
  page?: number
  com?: number
  upp?: string
  q?: string
}

export interface Grade {
  pk?: number
  company?: string
  code: string
  role: string
  min_promotion_years: number | null
  promotion_criteria: string
  positions?: number[]
}

export interface Position {
  pk?: number
  company?: string
  name: string
  grades: number[]
  desc: string
}

export interface Duty {
  pk?: number
  company?: string
  name: string
  desc: string
}

export interface ExecutiveRank {
  pk?: number
  company?: string
  code: string
  name: string
  rank_order: number
  role_desc: string
}

export type DirectorType =
  | 'inside'
  | 'outside'
  | 'non_standing_director'
  | 'auditor'
  | 'unregistered'
  | 'advisor'

export type RepresentType = 'none' | 'sole' | 'joint' | 'each'

export interface Executive {
  pk?: number
  company?: string
  staff: number
  staff_name?: string
  rank?: number | null
  rank_name?: string | null
  director_type: DirectorType
  director_type_desc?: string
  is_registered: boolean
  is_standing: boolean
  represent_type: RepresentType
  represent_type_desc?: string
  term_start?: string | null
  term_end?: string | null
  appointed_date?: string | null
  note?: string
}

export type ComFilter = {
  page?: number
  com?: number
  q?: string
}
