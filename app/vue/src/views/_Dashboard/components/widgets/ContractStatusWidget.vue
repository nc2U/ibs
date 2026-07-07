<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/api'
import { useProject } from '@/store/pinia/project'
import { CChartDoughnut, CChartBar } from '@coreui/vue-chartjs'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const projectStore = useProject()
const selectedProject = ref<number | null>(null)
const loading = ref(false)
const tab = ref<'overall' | 'type'>('overall')

// 전체 계약 현황 데이터
const totalUnits = ref(0)
const subsNum = ref(0)
const contsNum = ref(0)
const nonContsNum = ref(0)

// 타입별 분양 현황 데이터
interface UnitTypeStatus {
  order_group_name: string
  unit_type_name: string
  contract_units: number
  non_contract_units: number
}
const unitTypeStatusList = ref<UnitTypeStatus[]>([])

const projectOptions = computed(() => projectStore.projSelect)

// 가장 마지막에 등록된 계약건의 프로젝트 ID를 초기값으로 설정
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

// 프로젝트별 계약 데이터 Fetch
const fetchContractStatusData = async (projectId: number) => {
  loading.value = true
  try {
    // 1. 전체 현황 데이터
    const aggregateRes = await api.get(`/cont-aggregate/${projectId}/`)
    totalUnits.value = aggregateRes.data.total_units || 0
    subsNum.value = aggregateRes.data.subs_num || 0
    contsNum.value = aggregateRes.data.conts_num || 0
    nonContsNum.value = aggregateRes.data.non_conts_num || 0

    // 2. 타입별 현황 데이터
    const statusRes = await api.get(`/payment-status-by-unit-type/?project=${projectId}`)
    if (Array.isArray(statusRes.data)) {
      unitTypeStatusList.value = statusRes.data.map((item: any) => ({
        order_group_name: item.order_group_name || '',
        unit_type_name: item.unit_type_name || '',
        contract_units: item.contract_units || 0,
        non_contract_units: item.non_contract_units || 0,
      }))
    } else {
      unitTypeStatusList.value = []
    }
  } catch (error) {
    console.error('Failed to fetch contract status data:', error)
    totalUnits.value = 0
    subsNum.value = 0
    contsNum.value = 0
    nonContsNum.value = 0
    unitTypeStatusList.value = []
  } finally {
    loading.value = false
  }
}

const handleRefresh = async () => {
  if (selectedProject.value) {
    await fetchContractStatusData(selectedProject.value)
  }
}

// 분양 계약률
const contractRate = computed(() => {
  if (!totalUnits.value) return 0
  return Number(((contsNum.value / totalUnits.value) * 100).toFixed(1))
})

// 1. 전체 현황 도넛 차트 데이터
const doughnutChartData = computed(() => {
  return {
    labels: ['계약완료', '청약진행', '미계약'],
    datasets: [
      {
        backgroundColor: ['#2eb85c', '#f9b115', '#e55353'],
        data: [contsNum.value, subsNum.value, nonContsNum.value],
      },
    ],
  }
})

const doughnutChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        boxWidth: 10,
        font: {
          size: 10,
        },
      },
    },
  },
}

// 2. 타입별 현황 바 차트 데이터
const barChartData = computed(() => {
  const labels = unitTypeStatusList.value.map(item =>
    item.order_group_name
      ? `[${item.order_group_name}] ${item.unit_type_name}`
      : item.unit_type_name,
  )
  const contractData = unitTypeStatusList.value.map(item => item.contract_units)
  const nonContractData = unitTypeStatusList.value.map(item => item.non_contract_units)

  return {
    labels,
    datasets: [
      {
        label: '계약완료',
        backgroundColor: '#2eb85c',
        data: contractData,
      },
      {
        label: '미계약',
        backgroundColor: '#e55353',
        data: nonContractData,
      },
    ],
  }
})

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      stacked: true,
    },
    y: {
      stacked: true,
      ticks: {
        beginAtZero: true,
        precision: 0,
      },
    },
  },
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        boxWidth: 10,
        font: {
          size: 10,
        },
      },
    },
  },
}

onMounted(async () => {
  if (projectStore.projectList.length === 0) {
    await projectStore.fetchProjectList()
  }
  await fetchInitialProject()
})

watch(selectedProject, newVal => {
  if (newVal) {
    fetchContractStatusData(newVal)
  }
})
</script>

<template>
  <WidgetWrapper
    :widget-id="widgetId"
    :title="title"
    :icon="icon"
    refreshable
    @refresh="handleRefresh"
  >
    <div class="contract-status-widget d-flex flex-column h-100">
      <!-- 프로젝트 선택기 및 탭 조절 (헤더 영역 우측 상단 드롭다운 심플 배치) -->
      <div class="d-flex align-center justify-space-between mb-2 pb-2">
        <v-btn-toggle
          v-model="tab"
          mandatory
          density="comfortable"
          color="info"
          style="height: 30px"
        >
          <v-btn value="overall" size="small" class="px-2 font-weight-medium">전체</v-btn>
          <v-btn value="type" size="small" class="px-2 font-weight-medium">타입별</v-btn>
        </v-btn-toggle>

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

      <!-- 로딩 바 -->
      <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />

      <!-- 콘텐츠 영역 -->
      <div class="widget-content flex-grow-1 d-flex flex-column">
        <!-- 1. 전체 현황 탭 -->
        <template v-if="tab === 'overall'">
          <div class="chart-container flex-grow-1 position-relative" style="height: 140px">
            <CChartDoughnut
              v-if="totalUnits > 0"
              :data="doughnutChartData"
              :options="doughnutChartOptions"
              class="h-100"
            />
            <div
              v-else-if="!loading"
              class="d-flex align-center justify-center h-100 text-caption text-medium-emphasis"
            >
              계약 정보가 존재하지 않습니다.
            </div>
          </div>

          <!-- 상세 지표 정보 -->
          <div class="stats-panel mt-2">
            <v-row no-gutters class="text-center">
              <v-col cols="4" class="stat-box border-end pr-1">
                <div class="text-caption text-medium-emphasis">계약률</div>
                <div class="text-body-2 font-weight-bold text-success">{{ contractRate }}%</div>
                <div class="text-caption text-medium-emphasis">
                  ({{ contsNum }} / {{ totalUnits }}세대)
                </div>
              </v-col>
              <v-col cols="4" class="stat-box border-end px-1">
                <div class="text-caption text-medium-emphasis">청약 건수</div>
                <div class="text-body-2 font-weight-bold text-warning">{{ subsNum }}건</div>
                <div class="text-caption text-medium-emphasis">대기</div>
              </v-col>
              <v-col cols="4" class="stat-box pl-1">
                <div class="text-caption text-medium-emphasis">미계약</div>
                <div class="text-body-2 font-weight-bold text-error">{{ nonContsNum }}세대</div>
                <div class="text-caption text-medium-emphasis">잔여</div>
              </v-col>
            </v-row>
          </div>
        </template>

        <!-- 2. 타입별 분양 현황 탭 -->
        <template v-else-if="tab === 'type'">
          <div class="chart-container flex-grow-1 position-relative" style="height: 190px">
            <CChartBar
              v-if="unitTypeStatusList.length > 0"
              :data="barChartData"
              :options="barChartOptions"
              class="h-100"
            />
            <div
              v-else-if="!loading"
              class="d-flex align-center justify-center h-100 text-caption text-medium-emphasis"
            >
              타입별 상세 분양 정보가 존재하지 않습니다.
            </div>
          </div>
        </template>
      </div>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.contract-status-widget {
  min-height: 280px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.border-end {
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.border-bottom {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.compact-select :deep(.v-field__input) {
  font-size: 1em !important;
  min-height: 30px !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.compact-select :deep(.v-field__append-inner) {
  padding-top: 0 !important;
}

.compact-select :deep(.v-select__selection-text) {
  font-size: 1em !important;
  font-weight: 500;
}
</style>
