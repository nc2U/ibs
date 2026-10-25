<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useProject } from '@/store/pinia/project'
import { useSales } from '@/store/pinia/sales'
import WidgetWrapper from '../WidgetWrapper.vue'
import type { SettlementPeriod, CommissionPayout, AgencyPayout } from '@/store/types/sales'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const router = useRouter()
const projectStore = useProject()
const salesStore = useSales()

const selectedProject = ref<number | null>(null)
const selectedPeriodId = ref<number | null>(null)
const loading = ref(false)
const tab = ref<'settlement' | 'agency'>('settlement')

const projectOptions = computed(() => projectStore.projSelect)

// 회차 목록
const periodOptions = computed(() =>
  salesStore.periodList.map(p => ({
    title: `${p.title} (${p.start_date} ~ ${p.end_date})`,
    value: p.id,
  })),
)

// 선택된 회차 객체
const currentPeriod = computed<SettlementPeriod | undefined>(() =>
  salesStore.periodList.find(p => p.id === selectedPeriodId.value),
)

// 개인별 지급 명세 목록
const currentPayouts = computed<CommissionPayout[]>(() => salesStore.payoutList)

// 대행사별 지급 명세 목록
const currentAgencyPayouts = computed<AgencyPayout[]>(() => salesStore.agencyPayoutList)

// 통계 계산
const totalNetPay = computed(() =>
  currentPayouts.value.reduce((acc, cur) => acc + (cur.net_amount || 0), 0),
)

const paidCount = computed(() => currentPayouts.value.filter(p => p.pay_status === '3').length)
const readyCount = computed(() => currentPayouts.value.filter(p => p.pay_status === '2').length)
const unpaidCount = computed(() => currentPayouts.value.filter(p => p.pay_status === '1').length)

const paidAmount = computed(() =>
  currentPayouts.value
    .filter(p => p.pay_status === '3')
    .reduce((acc, cur) => acc + (cur.net_amount || 0), 0),
)

const payoutRate = computed(() => {
  if (!totalNetPay.value) return 0
  return (paidAmount.value / totalNetPay.value) * 100
})

// 총 미처리 환수금액
const totalClawbackPending = computed(() =>
  salesStore.clawbackList
    .filter(c => !c.is_settled)
    .reduce((acc, cur) => acc + (cur.amount || 0), 0),
)

const formatCurrency = (val?: number) => {
  if (!val) return '0원'
  if (Math.abs(val) >= 100000000) {
    const amount = val / 100000000
    const formatted = new Intl.NumberFormat('ko-KR', {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(amount)
    return `${formatted}억`
  }
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(val)
}

const getPeriodStatusText = (status: string) => {
  switch (status) {
    case '1':
      return '집계중'
    case '2':
      return '정산확정'
    case '3':
      return '지급완료'
    default:
      return '대기'
  }
}

const getPeriodStatusColor = (status: string) => {
  switch (status) {
    case '1':
      return 'warning'
    case '2':
      return 'info'
    case '3':
      return 'success'
    default:
      return 'grey'
  }
}

const getPayStatusText = (status: string) => {
  switch (status) {
    case '1':
      return '대기'
    case '2':
      return '승인'
    case '3':
      return '지급완료'
    case '4':
      return '지급보류'
    default:
      return '-'
  }
}

const getPayStatusColor = (status: string) => {
  switch (status) {
    case '1':
      return 'grey'
    case '2':
      return 'info'
    case '3':
      return 'success'
    case '4':
      return 'error'
    default:
      return 'grey'
  }
}

// 데이터 페치
const fetchSalesData = async (projectId: number) => {
  loading.value = true
  try {
    await Promise.all([
      salesStore.fetchPeriodList(projectId),
      salesStore.fetchAgencyList(projectId),
      salesStore.fetchTeamList(undefined, projectId),
      salesStore.fetchClawbackList(undefined, projectId),
    ])

    if (salesStore.periodList.length > 0) {
      selectedPeriodId.value = salesStore.periodList[0].id
      await Promise.all([
        salesStore.fetchPayoutList(selectedPeriodId.value),
        salesStore.fetchAgencyPayoutList(selectedPeriodId.value),
      ])
    } else {
      selectedPeriodId.value = null
      salesStore.payoutList = []
      salesStore.agencyPayoutList = []
    }
  } catch (error) {
    console.error('Failed to fetch sales dashboard data:', error)
  } finally {
    loading.value = false
  }
}

const onPeriodChange = async () => {
  if (!selectedPeriodId.value) return
  loading.value = true
  try {
    await Promise.all([
      salesStore.fetchPayoutList(selectedPeriodId.value),
      salesStore.fetchAgencyPayoutList(selectedPeriodId.value),
    ])
  } finally {
    loading.value = false
  }
}

const handleRefresh = async () => {
  if (selectedProject.value) {
    await fetchSalesData(selectedProject.value)
  }
}

const navigateTo = (path: string) => {
  router.push(path)
}

// 프로젝트 옵션 로드 시 첫 프로젝트 자동 바인딩
watch(
  () => projectStore.projSelect,
  newVal => {
    if (!selectedProject.value && newVal && newVal.length > 0) {
      selectedProject.value = newVal[0].value ?? null
    }
  },
  { immediate: true },
)

// 프로젝트 변경 감시
watch(selectedProject, newProjectId => {
  if (newProjectId) {
    fetchSalesData(newProjectId)
  }
})

onMounted(async () => {
  if (!projectStore.projSelect || projectStore.projSelect.length === 0) {
    await projectStore.fetchProjectList()
  }
  if (!selectedProject.value && projectStore.projSelect && projectStore.projSelect.length > 0) {
    selectedProject.value = projectStore.projSelect[0].value ?? null
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
    <div class="sales-widget-content pa-3 d-flex flex-column h-100 overflow-y-auto">
      <!-- 프로젝트 및 회차 선택 바 -->
      <div class="d-flex flex-wrap align-center gap-2 mb-2">
        <v-select
          v-model="selectedProject"
          :items="projectOptions"
          item-title="label"
          item-value="value"
          density="compact"
          variant="outlined"
          hide-details
          class="project-select flex-grow-1"
          style="min-width: 140px; max-width: 220px"
        />

        <v-select
          v-if="periodOptions.length > 0"
          v-model="selectedPeriodId"
          :items="periodOptions"
          item-title="title"
          item-value="value"
          density="compact"
          variant="outlined"
          hide-details
          class="period-select flex-grow-1"
          style="min-width: 160px; max-width: 240px"
          @update:model-value="onPeriodChange"
        />

        <v-spacer />

        <div class="d-flex align-center gap-1">
          <v-btn
            size="x-small"
            variant="tonal"
            color="primary"
            prepend-icon="mdi-calculator-variant-outline"
            @click="navigateTo('/sales/settlement')"
          >
            정산 관리
          </v-btn>
          <v-btn
            size="x-small"
            variant="tonal"
            color="success"
            prepend-icon="mdi-cash-check"
            @click="navigateTo('/sales/payout')"
          >
            지급 관리
          </v-btn>
        </div>
      </div>

      <!-- 탭 바 -->
      <v-tabs v-model="tab" density="compact" color="primary" class="mb-2 border-b">
        <v-tab value="settlement" size="small">
          <v-icon icon="mdi-cash-multiple" size="16" class="me-1" />
          정산 및 지급 요약
        </v-tab>
        <v-tab value="agency" size="small">
          <v-icon icon="mdi-account-group" size="16" class="me-1" />
          대행사 / 팀 현황
        </v-tab>
      </v-tabs>

      <!-- 로딩 인디케이터 -->
      <div v-if="loading" class="d-flex justify-center align-center flex-grow-1 py-8">
        <v-progress-circular indeterminate color="primary" size="32" />
      </div>

      <!-- 본문 영역 -->
      <div v-else class="flex-grow-1">
        <!-- ── TAB 1: 정산 및 지급 요약 ── -->
        <div v-if="tab === 'settlement'">
          <div v-if="currentPeriod">
            <!-- 회차 메타 칩 -->
            <div class="d-flex align-center justify-space-between mb-2 px-1">
              <span class="text-caption text-medium-emphasis">
                기간: {{ currentPeriod.start_date }} ~ {{ currentPeriod.end_date }}
              </span>
              <v-chip
                :color="getPeriodStatusColor(currentPeriod.status)"
                size="x-small"
                variant="flat"
                class="fw-bold"
              >
                {{ getPeriodStatusText(currentPeriod.status) }}
              </v-chip>
            </div>

            <!-- KPI 카드 4분할 -->
            <v-row dense class="mb-2">
              <v-col cols="6" sm="3">
                <div class="kpi-card pa-2 rounded-lg border text-center">
                  <div class="text-caption text-medium-emphasis">실지급 총액</div>
                  <div class="text-body-2 fw-bold text-primary text-truncate">
                    {{ formatCurrency(totalNetPay) }}
                  </div>
                </div>
              </v-col>
              <v-col cols="6" sm="3">
                <div class="kpi-card pa-2 rounded-lg border text-center">
                  <div class="text-caption text-medium-emphasis">지급 진척도</div>
                  <div class="text-body-2 fw-bold text-success text-truncate">
                    {{ payoutRate.toFixed(1) }}%
                  </div>
                </div>
              </v-col>
              <v-col cols="6" sm="3">
                <div class="kpi-card pa-2 rounded-lg border text-center">
                  <div class="text-caption text-medium-emphasis">정산 인원</div>
                  <div class="text-body-2 fw-bold text-truncate">{{ currentPayouts.length }}명</div>
                </div>
              </v-col>
              <v-col cols="6" sm="3">
                <div class="kpi-card pa-2 rounded-lg border text-center">
                  <div class="text-caption text-medium-emphasis">미처리 환수</div>
                  <div
                    class="text-body-2 fw-bold text-truncate"
                    :class="totalClawbackPending > 0 ? 'text-error' : 'text-medium-emphasis'"
                  >
                    {{ formatCurrency(totalClawbackPending) }}
                  </div>
                </div>
              </v-col>
            </v-row>

            <!-- 지급 진행 상태 누적 바 -->
            <div class="progress-section pa-2 rounded-lg border mb-3">
              <div class="d-flex justify-space-between align-center mb-1">
                <span class="text-caption fw-bold text-medium-emphasis">개인별 지급 진행 현황</span>
                <span class="text-caption text-muted">
                  완료 {{ paidCount }} / 대기 {{ readyCount }} / 미지급 {{ unpaidCount }} (총
                  {{ currentPayouts.length }}건)
                </span>
              </div>
              <v-progress-linear
                :model-value="payoutRate"
                color="success"
                background-color="grey-lighten-2"
                height="8"
                rounded
              />
            </div>

            <!-- 최근 지급 대상자 미니 리스트 -->
            <div class="payout-list-section">
              <div class="text-caption fw-bold text-medium-emphasis mb-1">
                최근 지급 대상자 명세
              </div>
              <v-table density="compact" class="border rounded-lg text-caption">
                <thead>
                  <tr class="bg-light">
                    <th>성명</th>
                    <th>직책</th>
                    <th>소속팀</th>
                    <th class="text-end">실지급액</th>
                    <th class="text-center">상태</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="payout in currentPayouts.slice(0, 4)" :key="payout.id">
                    <td class="fw-bold">{{ payout.sales_person_name || '-' }}</td>
                    <td>{{ payout.duty_display || '-' }}</td>
                    <td class="text-muted text-truncate" style="max-width: 90px">
                      {{ payout.team_name || '-' }}
                    </td>
                    <td class="text-end fw-bold">{{ formatCurrency(payout.net_amount) }}</td>
                    <td class="text-center">
                      <v-chip
                        :color="getPayStatusColor(payout.pay_status)"
                        size="x-small"
                        variant="tonal"
                      >
                        {{ getPayStatusText(payout.pay_status) }}
                      </v-chip>
                    </td>
                  </tr>
                  <tr v-if="currentPayouts.length === 0">
                    <td colspan="5" class="text-center py-3 text-muted">
                      정산 산출된 지급 명세가 없습니다.
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </div>
          </div>

          <!-- 회차가 없는 경우 Empty State -->
          <div v-else class="text-center py-8 text-medium-emphasis">
            <v-icon icon="mdi-calendar-blank-outline" size="40" class="mb-2 text-grey" />
            <div class="text-body-2 mb-2">등록된 수수료 정산 회차가 없습니다.</div>
            <v-btn
              size="small"
              variant="outlined"
              color="primary"
              @click="navigateTo('/sales/settlement')"
            >
              정산 회차 개설하기
            </v-btn>
          </div>
        </div>

        <!-- ── TAB 2: 대행사 / 팀 현황 ── -->
        <div v-else-if="tab === 'agency'">
          <div v-if="salesStore.agencyList.length > 0">
            <!-- 요약 배지 -->
            <div class="d-flex gap-2 mb-2">
              <v-chip size="small" variant="tonal" color="primary">
                대행사 {{ salesStore.agencyList.length }}개사
              </v-chip>
              <v-chip size="small" variant="tonal" color="secondary">
                영업팀 {{ salesStore.teamList.length }}개 팀
              </v-chip>
            </div>

            <!-- 대행사 목록 카드 -->
            <div class="agency-list-cards d-flex flex-column gap-2">
              <div
                v-for="agency in salesStore.agencyList"
                :key="agency.id"
                class="pa-2 border rounded-lg d-flex align-center justify-space-between bg-surface"
              >
                <div>
                  <div class="d-flex align-center gap-1 mb-1">
                    <span class="text-body-2 fw-bold">{{ agency.name }}</span>
                    <v-chip
                      size="x-small"
                      :color="agency.is_direct_managed ? 'primary' : 'grey'"
                      variant="flat"
                    >
                      {{ agency.is_direct_managed ? '직영' : '외주' }}
                    </v-chip>
                  </div>
                  <div class="text-caption text-medium-emphasis">
                    대표: {{ agency.ceo_name || '-' }} | 전화: {{ agency.phone || '-' }}
                  </div>
                </div>

                <!-- 대행사별 지급 현황 매핑이 있을 경우 -->
                <div class="text-end">
                  <div class="text-caption text-medium-emphasis">
                    소속팀 {{ salesStore.teamList.filter(t => t.agency === agency.id).length }}개
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 대행사가 없는 경우 Empty State -->
          <div v-else class="text-center py-8 text-medium-emphasis">
            <v-icon icon="mdi-office-building-outline" size="40" class="mb-2 text-grey" />
            <div class="text-body-2 mb-2">등록된 분양 대행사가 없습니다.</div>
            <v-btn
              size="small"
              variant="outlined"
              color="primary"
              @click="navigateTo('/sales/organization')"
            >
              대행사 등록하기
            </v-btn>
          </div>
        </div>
      </div>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.sales-widget-content {
  min-height: 240px;
}
.kpi-card {
  background-color: rgba(var(--v-theme-surface-variant), 0.15);
  transition: transform 0.15s ease-in-out;
}
.kpi-card:hover {
  transform: translateY(-1px);
}
.gap-1 {
  gap: 4px;
}
.gap-2 {
  gap: 8px;
}
</style>
