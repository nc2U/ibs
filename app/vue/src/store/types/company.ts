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
  code: string
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
  'inside' | 'outside' | 'non_standing_director' | 'auditor' | 'unregistered' | 'advisor'

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

export type EvaluationPeriod = 'yearly' | '1H' | '2H'
export type EvaluationGrade = 'S' | 'A' | 'B' | 'C' | 'D'
export type PromotionStatus = 'candidate' | 'recommended' | 'approved' | 'rejected' | 'hold'

export interface PromotionPolicy {
  pk?: number
  company?: string
  current_grade: number
  current_grade_code?: string
  target_grade: number
  target_grade_code?: string
  min_years: number
  min_avg_grade_point?: number | null
  required_eval_grade?: string
  required_credentials?: string
  disqualification_conditions?: string
  description?: string
  is_active: boolean
}

export type PromotionPolicyFilter = {
  page?: number
  com?: number
  current_grade?: number | string
  target_grade?: number | string
  is_active?: boolean | string
  q?: string
}

export interface StaffEvaluation {
  pk?: number
  company?: string
  staff: number
  staff_name?: string
  eval_year: number
  eval_period: EvaluationPeriod
  eval_period_desc?: string
  grade: EvaluationGrade
  score?: number | null
  achievement_summary?: string
  evaluator?: number | null
  evaluator_name?: string | null
  reviewer?: number | null
  reviewer_name?: string | null
  notes?: string
}

export interface PromotionCandidate {
  pk?: number
  company?: string
  policy: number
  staff: number
  staff_name?: string
  current_grade_code?: string
  target_grade_code?: string
  eval_year: number
  tenure_years: number
  avg_eval_score?: number | null
  status: PromotionStatus
  status_desc?: string
  committee_review?: string
  promoted_date?: string | null
}

export type PromotionCandidateFilter = {
  page?: number
  com?: number
  eval_year?: number | string
  status?: string
  policy?: number | string
  staff?: number | string
  q?: string
}

export type OrderType =
  | '10' // 채용/신규입사
  | '20' // 승진/승급
  | '30' // 부서이동(전보)
  | '40' // 보직임면/겸직
  | '50' // 휴직
  | '51' // 복직
  | '60' // 파견/전적
  | '70' // 포상/표창
  | '80' // 징계/문책
  | '90' // 퇴사/면직

export interface PersonnelOrder {
  id?: number
  pk?: number
  company?: string
  company_name?: string
  staff: number
  staff_name?: string
  order_type: OrderType
  order_type_desc?: string
  order_date: string
  effective_end_date?: string | null
  order_no?: string
  prev_department?: number | null
  prev_department_name?: string | null
  prev_grade?: number | null
  prev_grade_code?: string | null
  prev_position?: number | null
  prev_position_name?: string | null
  prev_duty?: number | null
  prev_duty_name?: string | null
  new_department?: number | null
  new_department_name?: string | null
  new_grade?: number | null
  new_grade_code?: string | null
  new_position?: number | null
  new_position_name?: string | null
  new_duty?: number | null
  new_duty_name?: string | null
  description?: string
  is_processed: boolean
}

export type PersonnelOrderFilter = {
  page?: number
  com?: number
  staff?: number | string
  order_type?: string
  department?: number | string
  is_processed?: boolean | string
  q?: string
}

export type ComFilter = {
  page?: number
  com?: number
  q?: string
}

export type ExecutiveFilter = {
  page?: number
  com?: number
  rank?: number | string
  director_type?: string
  is_registered?: boolean | string
  is_standing?: boolean | string
  represent_type?: string
  q?: string
}

export type StaffEvaluationFilter = {
  page?: number
  com?: number
  eval_year?: number | string
  eval_period?: string
  grade?: string
  staff?: number | string
  q?: string
}

export interface StaffCareer {
  id?: number
  pk?: number
  company?: string
  staff: number
  staff_name?: string
  company_name: string
  department_name?: string
  position_title?: string
  assigned_tasks?: string
  start_date: string
  end_date?: string | null
  recognized_ratio: number
  note?: string
}

export interface StaffCertificate {
  id?: number
  pk?: number
  company?: string
  staff: number
  staff_name?: string
  name: string
  grade?: string
  cert_number?: string
  issuer?: string
  acquired_date: string
  expire_date?: string | null
  has_allowance: boolean
  note?: string
}

export interface StaffRewardPunishment {
  id?: number
  pk?: number
  company?: string
  staff: number
  staff_name?: string
  sort: 'reward' | 'punish'
  sort_desc?: string
  type_name: string
  action_date: string
  expire_date?: string | null
  reason: string
  organization?: string
  note?: string
}

export type StaffRecordFilter = {
  page?: number
  com?: number
  staff?: number | string
  sort?: string
  q?: string
}

export interface StaffLeaveQuota {
  id?: number
  pk?: number
  company?: string
  staff: number
  staff_name?: string
  year: number
  granted_days: number
  carry_over_days: number
  reward_days: number
  total_granted_days?: number
  used_days?: number
  remaining_days?: number
  valid_start: string
  valid_end: string
  note?: string
}

export type StaffLeaveQuotaFilter = {
  page?: number
  com?: number
  staff?: number | string
  year?: number | string
  q?: string
}

export type LeaveType =
  | 'annual'
  | 'half_am'
  | 'half_pm'
  | 'quarter'
  | 'official'
  | 'sick'
  | 'condolence'
  | 'reward'
  | 'substitute'
  | 'other'

export interface StaffLeaveUsage {
  id?: number
  pk?: number
  company?: string
  staff: number
  staff_name?: string
  leave_type: LeaveType
  leave_type_desc?: string
  start_date: string
  end_date: string
  deduction_days: number
  approval_doc?: number | null
  reason?: string
  is_cancelled: boolean
  created?: string
}

export type StaffLeaveUsageFilter = {
  page?: number
  com?: number
  staff?: number | string
  leave_type?: string
  start_date?: string
  end_date?: string
  is_cancelled?: string | boolean
  q?: string
}
