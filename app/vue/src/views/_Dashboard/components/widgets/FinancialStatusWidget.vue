<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/api'
import { useProject } from '@/store/pinia/project'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const projectStore = useProject()
const selectedProject = ref<number | null>(null)
const loading = ref(false)

const summaryData = ref<any>(null)

const projectOptions = computed(() => projectStore.projSelect)

// 헬퍼: 수납 통계 변수들 계산
const payOrderList = computed<any[]>(() => summaryData.value?.pay_orders || [])
const contAggregate = computed(() => summaryData.value?.aggregate || {})

const totalContAmount = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + (order.contract_amount ?? 0), 0),
)
const totalActualCollected = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + (order.collection?.actual_collected ?? 0), 0),
)
const totalDueUnpaidAmount = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + (order.due_period?.unpaid_amount ?? 0), 0),
)
const totalNotDueUnpaid = computed(() =>
  payOrderList.value.reduce((acc, order) => acc + (order.not_due_unpaid ?? 0), 0),
)

const collectionRate = computed(() => {
  if (!totalContAmount.value) return 0
  return (totalActualCollected.value / totalContAmount.value) * 100
})

const formatCurrency = (val: number) => {
  if (!val) return '0원'
  if (val >= 100000000) {
    const amount = val / 100000000
    const formatted = new Intl.NumberFormat('ko-KR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount)
    return `${formatted}억 원`
  }
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(val)
}

const fetchInitialProject = async () => {
  try {
    const res = await api.get('/contract-set/?limit=1')
    if (res.data && res.data.results && res.data.results.length > 0) {
      selectedProject.value = res.data.results[0].project ?? null
    } else {
      if (projectStore.projSelect.length > 0) {
        selectedProject.value = projectStore.projSelect[0].value ?? null
      }
    }
  } catch (error) {
    console.error('Failed to fetch latest contract project:', error)
    if (projectStore.projSelect.length > 0) {
      selectedProject.value = projectStore.projSelect[0].value ?? null
    }
  }
}

const fetchFinancialSummary = async (projectId: number) => {
  loading.value = true
  try {
    const todayStr = new Date().toISOString().substring(0, 10)
    const res = await api.get(`/ledger/overall-summary/?project=${projectId}&date=${todayStr}`)
    summaryData.value = res.data
  } catch (error) {
    console.error('Failed to fetch financial summary:', error)
    summaryData.value = null
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  if (selectedProject.value) {
    fetchFinancialSummary(selectedProject.value)
  }
}

watch(
  selectedProject,
  newProj => {
    if (newProj) {
      fetchFinancialSummary(newProj)
    }
  },
  { immediate: true },
)

onMounted(async () => {
  if (projectStore.projectList.length === 0) {
    await projectStore.fetchProjectList()
  }
  await fetchInitialProject()
})
</script>

<template>
  <WidgetWrapper
    :widget-id="widgetId"
    :title="title"
    :icon="icon"
    refreshable
    @refresh="refreshData"
  >
    <div class="financial-status-widget d-flex flex-column h-100">
      <!-- 프로젝트 선택 드롭다운 (컨텐츠 최상단 배치) -->
      <div class="d-flex align-center justify-space-between mb-2 pb-2">
        <span class="text-medium-emphasis">프로젝트별 수납 현황</span>
        <div class="project-selector-wrapper text-muted" style="width: 240px">
          <v-select
            v-model="selectedProject"
            :items="projectOptions"
            item-title="label"
            item-value="value"
            density="compact"
            hide-details
            variant="underlined"
            class="compact-select"
          />
        </div>
      </div>

      <v-progress-linear
        v-if="loading"
        key="loading-bar"
        indeterminate
        color="primary"
        class="mb-2"
      />

      <div
        v-else-if="!summaryData"
        key="no-data"
        class="d-flex align-center justify-center py-8 text-grey text-caption"
      >
        분양 수납 집계 데이터를 찾을 수 없습니다.
      </div>

      <div v-else key="data-content" class="summary-content flex-grow-1">
        <!-- 2x2 그리드형 카드 지표 -->
        <v-row class="ma-0 mb-4" dense>
          <v-col cols="6" class="pa-1">
            <div class="kpi-card pa-3 rounded-lg border">
              <div class="text-caption text-medium-emphasis">총 계약률</div>
              <div class="text-h6 font-weight-bold text-slate-800">
                {{
                  contAggregate.contract_rate
                    ? Number(contAggregate.contract_rate).toFixed(2)
                    : '0.00'
                }}%
              </div>
            </div>
          </v-col>
          <v-col cols="6" class="pa-1">
            <div class="kpi-card pa-3 rounded-lg border">
              <div class="text-caption text-medium-emphasis">수납율</div>
              <div class="text-h6 font-weight-bold text-slate-800">
                {{ collectionRate.toFixed(2) }}%
              </div>
            </div>
          </v-col>
          <v-col cols="6" class="pa-1">
            <div class="kpi-card pa-3 rounded-lg border">
              <div class="text-caption text-medium-emphasis">실수납액</div>
              <div class="text-body-1 font-weight-bold text-emerald">
                {{ formatCurrency(totalActualCollected) }}
              </div>
            </div>
          </v-col>
          <v-col cols="6" class="pa-1">
            <div class="kpi-card pa-3 rounded-lg border">
              <div class="text-caption text-medium-emphasis">연체 미수금</div>
              <div class="text-body-1 font-weight-bold text-error">
                {{ formatCurrency(totalDueUnpaidAmount) }}
              </div>
            </div>
          </v-col>
        </v-row>

        <!-- 수납 진행 누적 프로그레스 바 -->
        <div class="progress-section mt-3 pa-2 rounded-lg border">
          <div class="d-flex justify-space-between align-center mb-2">
            <span class="font-weight-bold text-medium-emphasis">수납 진행 추이</span>
            <span class="text-muted"> 총 약정 : {{ formatCurrency(totalContAmount) }} </span>
          </div>

          <!-- 누적 바 그래프 -->
          <div class="stacked-bar-container rounded-sm overflow-hidden mb-2 d-flex">
            <div
              class="bar-segment collected"
              :style="{
                width: `${totalContAmount ? (totalActualCollected / totalContAmount) * 100 : 0}%`,
              }"
            >
              <v-tooltip activator="parent" location="top">수납완료</v-tooltip>
            </div>
            <div
              class="bar-segment unpaid"
              :style="{
                width: `${totalContAmount ? (totalDueUnpaidAmount / totalContAmount) * 100 : 0}%`,
              }"
            >
              <v-tooltip activator="parent" location="top">연체미수</v-tooltip>
            </div>
            <div
              class="bar-segment remaining"
              :style="{
                width: `${totalContAmount ? (totalNotDueUnpaid / totalContAmount) * 100 : 100}%`,
              }"
            >
              <v-tooltip activator="parent" location="top">미도래</v-tooltip>
            </div>
          </div>

          <!-- 범례 -->
          <div class="d-flex justify-space-between text-muted">
            <div class="d-flex align-center">
              <span class="dot collected mr-1" />
              <span>
                수납 ({{
                  totalContAmount ? ((totalActualCollected / totalContAmount) * 100).toFixed(1) : 0
                }}%)
              </span>
            </div>
            <div class="d-flex align-center">
              <span class="dot unpaid mr-1" />
              <span>
                연체 ({{
                  totalContAmount ? ((totalDueUnpaidAmount / totalContAmount) * 100).toFixed(1) : 0
                }}%)
              </span>
            </div>
            <div class="d-flex align-center">
              <span class="dot remaining mr-1" />
              <span>
                미도래 ({{
                  totalContAmount ? ((totalNotDueUnpaid / totalContAmount) * 100).toFixed(1) : 100
                }}%)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </WidgetWrapper>
</template>

<style scoped lang="scss">
.financial-status-widget {
  height: 100%;
}

.kpi-card {
  background-color: rgba(var(--v-theme-on-surface), 0.01);
  border-color: rgba(var(--v-theme-on-surface), 0.08) !important;
}

.text-emerald {
  color: #059669;
}

.stacked-bar-container {
  height: 16px;
  background-color: rgba(var(--v-theme-on-surface), 0.06);
  display: flex;
}

.bar-segment {
  height: 100%;
  transition: width 0.3s ease;

  &.collected {
    background-color: #059669;
  }
  &.unpaid {
    background-color: #e11d48;
  }
  &.remaining {
    background-color: #94a3b8;
  }
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;

  &.collected {
    background-color: #059669;
  }
  &.unpaid {
    background-color: #e11d48;
  }
  &.remaining {
    background-color: #94a3b8;
  }
}

body.dark-theme {
  .kpi-card,
  .progress-section {
    border-color: rgba(255, 255, 255, 0.08) !important;
    background-color: rgba(255, 255, 255, 0.02);
  }
  .text-emerald {
    color: #34d399;
  }
  .bar-segment.collected,
  .dot.collected {
    background-color: #34d399;
  }
  .bar-segment.unpaid,
  .dot.unpaid {
    background-color: #f43f5e;
  }
  .bar-segment.remaining,
  .dot.remaining {
    background-color: #64748b;
  }
}
</style>
