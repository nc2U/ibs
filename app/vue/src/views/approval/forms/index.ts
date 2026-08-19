import { defineAsyncComponent, type Component } from 'vue'

export { default as DynamicSchemaForm } from './DynamicSchemaForm.vue'
export { default as LeaveApplicationForm } from './LeaveApplicationForm.vue'
export { default as ExpenseReportForm } from './ExpenseReportForm.vue'
export { default as PurchaseOrderForm } from './PurchaseOrderForm.vue'

/**
 * STATIC 폼 컴포넌트 레지스트리
 * DocumentType.form_template_key 와 매칭되는 Vue 컴포넌트 목록
 */
export const STATIC_FORM_REGISTRY: Record<string, Component> = {
  LEAVE_APPLICATION: defineAsyncComponent(() => import('./LeaveApplicationForm.vue')),
  EXPENSE_REPORT: defineAsyncComponent(() => import('./ExpenseReportForm.vue')),
  PURCHASE_ORDER: defineAsyncComponent(() => import('./PurchaseOrderForm.vue')),
}
