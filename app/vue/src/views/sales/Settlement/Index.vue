<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { pageTitle, useSalesNavMenu } from '@/views/sales/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useSales } from '@/store/pinia/sales'
import { bgLight, TableSecondary } from '@/utils/cssMixins'
import type { Project } from '@/store/types/project'
import type { CommissionPayout, OrgHealthCheckResult } from '@/store/types/sales'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import SalesAuthGuard from '@/components/AuthGuard/SalesAuthGuard.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import PeriodFormModal from './components/PeriodFormModal.vue'
import PayoutDetailModal from './components/PayoutDetailModal.vue'

const refSettlement = ref()
const refConfirmSettlement = ref()
const refDeletePeriod = ref()

const router = useRouter()
const { can, PERM } = usePerms()
const projStore = useProject()
const project = computed(() => (projStore.project as Project | null)?.pk)
const navMenu = useSalesNavMenu(project)
const canSalesSettle = computed(() =>
  project.value ? can(PERM.SALES_SETTLE, project.value) : can(PERM.SALES_SETTLE),
)
const canSalesPayout = computed(() =>
  project.value ? can(PERM.SALES_PAYOUT, project.value) : can(PERM.SALES_PAYOUT),
)

const salesStore = useSales()
const periodList = computed(() => salesStore.periodList)
const payoutList = computed(() => salesStore.payoutList)
const agencyPayoutList = computed(() => salesStore.agencyPayoutList)
const clawbackList = computed(() => salesStore.clawbackList)

// 팀장/본부장 부재로 대행사(시행사)에 귀속된 이익 총액
const totalUnallocatedFee = computed(() =>
  agencyPayoutList.value.reduce((sum, ap) => sum + (ap.unallocated_fee || 0), 0),
)

const selectedPeriodId = ref<number | null>(null)
const selectedPeriod = computed(
  () => periodList.value.find(p => p.id === selectedPeriodId.value) || null,
)

const periodModalRef = ref()
const detailModalRef = ref()

// 조직 건강성 사전 진단 결과
const orgHealthResult = ref<OrgHealthCheckResult | null>(null)
const isCheckingHealth = ref(false)
const isMutating = ref(false)

const resetState = () => {
  selectedPeriodId.value = null
  orgHealthResult.value = null
  salesStore.periodList = []
  salesStore.payoutList = []
  salesStore.agencyPayoutList = []
  salesStore.clawbackList = []
}

const loadData = async (projId: number) => {
  await Promise.all([salesStore.fetchPeriodList(projId), salesStore.fetchClawbackList(undefined, projId)])
  if (periodList.value.length > 0) {
    if (!selectedPeriodId.value || !periodList.value.some(p => p.id === selectedPeriodId.value)) {
      selectedPeriodId.value = periodList.value[0].id
    } else {
      await Promise.all([
        salesStore.fetchPayoutList(selectedPeriodId.value),
        salesStore.fetchAgencyPayoutList(selectedPeriodId.value),
      ])
    }
  } else {
    selectedPeriodId.value = null
    salesStore.payoutList = []
    salesStore.agencyPayoutList = []
  }
}

watch(
  project,
  (newVal, oldVal) => {
    if (newVal !== oldVal) {
      resetState()
    }
    if (newVal && canSalesSettle.value) {
      loadData(newVal)
    } else if (!newVal) {
      resetState()
    }
  },
  { immediate: true },
)

watch(selectedPeriodId, async newVal => {
  if (newVal) {
    await Promise.all([
      salesStore.fetchPayoutList(newVal),
      salesStore.fetchAgencyPayoutList(newVal),
    ])
  } else {
    salesStore.payoutList = []
    salesStore.agencyPayoutList = []
  }
})

// 정산 실행 및 확정
const runGeneratePayouts = async () => {
  if (!selectedPeriodId.value || !project.value || selectedPeriod.value?.status !== '1') return
  isCheckingHealth.value = true
  try {
    const result = await salesStore.validateOrgHealth(project.value)
    orgHealthResult.value = result ?? null
  } finally {
    isCheckingHealth.value = false
  }
  refSettlement.value?.callModal()
}

const executeSettlement = async () => {
  if (!selectedPeriodId.value || isMutating.value) return
  refSettlement.value?.close()
  isMutating.value = true
  try {
    const ok = await salesStore.generatePayouts(selectedPeriodId.value)
    if (!ok) return
    if (project.value) {
      await Promise.all([
        salesStore.fetchPeriodList(project.value),
        salesStore.fetchPayoutList(selectedPeriodId.value),
        salesStore.fetchAgencyPayoutList(selectedPeriodId.value),
        salesStore.fetchClawbackList(undefined, project.value),
      ])
    }
  } finally {
    isMutating.value = false
  }
}

const goToPayout = () => {
  if (selectedPeriodId.value) {
    router.push({ path: '/sales/payout', query: { period: String(selectedPeriodId.value) } })
  } else {
    router.push('/sales/payout')
  }
}

const runConfirmSettlement = () => {
  if (!selectedPeriodId.value || selectedPeriod.value?.status !== '1') return
  refConfirmSettlement.value?.callModal()
}

const executeConfirmSettlement = async () => {
  if (!selectedPeriodId.value || isMutating.value) return
  refConfirmSettlement.value?.close()
  isMutating.value = true
  try {
    const ok = await salesStore.confirmSettlement(selectedPeriodId.value)
    if (!ok) return
    if (project.value) {
      await salesStore.fetchPeriodList(project.value)
    }
    if (canSalesPayout.value) {
      goToPayout()
    }
  } finally {
    isMutating.value = false
  }
}

const openCreatePeriod = () => {
  if (!canSalesSettle.value) return
  periodModalRef.value?.open()
}

const openEditPeriod = () => {
  if (!canSalesSettle.value || !selectedPeriod.value || selectedPeriod.value.status !== '1') return
  periodModalRef.value?.open(selectedPeriod.value)
}

const runDeletePeriod = () => {
  if (!canSalesSettle.value || !selectedPeriod.value || selectedPeriod.value.status !== '1') return
  refDeletePeriod.value?.callModal()
}

const executeDeletePeriod = async () => {
  if (!selectedPeriodId.value || isMutating.value) return
  refDeletePeriod.value?.close()
  isMutating.value = true
  try {
    const ok = await salesStore.deletePeriod(selectedPeriodId.value)
    if (!ok) return
    selectedPeriodId.value = null
    if (project.value) {
      await loadData(project.value)
    }
  } finally {
    isMutating.value = false
  }
}

const openPayoutDetail = (payout: CommissionPayout) => detailModalRef.value?.open(payout)

const onPeriodSaved = async () => {
  if (project.value) {
    const prevId = selectedPeriodId.value
    await salesStore.fetchPeriodList(project.value)
    if (periodList.value.length > 0) {
      selectedPeriodId.value =
        prevId && periodList.value.some(p => p.id === prevId) ? prevId : periodList.value[0].id
    }
  }
}
</script>

<template>
  <SalesAuthGuard :project="project" :required-perm="PERM.SALES_SETTLE">
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <CCardBody class="p-3 p-md-4 pb-5">
        <div v-if="!project" class="py-5 text-center text-muted">
          <v-icon icon="mdi-alert-circle-outline" size="large" class="mb-2 text-warning" />
          <h5>프로젝트를 먼저 선택해 주세요.</h5>
          <p class="mb-0 text-secondary">
            상단 프로젝트 선택 메뉴에서 관리하실 프로젝트를 선택하시면 수수료 정산을 관리할 수
            있습니다.
          </p>
        </div>

        <div v-else>
          <!-- 회차 선택 및 액션 바 -->
          <CCard class="shadow-sm mb-4">
            <CCardBody
              class="py-3 d-flex flex-wrap justify-content-between align-items-center gap-3"
            >
              <!-- 좌측: 회차 선택 셀렉터 -->
              <div class="d-flex align-items-center gap-2">
                <span class="fw-bold text-primary text-nowrap">
                  <v-icon icon="mdi-calendar-range" size="small" class="me-1 text-primary" />
                  정산 회차:
                </span>
                <CFormSelect
                  :model-value="selectedPeriodId ? String(selectedPeriodId) : ''"
                  style="min-width: 240px"
                  @update:model-value="
                    val => (selectedPeriodId = val && !Array.isArray(val) ? Number(val) : null)
                  "
                >
                  <option value="">정산 회차를 선택하세요</option>
                  <option v-for="p in periodList" :key="p.id" :value="String(p.id)">
                    [{{ p.status_display }}] {{ p.title }} ({{ p.start_date }} ~ {{ p.end_date }})
                  </option>
                </CFormSelect>

                <v-chip
                  v-if="selectedPeriod"
                  :color="
                    selectedPeriod.status === '2'
                      ? 'info'
                      : selectedPeriod.status === '3'
                        ? 'success'
                        : 'warning'
                  "
                  variant="flat"
                  size="x-small"
                  class="px-2 py-1"
                >
                  {{ selectedPeriod.status_display }}
                </v-chip>
              </div>

              <!-- 우측: 액션 버튼 그룹 -->
              <div class="d-flex flex-wrap align-items-center gap-2">
                <v-btn
                  v-if="canSalesSettle"
                  color="primary"
                  size="small"
                  :disabled="isMutating"
                  @click="openCreatePeriod"
                >
                  <v-icon icon="mdi-plus" size="small" class="me-1" />
                  신규 회차 생성
                </v-btn>

                <v-btn
                  v-if="selectedPeriod && selectedPeriod.status === '1' && canSalesSettle"
                  color="secondary"
                  variant="outlined"
                  size="small"
                  :disabled="isMutating"
                  @click="openEditPeriod"
                >
                  <v-icon icon="mdi-pencil" size="small" class="me-1" />
                  회차 수정
                </v-btn>

                <v-btn
                  v-if="selectedPeriod && selectedPeriod.status === '1' && canSalesSettle"
                  color="danger"
                  variant="outlined"
                  size="small"
                  :disabled="isMutating"
                  @click="runDeletePeriod"
                >
                  <v-icon icon="mdi-delete" size="small" class="me-1" />
                  회차 삭제
                </v-btn>

                <v-btn
                  v-if="selectedPeriod && selectedPeriod.status === '1' && canSalesSettle"
                  color="info"
                  size="small"
                  :loading="isCheckingHealth || isMutating"
                  :disabled="isCheckingHealth || isMutating"
                  @click="runGeneratePayouts"
                >
                  <v-icon icon="mdi-calculator-variant" size="small" class="me-1" />
                  수수료 자동 정산 실행
                </v-btn>

                <v-btn
                  v-if="selectedPeriod && selectedPeriod.status === '1' && canSalesSettle"
                  color="success"
                  size="small"
                  :disabled="isMutating"
                  @click="runConfirmSettlement"
                >
                  <v-icon icon="mdi-check-all" size="small" class="me-1" />
                  정산 확정
                </v-btn>

                <v-btn
                  v-if="selectedPeriod && selectedPeriod.status !== '1' && canSalesPayout"
                  color="secondary"
                  variant="outlined"
                  size="small"
                  @click="goToPayout"
                >
                  <v-icon icon="mdi-arrow-right-circle-outline" size="small" class="me-1" />
                  수수료 지급 관리로 이동
                </v-btn>
              </div>
            </CCardBody>
          </CCard>

          <!-- 정산 총괄 요약 카드 (1줄 4개 구성) -->
          <CRow v-if="selectedPeriod" class="mb-4 g-3">
            <!-- 1. 운영인력 지급 총액 (세전) -->
            <CCol sm="6" lg="3">
              <CCard class="shadow-sm h-100 border-start border-start-4 border-start-primary">
                <CCardBody>
                  <div class="text-body-secondary small fw-semibold">
                    운영인력 지급 총액 (세전)
                  </div>
                  <div class="fs-4 fw-bold text-primary">
                    {{ (selectedPeriod.total_gross_amount || 0).toLocaleString() }}원
                  </div>
                  <div class="small text-muted">
                    인센티브 + 일비 - 공제 ({{ payoutList.length }}명)
                  </div>
                </CCardBody>
              </CCard>
            </CCol>

            <!-- 2. 원천징수 세액 (3.3%) -->
            <CCol sm="6" lg="3">
              <CCard class="shadow-sm h-100 border-start border-start-4 border-start-danger">
                <CCardBody>
                  <div class="text-body-secondary small fw-semibold">원천징수 세액 (3.3%)</div>
                  <div class="fs-4 fw-bold text-danger">
                    {{ (selectedPeriod.total_tax_amount || 0).toLocaleString() }}원
                  </div>
                  <div class="small text-muted">소득세 3% + 지방소득세 0.3%</div>
                </CCardBody>
              </CCard>
            </CCol>

            <!-- 3. 인력 총 실지급액 (세후) -->
            <CCol sm="6" lg="3">
              <CCard class="shadow-sm h-100 border-start border-start-4 border-start-success">
                <CCardBody>
                  <div class="text-body-secondary small fw-semibold">인력 총 실지급액 (세후)</div>
                  <div class="fs-4 fw-bold text-success">
                    {{ (selectedPeriod.total_net_amount || 0).toLocaleString() }}원
                  </div>
                  <div class="small text-muted">
                    지급 예정일: {{ selectedPeriod.payout_date || '미정' }}
                  </div>
                </CCardBody>
              </CCard>
            </CCol>

            <!-- 4. 시행사 청구 금액 (VAT 포함) -->
            <CCol sm="6" lg="3">
              <CCard
                class="shadow-sm h-100 border-start border-start-4 border-start-warning bg-more-light"
              >
                <CCardBody>
                  <div class="d-flex justify-content-between align-items-center mb-1">
                    <div class="text-body-secondary small fw-semibold">시행사 청구 금액</div>
                    <span class="badge bg-warning text-body small px-1">VAT 포함</span>
                  </div>
                  <div class="fs-4 fw-bold text-body">
                    {{
                      (
                        selectedPeriod.billing_total_amount ||
                        Math.floor((selectedPeriod.billing_supply_price || 0) * 1.1)
                      ).toLocaleString()
                    }}원
                  </div>
                  <div class="small text-muted">
                    총 {{ (selectedPeriod.total_contracts || 0).toLocaleString() }}건 (공급가:
                    {{
                      (
                        selectedPeriod.billing_supply_price ||
                        selectedPeriod.total_gross_amount ||
                        0
                      ).toLocaleString()
                    }}원)
                  </div>
                  <div v-if="totalUnallocatedFee > 0" class="mt-1 small text-info fw-semibold">
                    <v-icon icon="mdi-information-outline" size="x-small" class="me-1" />
                    팀장/본부장 미배정 귀속 이익: {{ totalUnallocatedFee.toLocaleString() }}원
                  </div>
                </CCardBody>
              </CCard>
            </CCol>
          </CRow>

          <!-- 개인별 수수료 지급 명세 테이블 -->
          <CCard v-if="selectedPeriod" class="shadow-sm mb-4">
            <CCardHeader
              :class="bgLight"
              class="d-flex justify-content-between align-items-center py-2"
            >
              <div class="fw-bold d-flex align-items-center">
                <v-icon icon="mdi-format-list-numbered" size="small" class="me-1 text-primary" />
                개인별 정산 및 세금 공제 명세
                <v-chip color="info" variant="flat" size="x-small" class="ms-2">
                  {{ payoutList.length }}명
                </v-chip>
              </div>
            </CCardHeader>

            <CCardBody class="p-0">
              <CTable
                hover
                responsive
                bordered
                align="middle"
                class="mb-0 text-center text-body small"
              >
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
                    <CTableHeaderCell>실지급액 (세후)</CTableHeaderCell>
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
                      <a
                        href="#"
                        class="text-primary text-decoration-none"
                        @click.prevent="openPayoutDetail(payout)"
                      >
                        {{ payout.sales_person_name }}
                      </a>
                    </CTableDataCell>
                    <CTableDataCell class="font-monospace">
                      {{ payout.contract_count }}건
                    </CTableDataCell>
                    <CTableDataCell class="text-end font-monospace">
                      {{ payout.commission_amount.toLocaleString() }}원
                    </CTableDataCell>
                    <CTableDataCell class="text-end font-monospace">
                      {{ payout.base_pay.toLocaleString() }}원
                    </CTableDataCell>
                    <CTableDataCell class="text-end font-monospace text-danger">
                      <span v-if="payout.deduction_amount > 0">
                        -{{ payout.deduction_amount.toLocaleString() }}원
                      </span>
                      <span v-else class="text-muted">0원</span>
                    </CTableDataCell>
                    <CTableDataCell class="text-end font-monospace fw-bold">
                      {{ payout.gross_amount.toLocaleString() }}원
                    </CTableDataCell>
                    <CTableDataCell class="text-end font-monospace text-danger">
                      {{ payout.total_tax.toLocaleString() }}원
                    </CTableDataCell>
                    <CTableDataCell class="text-end font-monospace fw-bold text-primary">
                      {{ payout.net_amount.toLocaleString() }}원
                    </CTableDataCell>
                    <CTableDataCell>
                      <v-chip
                        :color="
                          payout.pay_status === '3'
                            ? 'success'
                            : payout.pay_status === '2'
                              ? 'info'
                              : 'secondary'
                        "
                        variant="flat"
                        size="x-small"
                      >
                        {{ payout.pay_status_display }}
                      </v-chip>
                    </CTableDataCell>
                    <CTableDataCell>
                      <v-btn size="x-small" color="info" @click="openPayoutDetail(payout)">
                        보기
                      </v-btn>
                    </CTableDataCell>
                  </CTableRow>

                  <CTableRow v-if="payoutList.length === 0">
                    <CTableDataCell colspan="12" class="py-5 text-center text-muted">
                      정산된 수수료 명세가 없습니다.<template v-if="selectedPeriod?.status === '1'">
                        상단의 [수수료 자동 정산 실행]을 눌러 계약 실적을 집계하세요.</template
                      >
                    </CTableDataCell>
                  </CTableRow>
                </CTableBody>
              </CTable>
            </CCardBody>
          </CCard>

          <!-- 대행사 단위 정산 및 귀속 이익 명세 테이블 -->
          <CCard v-if="selectedPeriod && agencyPayoutList.length > 0" class="shadow-sm mb-4">
            <CCardHeader
              :class="bgLight"
              class="d-flex justify-content-between align-items-center py-2"
            >
              <div class="fw-bold d-flex align-items-center">
                <v-icon icon="mdi-domain" size="small" class="me-1 text-primary" />
                대행사 정산 및 귀속 이익 명세
                <v-chip color="info" variant="flat" size="x-small" class="ms-2">
                  {{ agencyPayoutList.length }}개사
                </v-chip>
              </div>
              <div v-if="totalUnallocatedFee > 0" class="small text-info fw-semibold">
                <v-icon icon="mdi-shield-check" size="small" class="me-1" />
                총 귀속 이익: {{ totalUnallocatedFee.toLocaleString() }}원
              </div>
            </CCardHeader>

            <CCardBody class="p-0">
              <CTable
                hover
                responsive
                bordered
                align="middle"
                class="mb-0 text-center text-body small"
              >
                <colgroup>
                  <col style="width: 15%" />
                  <col style="width: 10%" />
                  <col style="width: 8%" />
                  <col style="width: 14%" />
                  <col style="width: 14%" />
                  <col style="width: 12%" />
                  <col style="width: 14%" />
                  <col style="width: 13%" />
                </colgroup>
                <CTableHead :color="TableSecondary">
                  <CTableRow>
                    <CTableHeaderCell>대행사명</CTableHeaderCell>
                    <CTableHeaderCell>운영 구분</CTableHeaderCell>
                    <CTableHeaderCell>계약 건수</CTableHeaderCell>
                    <CTableHeaderCell>수수료 합계 (공급가)</CTableHeaderCell>
                    <CTableHeaderCell class="text-info">귀속 이익 (미배정 fee)</CTableHeaderCell>
                    <CTableHeaderCell>부가세 (10%)</CTableHeaderCell>
                    <CTableHeaderCell>총 정산액 (VAT 포함)</CTableHeaderCell>
                    <CTableHeaderCell>비고</CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  <CTableRow v-for="ap in agencyPayoutList" :key="ap.id">
                    <CTableDataCell class="fw-bold text-start ps-3">
                      {{ ap.agency_name }}
                    </CTableDataCell>
                    <CTableDataCell>
                      <v-chip
                        :color="ap.is_direct_managed ? 'info' : 'success'"
                        variant="flat"
                        size="x-small"
                      >
                        {{ ap.is_direct_managed ? '직영 사업부' : '외주 대행' }}
                      </v-chip>
                    </CTableDataCell>
                    <CTableDataCell class="font-monospace">
                      {{ ap.contract_count }}건
                    </CTableDataCell>
                    <CTableDataCell class="text-end font-monospace">
                      {{ ap.agency_fee_sum.toLocaleString() }}원
                    </CTableDataCell>
                    <CTableDataCell class="text-end font-monospace text-info fw-bold">
                      <span v-if="(ap.unallocated_fee || 0) > 0">
                        {{ (ap.unallocated_fee || 0).toLocaleString() }}원
                      </span>
                      <span v-else class="text-muted">-</span>
                    </CTableDataCell>
                    <CTableDataCell class="text-end font-monospace">
                      {{ ap.vat_amount.toLocaleString() }}원
                    </CTableDataCell>
                    <CTableDataCell class="text-end font-monospace fw-bold">
                      {{ ap.total_amount.toLocaleString() }}원
                    </CTableDataCell>
                    <CTableDataCell class="text-start small text-muted">
                      {{ ap.note || '-' }}
                    </CTableDataCell>
                  </CTableRow>
                </CTableBody>
              </CTable>
            </CCardBody>
          </CCard>

          <!-- 수수료 환수 이력 테이블 -->
          <CCard v-if="selectedPeriod && clawbackList.length > 0" class="shadow-sm mb-4">
            <CCardHeader
              :class="bgLight"
              class="d-flex justify-content-between align-items-center py-2"
            >
              <div class="fw-bold d-flex align-items-center">
                <v-icon icon="mdi-cash-refund" size="small" class="me-1 text-danger" />
                수수료 환수 이력
                <v-chip color="danger" variant="flat" size="x-small" class="ms-2">
                  {{ clawbackList.length }}건
                </v-chip>
                <v-chip
                  v-if="clawbackList.filter(c => !c.is_settled).length > 0"
                  color="warning"
                  variant="flat"
                  size="x-small"
                  class="ms-1"
                >
                  미상계 {{ clawbackList.filter(c => !c.is_settled).length }}건
                </v-chip>
              </div>
              <div class="small text-danger fw-semibold">
                총 환수액:
                {{ clawbackList.reduce((s, c) => s + (c.amount || 0), 0).toLocaleString() }}원
              </div>
            </CCardHeader>

            <CCardBody class="p-0">
              <CTable
                hover
                responsive
                bordered
                align="middle"
                class="mb-0 text-center text-body small"
              >
                <colgroup>
                  <col style="width: 10%" />
                  <col style="width: 12%" />
                  <col style="width: 10%" />
                  <col style="width: 12%" />
                  <col style="width: 30%" />
                  <col style="width: 10%" />
                  <col style="width: 16%" />
                </colgroup>
                <CTableHead :color="TableSecondary">
                  <CTableRow>
                    <CTableHeaderCell>해지 계약번호</CTableHeaderCell>
                    <CTableHeaderCell>환수 대상자</CTableHeaderCell>
                    <CTableHeaderCell>환수 금액</CTableHeaderCell>
                    <CTableHeaderCell>상계 여부</CTableHeaderCell>
                    <CTableHeaderCell>환수 사유</CTableHeaderCell>
                    <CTableHeaderCell>등록일</CTableHeaderCell>
                    <CTableHeaderCell>상계 처리 정산</CTableHeaderCell>
                  </CTableRow>
                </CTableHead>
                <CTableBody>
                  <CTableRow v-for="c in clawbackList" :key="c.id">
                    <CTableDataCell class="small font-monospace text-start ps-3">
                      {{ c.contract_serial || `#${c.contract}` }}
                    </CTableDataCell>
                    <CTableDataCell class="fw-bold">
                      {{ c.sales_person_name || `#${c.sales_person}` }}
                    </CTableDataCell>
                    <CTableDataCell class="text-end font-monospace text-danger fw-bold">
                      {{ c.amount.toLocaleString() }}원
                    </CTableDataCell>
                    <CTableDataCell>
                      <v-chip
                        :color="c.is_settled ? 'success' : 'warning'"
                        variant="flat"
                        size="x-small"
                      >
                        {{ c.is_settled ? '상계 완료' : '미상계' }}
                      </v-chip>
                    </CTableDataCell>
                    <CTableDataCell class="text-start small text-muted">{{
                      c.reason
                    }}</CTableDataCell>
                    <CTableDataCell class="small text-muted">
                      {{ c.created_at?.slice(0, 10) }}
                    </CTableDataCell>
                    <CTableDataCell class="small text-muted">
                      <span v-if="c.settled_payout">{{ c.settled_payout }}회차 상계</span>
                      <span v-else class="text-muted">-</span>
                    </CTableDataCell>
                  </CTableRow>
                </CTableBody>
              </CTable>
            </CCardBody>
          </CCard>

          <div v-if="!selectedPeriod" class="py-5 text-center text-muted">
            <v-icon icon="mdi-calendar-blank" size="large" class="mb-2 text-secondary" />
            <h5>등록된 정산 회차가 없습니다.</h5>
            <p class="mb-0 text-secondary">
              상단의 [신규 회차 생성] 버튼을 눌러 정산 회차(월별/주기별)를 먼저 생성해 주세요.
            </p>
          </div>
        </div>
      </CCardBody>

      <!-- 모달 다이얼로그들 -->
      <PeriodFormModal
        v-if="project"
        ref="periodModalRef"
        :project="project"
        @saved="onPeriodSaved"
      />

      <PayoutDetailModal ref="detailModalRef" />

      <!-- 수수료 자동 정산 실행 확인 모달 -->
      <ConfirmModal ref="refSettlement">
        <template #header>수수료 자동 정산 실행</template>
        <template #default>
          <p class="mb-2">
            <strong>[{{ selectedPeriod?.title }}]</strong> 정산 계산을 실행하시겠습니까?
          </p>

          <!-- 조직 건강성 사전 진단 경고 표시 -->
          <div v-if="orgHealthResult && !orgHealthResult.is_healthy" class="my-3">
            <CAlert color="warning" class="py-2 px-3 mb-2 small border-warning">
              <div class="fw-bold mb-1 d-flex align-items-center">
                <v-icon icon="mdi-alert" size="small" class="text-warning me-1" />
                조직/인력 구조 점검 결과 (주의 {{ orgHealthResult.warning_count }}건 / 오류
                {{ orgHealthResult.error_count }}건)
              </div>
              <ul class="mb-0 ps-3">
                <li v-for="(item, idx) in orgHealthResult.items" :key="idx" class="mt-1">
                  <span v-if="item.severity === 'error'" class="badge bg-danger me-1">오류</span>
                  <span v-else class="badge bg-warning text-body me-1">주의</span>
                  {{ item.message }}
                </li>
              </ul>
            </CAlert>
            <div class="small text-secondary mb-2">
              * 주의 항목(팀장 부재 등)은 상위 본부장 합산 수령 또는 대행사 귀속 이익으로 자동
              처리됩니다.
            </div>
          </div>

          <ul class="text-secondary small mb-0 ps-3">
            <li>계약일자 기준 정산 대상(승인 완료 건)을 집계합니다.</li>
            <li>기존 타 회차에서 이미 정산된 계약건은 자동으로 제외됩니다.</li>
            <li>수수료 정책에 따라 인력별 지급액 및 시행사 청구금액이 자동 산출됩니다.</li>
          </ul>
        </template>
        <template #footer>
          <v-btn size="small" color="primary" @click="executeSettlement">정산 실행</v-btn>
        </template>
      </ConfirmModal>

      <!-- 정산 회차 확정 확인 모달 -->
      <ConfirmModal ref="refConfirmSettlement">
        <template #header>정산 회차 확정</template>
        <template #default>
          <p class="mb-2">
            <strong>[{{ selectedPeriod?.title }}]</strong> 정산 회차를 <strong>[확정]</strong> 상태로
            변경하시겠습니까?
          </p>
          <ul class="text-secondary small mb-0 ps-3">
            <li>확정 후에는 정산 계산을 다시 실행할 수 없습니다.</li>
            <li v-if="canSalesPayout">
              확정 처리가 완료되면 [수수료 지급 관리] 화면으로 자동 이동합니다.
            </li>
          </ul>
        </template>
        <template #footer>
          <v-btn size="small" color="success" @click="executeConfirmSettlement">정산 확정</v-btn>
        </template>
      </ConfirmModal>

      <!-- 정산 회차 삭제 확인 모달 -->
      <ConfirmModal ref="refDeletePeriod">
        <template #header>정산 회차 삭제 확인</template>
        <template #default>
          <p class="mb-2">
            <strong>[{{ selectedPeriod?.title }}]</strong> 정산 회차를 삭제하시겠습니까?
          </p>
          <p class="text-danger small mb-0">
            * 정산 작성 중 회차의 지급 명세는 함께 삭제되며, 상계되었던 환수금은 미상계 상태로
            자동 복원됩니다.
          </p>
        </template>
        <template #footer>
          <v-btn size="small" color="danger" @click="executeDeletePeriod">회차 삭제</v-btn>
        </template>
      </ConfirmModal>
    </ContentBody>
  </SalesAuthGuard>
</template>
