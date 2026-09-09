<script lang="ts" setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { pageTitle, useSalesNavMenu } from '@/views/sales/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useSales } from '@/store/pinia/sales'
import type { Project } from '@/store/types/project'
import type { CommissionPayout, AgencyPayout } from '@/store/types/sales'
import { TableSecondary } from '@/utils/cssMixins'
import { usePerms } from '@/composables/usePerms'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PayoutStatusSummary from './components/PayoutStatusSummary.vue'
import PayoutDetailModal from '@/views/sales/Settlement/components/PayoutDetailModal.vue'
import PersonPayoutHistoryModal from './components/PersonPayoutHistoryModal.vue'

const route = useRoute()
const { can, PERM } = usePerms()
const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)
const navMenu = useSalesNavMenu(project)

const salesStore = useSales()
const periodList = computed(() => salesStore.periodList)
const payoutList = computed(() => salesStore.payoutList)
const agencyPayoutList = computed(() => salesStore.agencyPayoutList)

const selectedPeriodId = ref<number | null>(null)
const selectedPeriod = computed(
  () => periodList.value.find(p => p.id === selectedPeriodId.value) || null,
)

// 탭: 'person' | 'agency'
const activeTab = ref<'person' | 'agency'>('person')

// 개인 탭 필터 및 검색
const statusFilter = ref<string>('')
const searchQuery = ref<string>('')

// 대행사 탭 필터
const agencyStatusFilter = ref<string>('')
const agencySearchQuery = ref<string>('')

// 다중 선택 상태 (개인 탭)
const selectedPayoutIds = ref<number[]>([])
const isBatchLoading = ref<boolean>(false)

// 모달
const detailModalRef = ref()
const historyModalRef = ref()

// 데이터 로드
const loadData = async (projId: number) => {
  await salesStore.fetchPeriodList(projId)
  if (periodList.value.length > 0) {
    const queryPeriod = Number(route.query.period)
    if (queryPeriod && periodList.value.some(p => p.id === queryPeriod)) {
      selectedPeriodId.value = queryPeriod
    } else if (
      !selectedPeriodId.value ||
      !periodList.value.some(p => p.id === selectedPeriodId.value)
    ) {
      selectedPeriodId.value = periodList.value[0].id
    }
    await Promise.all([
      salesStore.fetchPayoutList(selectedPeriodId.value),
      salesStore.fetchAgencyPayoutList(selectedPeriodId.value),
    ])
  } else {
    selectedPeriodId.value = null
    salesStore.payoutList = []
    salesStore.agencyPayoutList = []
  }
  selectedPayoutIds.value = []
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
  selectedPayoutIds.value = []
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

onMounted(() => {
  if (project.value) {
    loadData(project.value)
  }
})

// ─── 개인 탭 ─────────────────────────────────────────────
const filteredPayouts = computed(() => {
  let list = payoutList.value
  if (statusFilter.value) {
    list = list.filter(p => p.pay_status === statusFilter.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(
      p =>
        (p.sales_person_name && p.sales_person_name.toLowerCase().includes(q)) ||
        (p.team_name && p.team_name.toLowerCase().includes(q)) ||
        (p.account_holder && p.account_holder.toLowerCase().includes(q)) ||
        (p.bank_name && p.bank_name.toLowerCase().includes(q)) ||
        (p.account_number && p.account_number.includes(q)),
    )
  }
  return list
})

const isAllSelected = computed(() => {
  if (filteredPayouts.value.length === 0) return false
  return filteredPayouts.value.every(p => selectedPayoutIds.value.includes(p.id))
})

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedPayoutIds.value = []
  } else {
    selectedPayoutIds.value = filteredPayouts.value.map(p => p.id)
  }
}

const toggleSelect = (id: number) => {
  const idx = selectedPayoutIds.value.indexOf(id)
  if (idx > -1) {
    selectedPayoutIds.value.splice(idx, 1)
  } else {
    selectedPayoutIds.value.push(id)
  }
}

const selectedTotalAmount = computed(() => {
  return filteredPayouts.value
    .filter(p => selectedPayoutIds.value.includes(p.id))
    .reduce((sum, p) => sum + (p.net_amount || 0), 0)
})

const changePayoutStatus = async (payout: CommissionPayout, newStatus: string) => {
  if (payout.pay_status === newStatus) return
  await salesStore.updatePayStatus(payout.id, newStatus)
  if (selectedPeriodId.value) {
    await salesStore.fetchPayoutList(selectedPeriodId.value)
  }
}

const batchUpdateStatus = async (targetStatus: string, label: string) => {
  if (selectedPayoutIds.value.length === 0) {
    alert('상태를 변경할 대상을 1명 이상 선택해 주세요.')
    return
  }
  const count = selectedPayoutIds.value.length
  if (!confirm(`선택한 ${count}명의 지급 상태를 [${label}] 상태로 일괄 변경하시겠습니까?`)) {
    return
  }
  isBatchLoading.value = true
  try {
    const promises = selectedPayoutIds.value.map(id => salesStore.updatePayStatus(id, targetStatus))
    await Promise.all(promises)
    if (selectedPeriodId.value) {
      await salesStore.fetchPayoutList(selectedPeriodId.value)
    }
    selectedPayoutIds.value = []
  } finally {
    isBatchLoading.value = false
  }
}

// 은행 이체용 CSV 다운로드
const downloadBankingCsv = () => {
  const targets =
    selectedPayoutIds.value.length > 0
      ? filteredPayouts.value.filter(p => selectedPayoutIds.value.includes(p.id))
      : filteredPayouts.value

  if (targets.length === 0) {
    alert('내보낼 지급 명세 내역이 없습니다.')
    return
  }

  const headers = [
    '순번', '입금은행', '입금계좌번호', '예금주', '실지급액(세후)',
    '세전총액', '원천세(3.3%)', '성명', '소속팀', '직책', '지급상태', '지급일자', '정산회차', '비고/메모',
  ]

  const rows = targets.map((p, index) => [
    index + 1,
    `"${p.bank_name || ''}"`,
    `"\t${p.account_number || ''}"`,
    `"${p.account_holder || ''}"`,
    p.net_amount,
    p.gross_amount,
    p.total_tax,
    `"${p.sales_person_name}"`,
    `"${p.team_name}"`,
    `"${p.duty_display}"`,
    `"${p.pay_status_display}"`,
    `"${p.paid_date || ''}"`,
    `"${selectedPeriod.value?.title || ''}"`,
    `"${(p.note || '').replace(/"/g, '""')}"`,
  ])

  const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\r\n')
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  const periodTitle = selectedPeriod.value?.title
    ? selectedPeriod.value.title.replace(/\s+/g, '_')
    : '수수료정산'
  const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  link.setAttribute('href', url)
  link.setAttribute('download', `은행이체명세_${periodTitle}_${dateStr}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const openPayoutDetail = (payout: CommissionPayout) => {
  detailModalRef.value?.open(payout)
}

const openPersonHistory = (payout: CommissionPayout) => {
  historyModalRef.value?.open(payout)
}

// ─── 대행사 탭 ──────────────────────────────────────────────
const filteredAgencyPayouts = computed(() => {
  let list = agencyPayoutList.value
  if (agencyStatusFilter.value) {
    list = list.filter(ap => ap.pay_status === agencyStatusFilter.value)
  }
  if (agencySearchQuery.value.trim()) {
    const q = agencySearchQuery.value.trim().toLowerCase()
    list = list.filter(
      ap =>
        (ap.agency_name && ap.agency_name.toLowerCase().includes(q)) ||
        (ap.business_number && ap.business_number.includes(q)) ||
        (ap.account_holder && ap.account_holder.toLowerCase().includes(q)),
    )
  }
  return list
})

const agencyTotalAmount = computed(() =>
  filteredAgencyPayouts.value.reduce((s, ap) => s + (ap.total_amount || 0), 0),
)
const agencyPaidAmount = computed(() =>
  filteredAgencyPayouts.value
    .filter(ap => ap.pay_status === '3')
    .reduce((s, ap) => s + (ap.total_amount || 0), 0),
)

const changeAgencyPayStatus = async (ap: AgencyPayout, newStatus: string) => {
  if (ap.pay_status === newStatus) return
  await salesStore.updateAgencyPayStatus(ap.id, newStatus)
  if (selectedPeriodId.value) {
    await salesStore.fetchAgencyPayoutList(selectedPeriodId.value)
  }
}

const agencyPayStatusColor = (status: string) => {
  if (status === '3') return 'text-success border-success'
  if (status === '2') return 'text-primary border-primary'
  if (status === '4') return 'text-warning border-warning'
  return 'text-secondary border-secondary'
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
    <CCardBody class="p-3 p-md-4 pb-5">
      <div v-if="!project" class="py-5 text-center text-muted">
        <v-icon icon="mdi-alert-circle-outline" size="large" class="mb-2 text-warning" />
        <h5>프로젝트를 먼저 선택해 주세요.</h5>
        <p class="mb-0 text-secondary">
          상단 프로젝트 선택 메뉴에서 관리하실 프로젝트를 선택하시면 수수료 지급 대장을 조회할 수
          있습니다.
        </p>
      </div>

      <div v-else>
        <!-- 회차 선택 및 필터 툴바 -->
        <CCard class="shadow-sm mb-4">
          <CCardBody class="py-3">
            <CRow class="g-3 align-items-center">
              <!-- 정산 회차 선택 -->
              <CCol md="4" lg="3">
                <div class="d-flex align-items-center gap-2">
                  <span class="fw-bold text-primary text-nowrap">
                    <v-icon icon="mdi-calendar-range" size="small" class="mr-1 text-primary" />
                    정산 회차:
                  </span>
                  <CFormSelect v-model.number="selectedPeriodId">
                    <option :value="null">회차를 선택하세요</option>
                    <option v-for="p in periodList" :key="p.id" :value="p.id">
                      [{{ p.status_display }}] {{ p.title }}
                    </option>
                  </CFormSelect>
                </div>
              </CCol>

              <!-- 탭 토글: 개인 | 대행사 -->
              <CCol md="5" lg="4">
                <div class="d-flex gap-2">
                  <v-btn
                    size="small"
                    :color="activeTab === 'person' ? 'primary' : 'secondary'"
                    :variant="activeTab === 'person' ? 'flat' : 'outlined'"
                    @click="activeTab = 'person'"
                  >
                    <v-icon icon="mdi-account-group" size="small" class="mr-1" />
                    개인 지급 명세
                    <CBadge color="light" text-color="dark" class="ml-1">{{ payoutList.length }}</CBadge>
                  </v-btn>
                  <v-btn
                    size="small"
                    :color="activeTab === 'agency' ? 'info' : 'secondary'"
                    :variant="activeTab === 'agency' ? 'flat' : 'outlined'"
                    @click="activeTab = 'agency'"
                  >
                    <v-icon icon="mdi-domain" size="small" class="mr-1" />
                    대행사 지급 명세
                    <CBadge color="light" text-color="dark" class="ml-1">{{ agencyPayoutList.length }}</CBadge>
                  </v-btn>
                </div>
              </CCol>

              <!-- 건수 -->
              <CCol md="3" lg="5" class="text-lg-end">
                <span v-if="activeTab === 'person'" class="small text-muted">
                  조회: <strong>{{ filteredPayouts.length }}</strong>명
                </span>
                <span v-else class="small text-muted">
                  조회: <strong>{{ filteredAgencyPayouts.length }}</strong>개사
                </span>
              </CCol>
            </CRow>
          </CCardBody>
        </CCard>

        <!-- ═══════════════════ 개인 탭 ═══════════════════ -->
        <template v-if="activeTab === 'person'">
          <!-- 지급 진행 현황 대시보드 요약 카드 -->
          <PayoutStatusSummary v-if="selectedPeriod" :payouts="payoutList" />

          <!-- 필터 바 + 일괄 작업 -->
          <CCard v-if="selectedPeriod" class="shadow-sm mb-4">
            <CCardHeader
              class="bg-light py-2 d-flex flex-wrap justify-content-between align-items-center gap-2"
            >
              <!-- 좌측: 필터 + 검색 -->
              <div class="d-flex align-items-center gap-2 flex-wrap">
                <!-- 상태 필터 -->
                <CFormSelect v-model="statusFilter" style="max-width: 130px">
                  <option value="">전체 상태</option>
                  <option value="1">지급대기</option>
                  <option value="2">지급승인</option>
                  <option value="3">지급완료</option>
                  <option value="4">지급보류</option>
                </CFormSelect>

                <!-- 검색 -->
                <CFormInput
                  v-model="searchQuery"
                  placeholder="성명, 팀, 계좌번호..."
                  style="max-width: 200px"
                />

                <!-- 다중 선택 -->
                <div class="form-check m-0">
                  <input
                    id="checkAll"
                    type="checkbox"
                    class="form-check-input"
                    :checked="isAllSelected"
                    @change="toggleSelectAll"
                  />
                  <label for="checkAll" class="form-check-label small fw-bold text-dark cursor-pointer">
                    전체 선택
                  </label>
                </div>

                <template v-if="selectedPayoutIds.length > 0">
                  <CBadge color="primary" class="px-2 py-1">
                    선택 {{ selectedPayoutIds.length }}명 ({{ selectedTotalAmount.toLocaleString() }}원)
                  </CBadge>

                  <template v-if="can(PERM.SALES_PAYOUT)">
                    <v-btn size="small" color="primary" variant="flat" :disabled="isBatchLoading" @click="batchUpdateStatus('2', '지급승인')">
                      <v-icon icon="mdi-check" size="small" class="mr-1" />선택 승인
                    </v-btn>
                    <v-btn size="small" color="success" variant="flat" :disabled="isBatchLoading" @click="batchUpdateStatus('3', '지급완료')">
                      <v-icon icon="mdi-cash-check" size="small" class="mr-1" />선택 지급완료
                    </v-btn>
                    <v-btn size="small" color="warning" variant="flat" :disabled="isBatchLoading" @click="batchUpdateStatus('4', '지급보류')">
                      <v-icon icon="mdi-pause-circle" size="small" class="mr-1" />선택 보류
                    </v-btn>
                  </template>

                  <v-btn size="small" color="secondary" variant="tonal" @click="selectedPayoutIds = []">
                    선택 해제
                  </v-btn>
                </template>
              </div>

              <!-- 우측: CSV 다운로드 -->
              <div class="d-flex align-items-center gap-2">
                <v-btn size="small" color="success" variant="flat" @click="downloadBankingCsv">
                  <v-icon icon="mdi-file-delimited" size="small" class="mr-1" />
                  은행 이체용 CSV
                  <span v-if="selectedPayoutIds.length > 0" class="ml-1">({{ selectedPayoutIds.length }}명)</span>
                </v-btn>
              </div>
            </CCardHeader>

            <!-- 개인 지급 명세 테이블 -->
            <CCardBody class="p-0">
              <CTable hover responsive bordered align="middle" class="mb-0 text-center text-body small">
                <colgroup>
                  <col style="width: 3%" />
                  <col style="width: 8%" />
                  <col style="width: 7%" />
                  <col style="width: 8%" />
                  <col style="width: 8%" />
                  <col style="width: 13%" />
                  <col style="width: 8%" />
                  <col style="width: 10%" />
                  <col style="width: 8%" />
                  <col style="width: 10%" />
                  <col style="width: 9%" />
                  <col style="width: 8%" />
                </colgroup>
                <CTableHead :color="TableSecondary">
                  <CTableRow>
                    <CTableHeaderCell class="p-2"></CTableHeaderCell>
                    <CTableHeaderCell>소속 팀</CTableHeaderCell>
                    <CTableHeaderCell>직책</CTableHeaderCell>
                    <CTableHeaderCell>성명</CTableHeaderCell>
                    <CTableHeaderCell>은행명</CTableHeaderCell>
                    <CTableHeaderCell>계좌번호</CTableHeaderCell>
                    <CTableHeaderCell>예금주</CTableHeaderCell>
                    <CTableHeaderCell>총액 (세전)</CTableHeaderCell>
                    <CTableHeaderCell>원천세 (3.3%)</CTableHeaderCell>
                    <CTableHeaderCell class="table-primary">실지급액 (세후)</CTableHeaderCell>
                    <CTableHeaderCell>지급 상태</CTableHeaderCell>
                    <CTableHeaderCell>이력/상세</CTableHeaderCell>
                  </CTableRow>
                </CTableHead>

                <CTableBody>
                  <CTableRow
                    v-for="payout in filteredPayouts"
                    :key="payout.id"
                    :class="{ 'table-active': selectedPayoutIds.includes(payout.id) }"
                  >
                    <!-- 체크박스 -->
                    <CTableDataCell class="p-2">
                      <input
                        type="checkbox"
                        class="form-check-input"
                        :checked="selectedPayoutIds.includes(payout.id)"
                        @change="toggleSelect(payout.id)"
                      />
                    </CTableDataCell>

                    <!-- 조직/인적 정보 -->
                    <CTableDataCell class="small">{{ payout.team_name }}</CTableDataCell>
                    <CTableDataCell>
                      <span class="badge bg-secondary">{{ payout.duty_display }}</span>
                    </CTableDataCell>
                    <CTableDataCell class="fw-bold">
                      <!-- 성명 클릭 → 누적 이력 모달 -->
                      <a
                        href="javascript:void(0);"
                        class="text-primary text-decoration-none"
                        @click="openPersonHistory(payout)"
                      >
                        {{ payout.sales_person_name }}
                      </a>
                    </CTableDataCell>

                    <!-- 계좌 정보 -->
                    <CTableDataCell class="fw-semibold">{{ payout.bank_name || '-' }}</CTableDataCell>
                    <CTableDataCell class="font-monospace text-left">{{ payout.account_number }}</CTableDataCell>
                    <CTableDataCell>{{ payout.account_holder }}</CTableDataCell>

                    <!-- 금액 정보 -->
                    <CTableDataCell class="text-right font-monospace">{{ payout.gross_amount.toLocaleString() }}원</CTableDataCell>
                    <CTableDataCell class="text-right font-monospace text-danger">{{ payout.total_tax.toLocaleString() }}원</CTableDataCell>
                    <CTableDataCell class="text-right font-monospace fw-bold text-primary table-primary">
                      {{ payout.net_amount.toLocaleString() }}원
                    </CTableDataCell>

                    <!-- 지급 상태 드롭다운 -->
                    <CTableDataCell>
                      <select
                        v-if="can(PERM.SALES_PAYOUT)"
                        :value="payout.pay_status"
                        class="form-select form-select-sm"
                        :class="{
                          'border-success text-success fw-bold': payout.pay_status === '3',
                          'border-primary text-primary fw-bold': payout.pay_status === '2',
                          'border-warning text-warning fw-bold': payout.pay_status === '4',
                          'border-secondary text-secondary': payout.pay_status === '1',
                        }"
                        @change="changePayoutStatus(payout, ($event.target as HTMLSelectElement).value)"
                      >
                        <option value="1">지급대기</option>
                        <option value="2">지급승인</option>
                        <option value="3">지급완료</option>
                        <option value="4">지급보류</option>
                      </select>
                      <CBadge
                        v-else
                        :color="payout.pay_status === '3' ? 'success' : payout.pay_status === '2' ? 'primary' : 'secondary'"
                      >
                        {{ payout.pay_status_display }}
                      </CBadge>
                      <div
                        v-if="payout.pay_status === '3' && payout.paid_date"
                        class="text-muted font-monospace"
                        style="font-size: 0.72rem"
                      >
                        {{ payout.paid_date }}
                      </div>
                    </CTableDataCell>

                    <!-- 이력/상세 버튼 -->
                    <CTableDataCell>
                      <div class="d-flex gap-1 justify-content-center">
                        <v-btn size="x-small" variant="tonal" color="secondary" @click="openPersonHistory(payout)" title="전 회차 이력">
                          <v-icon icon="mdi-history" size="x-small" />
                        </v-btn>
                        <v-btn size="x-small" variant="tonal" color="info" @click="openPayoutDetail(payout)" title="이번 회차 상세">
                          내역
                        </v-btn>
                      </div>
                    </CTableDataCell>
                  </CTableRow>

                  <CTableRow v-if="filteredPayouts.length === 0">
                    <CTableDataCell colspan="12" class="py-5 text-center text-muted">
                      조회 조건에 해당하는 지급 명세 데이터가 없습니다.
                    </CTableDataCell>
                  </CTableRow>
                </CTableBody>
              </CTable>
            </CCardBody>
          </CCard>
        </template>

        <!-- ═══════════════════ 대행사 탭 ═══════════════════ -->
        <template v-else>
          <!-- 대행사 지급 현황 요약 KPI -->
          <CRow v-if="selectedPeriod" class="mb-4 g-3">
            <CCol sm="6" lg="3">
              <CCard class="shadow-sm h-100 border-start border-start-4 border-start-info">
                <CCardBody>
                  <div class="text-body-secondary small fw-semibold">총 대행사 정산액 (VAT 포함)</div>
                  <div class="fs-4 fw-bold text-info">{{ agencyTotalAmount.toLocaleString() }}원</div>
                  <div class="small text-muted">{{ filteredAgencyPayouts.length }}개사</div>
                </CCardBody>
              </CCard>
            </CCol>
            <CCol sm="6" lg="3">
              <CCard class="shadow-sm h-100 border-start border-start-4 border-start-success">
                <CCardBody>
                  <div class="text-body-secondary small fw-semibold">지급 완료액</div>
                  <div class="fs-4 fw-bold text-success">{{ agencyPaidAmount.toLocaleString() }}원</div>
                  <div class="small text-success">{{ filteredAgencyPayouts.filter(ap => ap.pay_status === '3').length }}개사 완료</div>
                </CCardBody>
              </CCard>
            </CCol>
            <CCol sm="6" lg="3">
              <CCard class="shadow-sm h-100 border-start border-start-4 border-start-warning">
                <CCardBody>
                  <div class="text-body-secondary small fw-semibold">미지급 잔액</div>
                  <div class="fs-4 fw-bold text-warning">{{ (agencyTotalAmount - agencyPaidAmount).toLocaleString() }}원</div>
                  <div class="small text-muted">{{ filteredAgencyPayouts.filter(ap => ap.pay_status !== '3').length }}개사 대기</div>
                </CCardBody>
              </CCard>
            </CCol>
            <CCol sm="6" lg="3">
              <CCard class="shadow-sm h-100 border-start border-start-4 border-start-secondary">
                <CCardBody>
                  <div class="text-body-secondary small fw-semibold">직영 / 외주 구분</div>
                  <div class="small mt-1">
                    <CBadge color="primary" class="mr-1">직영 {{ agencyPayoutList.filter(ap => ap.is_direct_managed).length }}개</CBadge>
                    <CBadge color="success">외주 {{ agencyPayoutList.filter(ap => !ap.is_direct_managed).length }}개</CBadge>
                  </div>
                </CCardBody>
              </CCard>
            </CCol>
          </CRow>

          <!-- 필터 바 -->
          <CCard v-if="selectedPeriod" class="shadow-sm mb-4">
            <CCardHeader class="bg-light py-2 d-flex align-items-center gap-2 flex-wrap">
              <CFormSelect v-model="agencyStatusFilter" style="max-width: 130px">
                <option value="">전체 상태</option>
                <option value="1">지급대기</option>
                <option value="2">지급승인</option>
                <option value="3">지급완료</option>
                <option value="4">지급보류</option>
              </CFormSelect>
              <CFormInput
                v-model="agencySearchQuery"
                placeholder="대행사명, 사업자번호, 예금주..."
                style="max-width: 220px"
              />
              <span class="small text-muted ms-auto">조회: <strong>{{ filteredAgencyPayouts.length }}</strong>개사</span>
            </CCardHeader>

            <!-- 대행사 지급 명세 테이블 -->
            <CCardBody class="p-0">
              <CTable hover responsive bordered align="middle" class="mb-0 text-center text-body small">
                <colgroup>
                  <col style="width: 14%" />
                  <col style="width: 8%" />
                  <col style="width: 8%" />
                  <col style="width: 11%" />
                  <col style="width: 8%" />
                  <col style="width: 13%" />
                  <col style="width: 8%" />
                  <col style="width: 11%" />
                  <col style="width: 10%" />
                  <col style="width: 9%" />
                </colgroup>
                <CTableHead :color="TableSecondary">
                  <CTableRow>
                    <CTableHeaderCell>대행사명</CTableHeaderCell>
                    <CTableHeaderCell>구분</CTableHeaderCell>
                    <CTableHeaderCell>계약 건수</CTableHeaderCell>
                    <CTableHeaderCell>공급가액</CTableHeaderCell>
                    <CTableHeaderCell>부가세 (10%)</CTableHeaderCell>
                    <CTableHeaderCell class="table-info">총 정산액 (VAT 포함)</CTableHeaderCell>
                    <CTableHeaderCell>은행명</CTableHeaderCell>
                    <CTableHeaderCell>계좌번호</CTableHeaderCell>
                    <CTableHeaderCell>예금주</CTableHeaderCell>
                    <CTableHeaderCell>지급 상태</CTableHeaderCell>
                  </CTableRow>
                </CTableHead>

                <CTableBody>
                  <CTableRow v-for="ap in filteredAgencyPayouts" :key="ap.id">
                    <CTableDataCell class="fw-bold text-start ps-3">{{ ap.agency_name }}</CTableDataCell>
                    <CTableDataCell>
                      <CBadge :color="ap.is_direct_managed ? 'primary' : 'success'">
                        {{ ap.is_direct_managed ? '직영' : '외주' }}
                      </CBadge>
                    </CTableDataCell>
                    <CTableDataCell class="font-monospace">{{ ap.contract_count }}건</CTableDataCell>
                    <CTableDataCell class="text-end font-monospace">{{ ap.agency_fee_sum.toLocaleString() }}원</CTableDataCell>
                    <CTableDataCell class="text-end font-monospace">{{ ap.vat_amount.toLocaleString() }}원</CTableDataCell>
                    <CTableDataCell class="text-end font-monospace fw-bold text-info table-info">
                      {{ ap.total_amount.toLocaleString() }}원
                    </CTableDataCell>
                    <CTableDataCell>{{ ap.bank_name || '-' }}</CTableDataCell>
                    <CTableDataCell class="font-monospace small">{{ ap.account_number || '-' }}</CTableDataCell>
                    <CTableDataCell>{{ ap.account_holder || '-' }}</CTableDataCell>

                    <!-- 대행사 지급 상태 -->
                    <CTableDataCell>
                      <select
                        v-if="can(PERM.SALES_PAYOUT)"
                        :value="ap.pay_status"
                        class="form-select form-select-sm"
                        :class="agencyPayStatusColor(ap.pay_status)"
                        @change="changeAgencyPayStatus(ap, ($event.target as HTMLSelectElement).value)"
                      >
                        <option value="1">지급대기</option>
                        <option value="2">지급승인</option>
                        <option value="3">지급완료</option>
                        <option value="4">지급보류</option>
                      </select>
                      <CBadge
                        v-else
                        :color="ap.pay_status === '3' ? 'success' : ap.pay_status === '2' ? 'primary' : 'secondary'"
                      >
                        {{ ap.pay_status_display }}
                      </CBadge>
                      <div
                        v-if="ap.pay_status === '3' && ap.paid_date"
                        class="text-muted font-monospace"
                        style="font-size: 0.72rem"
                      >
                        {{ ap.paid_date }}
                      </div>
                    </CTableDataCell>
                  </CTableRow>

                  <CTableRow v-if="filteredAgencyPayouts.length === 0">
                    <CTableDataCell colspan="10" class="py-5 text-center text-muted">
                      대행사 지급 명세가 없습니다. 정산 관리에서 수수료 정산을 먼저 실행하세요.
                    </CTableDataCell>
                  </CTableRow>
                </CTableBody>
              </CTable>
            </CCardBody>
          </CCard>
        </template>

        <!-- 회차가 없을 때 안내 -->
        <div v-if="!selectedPeriod" class="py-5 text-center text-muted">
          <v-icon icon="mdi-calendar-blank" size="large" class="mb-2 text-secondary" />
          <h5>등록된 정산 회차가 없습니다.</h5>
          <p class="mb-0 text-secondary">
            수수료 정산 관리 메뉴에서 먼저 회차를 생성하고 수수료를 정산하세요.
          </p>
        </div>
      </div>
    </CCardBody>

    <!-- 정산 상세 모달 -->
    <PayoutDetailModal ref="detailModalRef" />

    <!-- 개인별 전 회차 누적 이력 모달 -->
    <PersonPayoutHistoryModal ref="historyModalRef" />
  </ContentBody>
</template>
