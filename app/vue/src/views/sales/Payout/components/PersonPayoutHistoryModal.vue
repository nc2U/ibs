<script lang="ts" setup>
/**
 * PersonPayoutHistoryModal.vue
 * 영업인력 개인별 전 회차 누적 수수료 지급 이력 모달
 */
import { ref, computed } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { CommissionPayout, CommissionClawback } from '@/store/types/sales'

const salesStore = useSales()
const isVisible = ref(false)
const isLoading = ref(false)

const personId = ref<number | null>(null)
const personName = ref<string>('')
const historyList = ref<CommissionPayout[]>([])
const clawbackList = ref<CommissionClawback[]>([])

const open = async (payout: CommissionPayout) => {
  personId.value = payout.sales_person
  personName.value = payout.sales_person_name || ''
  historyList.value = []
  clawbackList.value = []
  isVisible.value = true
  isLoading.value = true
  try {
    // 해당 인력의 전 회차 지급 이력
    const params = new URLSearchParams()
    params.append('sales_person', String(payout.sales_person))
    params.append('limit', '500')
    const [payoutRes, clawbackRes] = await Promise.all([
      import('@/api').then(m => m.default.get(`/sales-payout/?${params}`)),
      import('@/api').then(m => m.default.get(`/sales-clawback/?sales_person=${payout.sales_person}`)),
    ])
    historyList.value = payoutRes.data.results ?? payoutRes.data
    clawbackList.value = clawbackRes.data.results ?? clawbackRes.data
  } finally {
    isLoading.value = false
  }
}

const close = () => {
  isVisible.value = false
}

defineExpose({ open, close })

// 누적 집계
const totalGross = computed(() => historyList.value.reduce((s, p) => s + (p.gross_amount || 0), 0))
const totalTax = computed(() => historyList.value.reduce((s, p) => s + (p.total_tax || 0), 0))
const totalNet = computed(() => historyList.value.reduce((s, p) => s + (p.net_amount || 0), 0))
const totalClawback = computed(() => clawbackList.value.reduce((s, c) => s + (c.amount || 0), 0))

const payStatusColor = (status: string) => {
  if (status === '3') return 'success'
  if (status === '2') return 'primary'
  if (status === '4') return 'warning'
  return 'secondary'
}
</script>

<template>
  <CModal :visible="isVisible" size="xl" alignment="center" @close="close">
    <CModalHeader>
      <CModalTitle>
        <v-icon icon="mdi-account-cash" size="small" class="mr-1 text-primary" />
        {{ personName }} — 전 회차 수수료 지급 이력
      </CModalTitle>
    </CModalHeader>

    <CModalBody class="p-0">
      <div v-if="isLoading" class="py-5 text-center text-muted">
        <v-progress-circular indeterminate color="primary" size="36" class="mb-2" />
        <div>이력 조회 중...</div>
      </div>

      <template v-else>
        <!-- 누적 KPI 요약 -->
        <CRow class="g-0 border-bottom">
          <CCol sm="3" class="border-end p-3 text-center">
            <div class="text-body-secondary small fw-semibold">총 지급 회차</div>
            <div class="fs-5 fw-bold text-primary">{{ historyList.length }}회</div>
          </CCol>
          <CCol sm="3" class="border-end p-3 text-center">
            <div class="text-body-secondary small fw-semibold">누적 세전 총액</div>
            <div class="fs-5 fw-bold">{{ totalGross.toLocaleString() }}원</div>
          </CCol>
          <CCol sm="3" class="border-end p-3 text-center">
            <div class="text-body-secondary small fw-semibold">누적 원천세</div>
            <div class="fs-5 fw-bold text-danger">{{ totalTax.toLocaleString() }}원</div>
          </CCol>
          <CCol sm="3" class="p-3 text-center">
            <div class="text-body-secondary small fw-semibold">누적 실지급액 (세후)</div>
            <div class="fs-5 fw-bold text-success">{{ totalNet.toLocaleString() }}원</div>
          </CCol>
        </CRow>

        <!-- 환수 이력 요약 (있는 경우만) -->
        <div
          v-if="clawbackList.length > 0"
          class="px-3 py-2 bg-danger bg-opacity-10 border-bottom d-flex align-items-center gap-2"
        >
          <v-icon icon="mdi-cash-refund" size="small" class="text-danger" />
          <span class="small fw-semibold text-danger">
            환수 이력 {{ clawbackList.length }}건 — 총 {{ totalClawback.toLocaleString() }}원
            <span class="text-muted fw-normal">(미상계: {{ clawbackList.filter(c => !c.is_settled).length }}건)</span>
          </span>
        </div>

        <!-- 지급 이력 테이블 -->
        <CTable hover responsive bordered align="middle" class="mb-0 text-center text-body small">
          <CTableHead color="light">
            <CTableRow>
              <CTableHeaderCell>정산 회차</CTableHeaderCell>
              <CTableHeaderCell>계약건수</CTableHeaderCell>
              <CTableHeaderCell>인센티브</CTableHeaderCell>
              <CTableHeaderCell>기본급/일비</CTableHeaderCell>
              <CTableHeaderCell>공제/환수</CTableHeaderCell>
              <CTableHeaderCell>세전 총액</CTableHeaderCell>
              <CTableHeaderCell>원천세</CTableHeaderCell>
              <CTableHeaderCell class="table-success">실지급액</CTableHeaderCell>
              <CTableHeaderCell>상태</CTableHeaderCell>
              <CTableHeaderCell>지급일</CTableHeaderCell>
            </CTableRow>
          </CTableHead>
          <CTableBody>
            <CTableRow v-for="p in historyList" :key="p.id">
              <CTableDataCell class="small fw-semibold text-start ps-3">
                <!-- period 정보는 API에서 period_title 등을 반환하지 않으므로 id 표기 -->
                <span class="text-muted">#{{ p.period }}</span>
              </CTableDataCell>
              <CTableDataCell class="font-monospace">{{ p.contract_count }}건</CTableDataCell>
              <CTableDataCell class="text-end font-monospace">{{ p.commission_amount.toLocaleString() }}원</CTableDataCell>
              <CTableDataCell class="text-end font-monospace">{{ p.base_pay.toLocaleString() }}원</CTableDataCell>
              <CTableDataCell class="text-end font-monospace text-danger">
                <span v-if="p.deduction_amount > 0">-{{ p.deduction_amount.toLocaleString() }}원</span>
                <span v-else class="text-muted">-</span>
              </CTableDataCell>
              <CTableDataCell class="text-end font-monospace fw-bold">{{ p.gross_amount.toLocaleString() }}원</CTableDataCell>
              <CTableDataCell class="text-end font-monospace text-danger">{{ p.total_tax.toLocaleString() }}원</CTableDataCell>
              <CTableDataCell class="text-end font-monospace fw-bold text-success table-success">
                {{ p.net_amount.toLocaleString() }}원
              </CTableDataCell>
              <CTableDataCell>
                <CBadge :color="payStatusColor(p.pay_status)">{{ p.pay_status_display }}</CBadge>
              </CTableDataCell>
              <CTableDataCell class="small text-muted">{{ p.paid_date || '-' }}</CTableDataCell>
            </CTableRow>

            <CTableRow v-if="historyList.length === 0">
              <CTableDataCell colspan="10" class="py-4 text-center text-muted">
                지급 이력이 없습니다.
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>

        <!-- 환수 이력 상세 (있는 경우만) -->
        <template v-if="clawbackList.length > 0">
          <div class="px-3 pt-3 pb-1 fw-bold small border-top">
            <v-icon icon="mdi-cash-refund" size="small" class="mr-1 text-danger" />
            환수 이력 상세
          </div>
          <CTable hover responsive bordered align="middle" class="mb-0 text-center text-body small">
            <CTableHead color="light">
              <CTableRow>
                <CTableHeaderCell>해지 계약</CTableHeaderCell>
                <CTableHeaderCell>환수 금액</CTableHeaderCell>
                <CTableHeaderCell>환수 사유</CTableHeaderCell>
                <CTableHeaderCell>상계 여부</CTableHeaderCell>
                <CTableHeaderCell>등록일</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              <CTableRow v-for="c in clawbackList" :key="c.id">
                <CTableDataCell class="small text-start ps-3">{{ c.contract_serial || `#${c.contract}` }}</CTableDataCell>
                <CTableDataCell class="text-end font-monospace text-danger fw-bold">
                  {{ c.amount.toLocaleString() }}원
                </CTableDataCell>
                <CTableDataCell class="text-start small text-muted">{{ c.reason }}</CTableDataCell>
                <CTableDataCell>
                  <CBadge :color="c.is_settled ? 'success' : 'warning'">
                    {{ c.is_settled ? '상계 완료' : '미상계' }}
                  </CBadge>
                </CTableDataCell>
                <CTableDataCell class="small text-muted">{{ c.created_at?.slice(0, 10) }}</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </template>
      </template>
    </CModalBody>

    <CModalFooter>
      <v-btn size="small" variant="tonal" @click="close">닫기</v-btn>
    </CModalFooter>
  </CModal>
</template>
