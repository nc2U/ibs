<script lang="ts" setup>
import { computed } from 'vue'
import type { ContractSalesAgent } from '@/store/types/sales'

const props = defineProps({
  totalContracts: { type: Number, default: 0 },
  mappedList: { type: Array as () => ContractSalesAgent[], default: () => [] },
})

const mappedCount = computed(() => props.mappedList.length)
const unmappedCount = computed(() => Math.max(0, props.totalContracts - mappedCount.value))
const mappingRate = computed(() => {
  if (props.totalContracts === 0) return 0
  return Math.round((mappedCount.value / props.totalContracts) * 100)
})

const mgmCount = computed(() => props.mappedList.filter(m => !!m.mgm_name).length)

// 최다 실적 상담사 계산
const topAgent = computed(() => {
  if (props.mappedList.length === 0) return null
  const counts: Record<string, { name: string; team: string; count: number }> = {}
  props.mappedList.forEach(m => {
    const key = m.sales_person_name || '미정'
    if (!counts[key]) {
      counts[key] = { name: key, team: m.team_name || '', count: 0 }
    }
    counts[key].count += 1
  })
  const sorted = Object.values(counts).sort((a, b) => b.count - a.count)
  return sorted[0] || null
})
</script>

<template>
  <CRow class="mb-4 g-3">
    <!-- 총 분양 계약 -->
    <CCol sm="6" lg="3">
      <CCard class="shadow-sm h-100 border-start border-start-4 border-start-primary">
        <CCardBody class="d-flex justify-content-between align-items-center">
          <div>
            <div class="text-body-secondary small fw-semibold">총 분양 계약</div>
            <div class="fs-4 fw-bold text-primary">{{ totalContracts.toLocaleString() }}건</div>
            <div class="small text-muted">프로젝트 전체 계약</div>
          </div>
          <v-icon icon="mdi-file-document-check-outline" size="x-large" class="text-primary opacity-50" />
        </CCardBody>
      </CCard>
    </CCol>

    <!-- 영업 담당자 배정 완료 -->
    <CCol sm="6" lg="3">
      <CCard class="shadow-sm h-100 border-start border-start-4 border-start-success">
        <CCardBody class="d-flex justify-content-between align-items-center">
          <div>
            <div class="text-body-secondary small fw-semibold">영업 담당자 배정</div>
            <div class="fs-4 fw-bold text-success">
              {{ mappedCount.toLocaleString() }}건
              <span class="fs-6 fw-normal text-muted">({{ mappingRate }}%)</span>
            </div>
            <div class="small text-success">실적 매핑 완료</div>
          </div>
          <v-icon icon="mdi-account-check" size="x-large" class="text-success opacity-50" />
        </CCardBody>
      </CCard>
    </CCol>

    <!-- 미배정 계약건 -->
    <CCol sm="6" lg="3">
      <CCard class="shadow-sm h-100 border-start border-start-4" :class="unmappedCount > 0 ? 'border-start-warning' : 'border-start-secondary'">
        <CCardBody class="d-flex justify-content-between align-items-center">
          <div>
            <div class="text-body-secondary small fw-semibold">미배정 계약 건수</div>
            <div class="fs-4 fw-bold" :class="unmappedCount > 0 ? 'text-warning' : 'text-secondary'">
              {{ unmappedCount.toLocaleString() }}건
            </div>
            <div class="small text-muted">담당 상담사 배정 필요</div>
          </div>
          <v-icon icon="mdi-account-alert" size="x-large" :class="unmappedCount > 0 ? 'text-warning' : 'text-secondary'" class="opacity-50" />
        </CCardBody>
      </CCard>
    </CCol>

    <!-- 최다 실적 상담사 (Top Performer) -->
    <CCol sm="6" lg="3">
      <CCard class="shadow-sm h-100 border-start border-start-4 border-start-info">
        <CCardBody class="d-flex justify-content-between align-items-center">
          <div>
            <div class="text-body-secondary small fw-semibold">최다 실적 상담사</div>
            <div v-if="topAgent" class="fs-5 fw-bold text-dark">
              {{ topAgent.name }} <span class="fs-6 fw-normal text-primary">({{ topAgent.count }}건)</span>
            </div>
            <div v-else class="fs-6 text-muted">-</div>
            <div class="small text-muted">
              MGM 연계 {{ mgmCount }}건 포함
            </div>
          </div>
          <v-icon icon="mdi-trophy-outline" size="x-large" class="text-info opacity-50" />
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>
</template>
