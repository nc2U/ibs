<script lang="ts" setup>
import { computed } from 'vue'
import type { CommissionPayout } from '@/store/types/sales'

const props = defineProps({
  payouts: { type: Array as () => CommissionPayout[], default: () => [] },
})

const totalNetAmount = computed(() =>
  props.payouts.reduce((sum, p) => sum + (p.net_amount || 0), 0)
)

const paidPayouts = computed(() =>
  props.payouts.filter(p => p.pay_status === '3')
)

const paidNetAmount = computed(() =>
  paidPayouts.value.reduce((sum, p) => sum + (p.net_amount || 0), 0)
)

const unpaidNetAmount = computed(() =>
  Math.max(0, totalNetAmount.value - paidNetAmount.value)
)

const completionRate = computed(() => {
  if (totalNetAmount.value === 0) return 0
  return Math.round((paidNetAmount.value / totalNetAmount.value) * 100)
})

const totalTaxAmount = computed(() =>
  props.payouts.reduce((sum, p) => sum + (p.total_tax || 0), 0)
)
</script>

<template>
  <CRow class="mb-4 g-3">
    <!-- 총 지급 대상액 -->
    <CCol sm="6" lg="3">
      <CCard class="shadow-sm h-100 border-start border-start-4 border-start-primary">
        <CCardBody>
          <div class="text-body-secondary small fw-semibold">총 실지급 대상액 (세후)</div>
          <div class="fs-4 fw-bold text-primary">{{ totalNetAmount.toLocaleString() }}원</div>
          <div class="small text-muted">{{ payouts.length }}명 대상</div>
        </CCardBody>
      </CCard>
    </CCol>

    <!-- 지급 완료액 -->
    <CCol sm="6" lg="3">
      <CCard class="shadow-sm h-100 border-start border-start-4 border-start-success">
        <CCardBody>
          <div class="text-body-secondary small fw-semibold">지급 완료액 (이체완료)</div>
          <div class="fs-4 fw-bold text-success">
            {{ paidNetAmount.toLocaleString() }}원
            <span class="fs-6 fw-normal text-muted">({{ completionRate }}%)</span>
          </div>
          <div class="small text-success">{{ paidPayouts.length }}명 이체 완료</div>
        </CCardBody>
      </CCard>
    </CCol>

    <!-- 미지급액 (대기/승인/보류) -->
    <CCol sm="6" lg="3">
      <CCard class="shadow-sm h-100 border-start border-start-4" :class="unpaidNetAmount > 0 ? 'border-start-warning' : 'border-start-secondary'">
        <CCardBody>
          <div class="text-body-secondary small fw-semibold">지급 잔액 (대기/보류)</div>
          <div class="fs-4 fw-bold" :class="unpaidNetAmount > 0 ? 'text-warning' : 'text-secondary'">
            {{ unpaidNetAmount.toLocaleString() }}원
          </div>
          <div class="small text-muted">{{ payouts.length - paidPayouts.length }}명 대기 중</div>
        </CCardBody>
      </CCard>
    </CCol>

    <!-- 원천세 예수금 (다음달 납부용) -->
    <CCol sm="6" lg="3">
      <CCard class="shadow-sm h-100 border-start border-start-4 border-start-danger">
        <CCardBody>
          <div class="text-body-secondary small fw-semibold">원천세 예수금 합계 (3.3%)</div>
          <div class="fs-4 fw-bold text-danger">{{ totalTaxAmount.toLocaleString() }}원</div>
          <div class="small text-muted">익월 10일 세무 신고 납부 대상</div>
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>
</template>
