export interface SimpleUser {
  id: number
  username: string
  full_name: string
}

export interface RouteTemplate {
  id: number
  step_order: number
  role_label: string
  approvers: SimpleUser[]
  condition: 'AND' | 'OR'
}

export interface DocumentType {
  id: number
  name: string
  code: string
  description: string
  form_schema: FormField[]
  is_active: boolean
  route_templates: RouteTemplate[]
}

export interface FormField {
  key: string
  label: string
  type: 'text' | 'textarea' | 'number' | 'date' | 'select'
  required: boolean
  options?: string[]
}

export type DocumentStatus = 'draft' | 'pending' | 'approved' | 'rejected' | 'cancelled'
export type ApprovalCondition = 'AND' | 'OR'
export type ApprovalActionType = 'approved' | 'rejected' | 'commented'
export type StepStatus = 'pending' | 'approved' | 'rejected' | 'skipped'

export interface ApprovalActionRecord {
  id: number
  approver: SimpleUser
  action: ApprovalActionType
  comment: string
  acted_at: string
}

export interface ApprovalStep {
  id: number
  step_order: number
  role_label: string
  approvers: SimpleUser[]
  condition: ApprovalCondition
  status: StepStatus
  actions: ApprovalActionRecord[]
}

export interface ApprovalDocument {
  id: number
  doc_number: string
  title: string
  doc_type: number
  doc_type_detail?: DocumentType
  doc_type_name?: string
  content: Record<string, unknown>
  attachment?: string | null
  drafter: SimpleUser
  workspace?: number | null
  status: DocumentStatus
  current_step: number
  content_hash: string
  pdf_url: string | null
  created_at: string
  submitted_at: string | null
  completed_at: string | null
  steps?: ApprovalStep[]
}

export interface PatchApprovalDocument {
  title?: string
  doc_type?: number
  content?: Record<string, unknown>
  workspace?: number | null
}

export interface ApprovalActPayload {
  action: ApprovalActionType
  comment?: string
}
