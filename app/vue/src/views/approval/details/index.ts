import { defineAsyncComponent, type Component } from 'vue'

export { default as LeaveDetail } from './LeaveDetail.vue'
export { default as ExpenseDetail } from './ExpenseDetail.vue'
export { default as PurchaseDetail } from './PurchaseDetail.vue'
export { default as OfficialLetterDetail } from './OfficialLetterDetail.vue'
export { default as GeneralDetail } from './GeneralDetail.vue'
export { default as BusinessTripDetail } from './BusinessTripDetail.vue'
export { default as OvertimeDetail } from './OvertimeDetail.vue'
export { default as HrAppointmentDetail } from './HrAppointmentDetail.vue'
export { default as HrRequestDetail } from './HrRequestDetail.vue'
export { default as ExpenseSettlementDetail } from './ExpenseSettlementDetail.vue'
export { default as AdvancePaymentDetail } from './AdvancePaymentDetail.vue'
export { default as ContractDetail } from './ContractDetail.vue'
export { default as ContractChangeDetail } from './ContractChangeDetail.vue'
export { default as LegalReviewDetail } from './LegalReviewDetail.vue'
export { default as BusinessReviewDetail } from './BusinessReviewDetail.vue'
export { default as BusinessApprovalDetail } from './BusinessApprovalDetail.vue'
export { default as ProjectDecisionDetail } from './ProjectDecisionDetail.vue'
export { default as FallbackDetail } from './FallbackDetail.vue'

/**
 * STATIC 상세 뷰 컴포넌트 레지스트리
 * DocumentType.form_template_key 와 매칭되는 Vue 상세 뷰 컴포넌트 목록
 */
export const STATIC_DETAIL_REGISTRY: Record<string, Component> = {
  LEAVE: defineAsyncComponent(() => import('./LeaveDetail.vue')),
  LEAVE_APPLICATION: defineAsyncComponent(() => import('./LeaveDetail.vue')),

  EXPENSE: defineAsyncComponent(() => import('./ExpenseDetail.vue')),
  EXPENSE_REPORT: defineAsyncComponent(() => import('./ExpenseDetail.vue')),

  PURCHASE: defineAsyncComponent(() => import('./PurchaseDetail.vue')),
  PURCHASE_ORDER: defineAsyncComponent(() => import('./PurchaseDetail.vue')),

  OFFICIAL_LETTER: defineAsyncComponent(() => import('./OfficialLetterDetail.vue')),

  GENERAL: defineAsyncComponent(() => import('./GeneralDetail.vue')),
  GENERAL_PROPOSAL: defineAsyncComponent(() => import('./GeneralDetail.vue')),
  BIZ_APPROVAL: defineAsyncComponent(() => import('./GeneralDetail.vue')),
  PROPOSAL: defineAsyncComponent(() => import('./GeneralDetail.vue')),
  GENERAL_DRAFT: defineAsyncComponent(() => import('./GeneralDetail.vue')),

  BUSINESS_TRIP: defineAsyncComponent(() => import('./BusinessTripDetail.vue')),
  TRIP: defineAsyncComponent(() => import('./BusinessTripDetail.vue')),

  OVERTIME: defineAsyncComponent(() => import('./OvertimeDetail.vue')),
  OVERTIME_WORK: defineAsyncComponent(() => import('./OvertimeDetail.vue')),

  HR_APPOINTMENT: defineAsyncComponent(() => import('./HrAppointmentDetail.vue')),
  APPOINTMENT: defineAsyncComponent(() => import('./HrAppointmentDetail.vue')),

  HR_REQUEST: defineAsyncComponent(() => import('./HrRequestDetail.vue')),
  CERT_REQUEST: defineAsyncComponent(() => import('./HrRequestDetail.vue')),

  EXPENSE_SETTLEMENT: defineAsyncComponent(() => import('./ExpenseSettlementDetail.vue')),
  SETTLEMENT: defineAsyncComponent(() => import('./ExpenseSettlementDetail.vue')),

  ADVANCE: defineAsyncComponent(() => import('./AdvancePaymentDetail.vue')),
  ADVANCE_PAY: defineAsyncComponent(() => import('./AdvancePaymentDetail.vue')),
  ADVANCE_REQUEST: defineAsyncComponent(() => import('./AdvancePaymentDetail.vue')),

  CONTRACT: defineAsyncComponent(() => import('./ContractDetail.vue')),
  CONTRACT_APPROVAL: defineAsyncComponent(() => import('./ContractDetail.vue')),
  CONTRACT_PROPOSAL: defineAsyncComponent(() => import('./ContractDetail.vue')),

  CONTRACT_CHANGE: defineAsyncComponent(() => import('./ContractChangeDetail.vue')),
  CONTRACT_TERMINATION: defineAsyncComponent(() => import('./ContractChangeDetail.vue')),
  CONTRACT_AMENDMENT: defineAsyncComponent(() => import('./ContractChangeDetail.vue')),

  LEGAL_REVIEW: defineAsyncComponent(() => import('./LegalReviewDetail.vue')),
  LEGAL_CONSULTATION: defineAsyncComponent(() => import('./LegalReviewDetail.vue')),
  LEGAL_ADVICE: defineAsyncComponent(() => import('./LegalReviewDetail.vue')),

  BUSINESS_REVIEW: defineAsyncComponent(() => import('./BusinessReviewDetail.vue')),
  PROJECT_FEASIBILITY: defineAsyncComponent(() => import('./BusinessReviewDetail.vue')),
  BIZ_FEASIBILITY: defineAsyncComponent(() => import('./BusinessReviewDetail.vue')),
  PROJECT_REVIEW: defineAsyncComponent(() => import('./BusinessReviewDetail.vue')),
  INVESTMENT_REVIEW: defineAsyncComponent(() => import('./BusinessReviewDetail.vue')),

  BUSINESS_APPROVAL: defineAsyncComponent(() => import('./BusinessApprovalDetail.vue')),
  PROJECT_APPROVAL: defineAsyncComponent(() => import('./BusinessApprovalDetail.vue')),
  DEV_APPROVAL: defineAsyncComponent(() => import('./BusinessApprovalDetail.vue')),
  INVESTMENT_APPROVAL: defineAsyncComponent(() => import('./BusinessApprovalDetail.vue')),

  PROJECT_DECISION: defineAsyncComponent(() => import('./ProjectDecisionDetail.vue')),
  PROJECT_KEY_DECISION: defineAsyncComponent(() => import('./ProjectDecisionDetail.vue')),
  DECISION_PROPOSAL: defineAsyncComponent(() => import('./ProjectDecisionDetail.vue')),
  KEY_DECISION: defineAsyncComponent(() => import('./ProjectDecisionDetail.vue')),
}
