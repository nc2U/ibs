import { defineAsyncComponent, type Component } from 'vue'

export { default as DynamicSchemaForm } from './DynamicSchemaForm.vue'
export { default as LeaveApplicationForm } from './LeaveApplicationForm.vue'
export { default as ExpenseReportForm } from './ExpenseReportForm.vue'
export { default as PurchaseOrderForm } from './PurchaseOrderForm.vue'
export { default as OfficialLetterForm } from './OfficialLetterForm.vue'
export { default as GeneralProposalForm } from './GeneralProposalForm.vue'
export { default as BusinessTripForm } from './BusinessTripForm.vue'
export { default as OvertimeWorkForm } from './OvertimeWorkForm.vue'
export { default as HrAppointmentForm } from './HrAppointmentForm.vue'
export { default as HrRequestForm } from './HrRequestForm.vue'
export { default as ExpenseSettlementForm } from './ExpenseSettlementForm.vue'
export { default as AdvancePaymentForm } from './AdvancePaymentForm.vue'
export { default as ContractProposalForm } from './ContractProposalForm.vue'
export { default as ContractChangeForm } from './ContractChangeForm.vue'
export { default as LegalReviewForm } from './LegalReviewForm.vue'
export { default as BusinessReviewForm } from './BusinessReviewForm.vue'
export { default as BusinessApprovalForm } from './BusinessApprovalForm.vue'
export { default as ProjectDecisionForm } from './ProjectDecisionForm.vue'

/**
 * STATIC 폼 컴포넌트 레지스트리
 * DocumentType.form_template_key 와 매칭되는 Vue 컴포넌트 목록
 */
export const STATIC_FORM_REGISTRY: Record<string, Component> = {
  LEAVE: defineAsyncComponent(() => import('./LeaveApplicationForm.vue')),
  LEAVE_APPLICATION: defineAsyncComponent(() => import('./LeaveApplicationForm.vue')),
  EXPENSE: defineAsyncComponent(() => import('./ExpenseReportForm.vue')),
  EXPENSE_REPORT: defineAsyncComponent(() => import('./ExpenseReportForm.vue')),
  PURCHASE: defineAsyncComponent(() => import('./PurchaseOrderForm.vue')),
  PURCHASE_ORDER: defineAsyncComponent(() => import('./PurchaseOrderForm.vue')),
  OFFICIAL_LETTER: defineAsyncComponent(() => import('./OfficialLetterForm.vue')),
  GENERAL: defineAsyncComponent(() => import('./GeneralProposalForm.vue')),
  BIZ_APPROVAL: defineAsyncComponent(() => import('./GeneralProposalForm.vue')),
  BUSINESS_TRIP: defineAsyncComponent(() => import('./BusinessTripForm.vue')),
  TRIP: defineAsyncComponent(() => import('./BusinessTripForm.vue')),
  OVERTIME: defineAsyncComponent(() => import('./OvertimeWorkForm.vue')),
  OVERTIME_WORK: defineAsyncComponent(() => import('./OvertimeWorkForm.vue')),
  HR_APPOINTMENT: defineAsyncComponent(() => import('./HrAppointmentForm.vue')),
  APPOINTMENT: defineAsyncComponent(() => import('./HrAppointmentForm.vue')),
  HR_REQUEST: defineAsyncComponent(() => import('./HrRequestForm.vue')),
  CERT_REQUEST: defineAsyncComponent(() => import('./HrRequestForm.vue')),
  EXPENSE_SETTLEMENT: defineAsyncComponent(() => import('./ExpenseSettlementForm.vue')),
  SETTLEMENT: defineAsyncComponent(() => import('./ExpenseSettlementForm.vue')),
  ADVANCE: defineAsyncComponent(() => import('./AdvancePaymentForm.vue')),
  ADVANCE_PAY: defineAsyncComponent(() => import('./AdvancePaymentForm.vue')),
  ADVANCE_REQUEST: defineAsyncComponent(() => import('./AdvancePaymentForm.vue')),
  CONTRACT: defineAsyncComponent(() => import('./ContractProposalForm.vue')),
  CONTRACT_APPROVAL: defineAsyncComponent(() => import('./ContractProposalForm.vue')),
  CONTRACT_PROPOSAL: defineAsyncComponent(() => import('./ContractProposalForm.vue')),
  CONTRACT_CHANGE: defineAsyncComponent(() => import('./ContractChangeForm.vue')),
  CONTRACT_TERMINATION: defineAsyncComponent(() => import('./ContractChangeForm.vue')),
  CONTRACT_AMENDMENT: defineAsyncComponent(() => import('./ContractChangeForm.vue')),
  LEGAL_REVIEW: defineAsyncComponent(() => import('./LegalReviewForm.vue')),
  LEGAL_CONSULTATION: defineAsyncComponent(() => import('./LegalReviewForm.vue')),
  LEGAL_ADVICE: defineAsyncComponent(() => import('./LegalReviewForm.vue')),
  BUSINESS_REVIEW: defineAsyncComponent(() => import('./BusinessReviewForm.vue')),
  PROJECT_FEASIBILITY: defineAsyncComponent(() => import('./BusinessReviewForm.vue')),
  BIZ_FEASIBILITY: defineAsyncComponent(() => import('./BusinessReviewForm.vue')),
  PROJECT_REVIEW: defineAsyncComponent(() => import('./BusinessReviewForm.vue')),
  INVESTMENT_REVIEW: defineAsyncComponent(() => import('./BusinessReviewForm.vue')),
  BUSINESS_APPROVAL: defineAsyncComponent(() => import('./BusinessApprovalForm.vue')),
  PROJECT_APPROVAL: defineAsyncComponent(() => import('./BusinessApprovalForm.vue')),
  DEV_APPROVAL: defineAsyncComponent(() => import('./BusinessApprovalForm.vue')),
  INVESTMENT_APPROVAL: defineAsyncComponent(() => import('./BusinessApprovalForm.vue')),
  PROJECT_DECISION: defineAsyncComponent(() => import('./ProjectDecisionForm.vue')),
  PROJECT_KEY_DECISION: defineAsyncComponent(() => import('./ProjectDecisionForm.vue')),
  DECISION_PROPOSAL: defineAsyncComponent(() => import('./ProjectDecisionForm.vue')),
  KEY_DECISION: defineAsyncComponent(() => import('./ProjectDecisionForm.vue')),
}
