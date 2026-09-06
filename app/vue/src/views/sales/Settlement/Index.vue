<script lang="ts" setup>
import { ref, computed, watch, onMounted } from 'vue'
import { navMenu, pageTitle } from '@/views/sales/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useSales } from '@/store/pinia/sales'
import type { Project } from '@/store/types/project'
import type { CommissionPayout } from '@/store/types/sales'
import { TableSecondary } from '@/utils/cssMixins'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PeriodFormModal from './components/PeriodFormModal.vue'
import PayoutDetailModal from './components/PayoutDetailModal.vue'

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const salesStore = useSales()
const periodList = computed(() => salesStore.periodList)
const payoutList = computed(() => salesStore.payoutList)

const selectedPeriodId = ref<number | null>(null)
const selectedPeriod = computed(() =>
  periodList.value.find(p => p.id === selectedPeriodId.value) || null
)

const periodModalRef = ref()
const detailModalRef = ref()

const loadData = async (projId: number) => {
  await salesStore.fetchPeriodList(projId)
  if (periodList.value.length > 0) {
    if (!selectedPeriodId.value || !periodList.value.some(p => p.id === selectedPeriodId.value)) {
      selectedPeriodId.value = periodList.value[0].id
    }
    await salesStore.fetchPayoutList(selectedPeriodId.value)
  } else {
    selectedPeriodId.value = null
    salesStore.payoutList = []
  }
}

const projSelect = async (projId: number | null) => {
  if (projId) {
    await loadData(projId)
  }
}

watch(
  project,
  newVal => {
    if (newVal) loadData(newVal)
  },
  { immediate: true },
)

watch(selectedPeriodId, async newVal => {
  if (newVal) {
    await salesStore.fetchPayoutList(newVal)
  } else {
    salesStore.payoutList = []
  }
})

onMounted(() => {
  if (project.value) {
    loadData(project.value)
  }
})

// 정산 실행 및 확정
const runGeneratePayouts = async () => {
  if (!selectedPeriodId.value) return
  if (confirm(`'${selectedPeriod.value?.title}' 정산 계산을 실행하시겠습니까?\n(대상 기간 내의 계약 실적 및 3.3% 원천세가 자동 집계됩니다)`)) {
    await salesStore.generatePayouts(selectedPeriodId.value)
    if (project.value) {
      await salesStore.fetchPeriodList(project.value)
      await salesStore.fetchPayoutList(selectedPeriodId.value)
    }
  }
}

const runConfirmSettlement = async () => {
  if (!selectedPeriodId.value) return
  if (confirm(`'${selectedPeriod.value?.title}' 정산을 확정하시겠습니까?\n(확정 후 지급 승인 및 이체 관리를 진행할 수 있습니다)`)) {
    await salesStore.confirmSettlement(selectedPeriodId.value)
    if (project.value) {
      await salesStore.fetchPeriodList(project.value)
    }
  }
}

const openCreatePeriod = () => periodModalRef.value?.open()
const openPayoutDetail = (payout: CommissionPayout) => detailModalRef.value?.open(payout)

const onPeriodSaved = async () => {
  if (project.value) {
    await salesStore.fetchPeriodList(project.value)
    if (periodList.value.length > 0) {
      selectedPeriodId.value = periodList.value[0].id
    }
  }
}
</script>

<template>
  <ContentHeader
    :page-title="pageTitle"
    :nav-menu="navMenu"
    selector="ProjectSelect"
    @proj-select="projSelect"
  />

  <ContentBody>
    <div v-if="!project" class="py-5 text-center text-muted">
      <v-icon icon="mdi-alert-circle-outline" size="large" class="mb-2 text-warning" />
      <h5>프로젝트를 먼저 선택해 주세요.</h5>
      <p class="mb-0 text-secondary">
        상단 프로젝트 선택 메뉴에서 관리하실 프로젝트를 선택하시면 수수료 정산을 관리할 수 있습니다.
      </p>
    </div>

    <div v-else>
      <!-- 회차 선택 및 액션 바 -->
      <CCard class="shadow-sm mb-4">
        <CCardBody class="py-3 d-flex flex-wrap justify-content-between align-items-center gap-3">
          <!-- 좌측: 회차 선택 셀렉터 -->
          <div class="d-flex align-items-center gap-2">
            <span class="fw-bold text-dark text-nowrap">
              <v-icon icon="mdi-calendar-range" size="small" class="mr-1 text-primary" />
              정산 회차:
            </span>
            <CFormSelect v-model.number="selectedPeriodId" style="min-width: 280px">
              <option :value="null">정산 회차를 선택하세요</option>
              <option v-for="p in periodList" :key="p.id" :value="p.id">
                [{{ p.status_display }}] {{ p.title }} ({{ p.start_date }} ~ {{ p.end_date }})
              </option>
            </CFormSelect>

            <CBadge
              v-if="selectedPeriod"
              :color="selectedPeriod.status === '2' ? 'primary' : (selectedPeriod.status === '3' ? 'success' : 'warning')"
              class="px-2 py-1"
            >
              {{ selectedPeriod.status_display }}
            </CBadge>
          </div>

          <!-- 우측: 액션 버튼 그룹 -->
          <div class="d-flex align-items-center gap-2">
            <v-btn color="secondary" size="small" variant="tonal" @click="openCreatePeriod">
              <v-icon icon="mdi-plus" size="small" class="mr-1" />
              신규 회차 생성
            </v-btn>

            <v-btn
              v-if="selectedPeriod"
              color="primary"
              size="small"
              @click="runGeneratePayouts"
            >
              <v-icon icon="mdi-calculator-variant" size="small" class="mr-1" />
              수수료 자동 정산 실행
            </v-btn>

            <v-btn
              v-if="selectedPeriod && selectedPeriod.status === '1'"
              color="success"
              size="small"
              @click="runConfirmSettlement"
            >
              <v-icon icon="mdi-check-all" size="small" class="mr-1" />
              정산 확정
            </v-btn>
          </div>
        </CCardBody>
      </CCard>

      <!-- 정산 총괄 요약 카드 -->
      <CRow v-if="selectedPeriod" class="mb-4 g-3">
        <!-- 정산 계약 건수 -->
        <CCol sm="6" lg="3">
          <CCard class="shadow-sm h-100 border-start border-start-4 border-start-primary">
            <CCardBody>
              <div class="text-body-secondary small fw-semibold">정산 계약 건수</div>
              <div class="fs-4 fw-bold text-primary">{{ selectedPeriod.total_contracts.toLocaleString() }}건</div>
              <div class="small text-muted">{{ selectedPeriod.start_date }} ~ {{ selectedPeriod.end_date }}</div>
            </CCardBody>
          </CCard>
        </CCol>

        <!-- 총 지급액 (세전) -->
        <CCol sm="6" lg="3">
          <CCard class="shadow-sm h-100 border-start border-start-4 border-start-info">
            <CCardBody>
              <div class="text-body-secondary small fw-semibold">총 지급액 (세전)</div>
              <div class="fs-4 fw-bold text-dark">{{ selectedPeriod.total_gross_amount.toLocaleString() }}원</div>
              <div class="small text-muted">인센티브 + 일비 - 공제액</div>
            </CCardBody>
          </CCard>
        </CCol>

        <!-- 원천징수 세액 (3.3%) -->
        <CCol sm="6" lg="3">
          <CCard class="shadow-sm h-100 border-start border-start-4 border-start-danger">
            <CCardBody>
              <div class="text-body-secondary small fw-semibold">원천징수 세액 (3.3%)</div>
              <div class="fs-4 fw-bold text-danger">{{ selectedPeriod.total_tax_amount.toLocaleString() }}원</div>
              <div class="small text-muted">소득세 3% + 지방소득세 0.3%</div>
            </CCardBody>
          </CCard>
        </CCol>

        <!-- 총 실지급액 (세후) -->
        <CCol sm="6" lg="3">
          <CCard class="shadow-sm h-100 border-start border-start-4 border-start-success">
            <CCardBody>
              <div class="text-body-secondary small fw-semibold">총 실지급액 (세후)</div>
              <div class="fs-4 fw-bold text-success">{{ selectedPeriod.total_net_amount.toLocaleString() }}원</div>
              <div class="small text-muted">예정일: {{ selectedPeriod.payout_date || '미정' }}</div>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>

      <!-- 개인별 수수료 지급 명세 테이블 -->
      <CCard v-if="selectedPeriod" class="shadow-sm mb-4">
        <CCardHeader class="bg-light d-flex justify-content-between align-items-center py-2">
          <div class="fw-bold d-flex align-items-center">
            <v-icon icon="mdi-format-list-numbered" size="small" class="mr-1 text-primary" />
            개인별 정산 및 세금 공제 명세
            <CBadge color="primary" class="ml-2" shape="rounded-pill">
              {{ payoutList.length }}명
            </CBadge>
          </div>
        </CCardHeader>

        <CCardBody class="p-0">
          <CTable hover responsive bordered align="middle" class="mb-0 text-center text-body small">
            <colgroup>
              <col style="width: 10%" />
              <col style="width: 8%" />
              <col style="width: 9%" />
              <col style="width: 7%" />
              <col style="width: 10%" />
              <col style="width: 8%" />
              <col style="width: 8%" />
              <col style="width: 10%" />
              <col style="width: 8%" />
              <col style="width: 10%" />
              <col style="width: 6%" />
              <col style="width: 6%" />
            </colgroup>
            <CTableHead :color="TableSecondary">
              <CTableRow>
                <CTableHeaderCell>소속 팀</CTableHeaderCell>
                <CTableHeaderCell>직책</CTableHeaderCell>
                <CTableHeaderCell>성명</CTableHeaderCell>
                <CTableHeaderCell>건수</CTableHeaderCell>
                <CTableHeaderCell>인센티브</CTableHeaderCell>
                <CTableHeaderCell>기본급/일비</CTableHeaderCell>
                <CTableHeaderCell>공제/환수</CTableHeaderCell>
                <CTableHeaderCell>총액 (세전)</CTableHeaderCell>
                <CTableHeaderCell>원천세 (3.3%)</CTableHeaderCell>
                <CTableHeaderCell class="table-primary">실지급액 (세후)</CTableHeaderCell>
                <CTableHeaderCell>상태</CTableHeaderCell>
                <CTableHeaderCell>상세</CTableHeaderCell>
              </CTableRow>
            </CTableHead>

            <CTableBody>
              <CTableRow v-for="payout in payoutList" :key="payout.id">
                <CTableDataCell class="small">{{ payout.team_name }}</CTableDataCell>
                <CTableDataCell>
                  <span class="badge bg-secondary">{{ payout.duty_display }}</span>
                </CTableDataCell>
                <CTableDataCell class="fw-bold">
                  <a href="javascript:void(0);" class="text-primary text-decoration-none" @click="openPayoutDetail(payout)">
                    {{ payout.sales_person_name }}
                  </a>
                </CTableDataCell>
                <CTableDataCell class="font-monospace">{{ payout.contract_count }}건</CTableDataCell>
                <CTableDataCell class="text-right font-monospace">{{ payout.commission_amount.toLocaleString() }}원</CTableDataCell>
                <CTableDataCell class="text-right font-monospace">{{ payout.base_pay.toLocaleString() }}원</CTableDataCell>
                <CTableDataCell class="text-right font-monospace text-danger">
                  <span v-if="payout.deduction_amount > 0">-{{ payout.deduction_amount.toLocaleString() }}원</span>
                  <span v-else class="text-muted">0원</span>
                </CTableDataCell>
                <CTableDataCell class="text-right font-monospace fw-bold">{{ payout.gross_amount.toLocaleString() }}원</CTableDataCell>
                <CTableDataCell class="text-right font-monospace text-danger">{{ payout.total_tax.toLocaleString() }}원</CTableDataCell>
                <CTableDataCell class="text-right font-monospace fw-bold text-primary table-primary">
                  {{ payout.net_amount.toLocaleString() }}원
                </CTableDataCell>
                <CTableDataCell>
                  <CBadge :color="payout.pay_status === '3' ? 'success' : (payout.pay_status === '2' ? 'primary' : 'secondary')">
                    {{ payout.pay_status_display }}
                  </CBadge>
                </CTableDataCell>
                <CTableDataCell>
                  <v-btn size="x-small" variant="tonal" color="info" @click="openPayoutDetail(payout)">
                    보기
                  </v-btn>
                </CTableDataCell>
              </CTableRow>

              <CTableRow v-if="payoutList.length === 0">
                <CTableDataCell colspan="12" class="py-5 text-center text-muted">
                  정산된 수수료 명세가 없습니다. 상단의 [수수료 자동 정산 실행]을 눌러 계약 실적을 집계하세요.
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </CCardBody>
      </CCard>

      <div v-else class="py-5 text-center text-muted">
        <v-icon icon="mdi-calendar-blank" size="large" class="mb-2 text-secondary" />
        <h5>등록된 정산 회차가 없습니다.</h5>
        <p class="mb-0 text-secondary">
          상단의 [신규 회차 생성] 버튼을 눌러 정산 회차(월별/주기별)를 먼저 생성해 주세요.
        </p>
      </div>
    </div>

    <!-- 모달 다이얼로그들 -->
    <PeriodFormModal
      v-if="project"
      ref="periodModalRef"
      :project="project"
      @saved="onPeriodSaved"
    />

    <PayoutDetailModal
      ref="detailModalRef"
    />
  </ContentBody>
</template>
