<script lang="ts" setup>
import { ref, computed, watch, onMounted } from 'vue'
import { pageTitle, useSalesNavMenu } from '@/views/sales/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useSales } from '@/store/pinia/sales'
import { useContract } from '@/store/pinia/contract'
import type { Project } from '@/store/types/project'
import type { ContractSalesAgent } from '@/store/types/sales'
import { TableSecondary } from '@/utils/cssMixins'
import { usePerms } from '@/composables/usePerms'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PerformanceSummary from './components/PerformanceSummary.vue'
import ContractAgentModal from './components/ContractAgentModal.vue'
import SettlementApprovalModal from './components/SettlementApprovalModal.vue'
import { CCardBody } from '@coreui/vue'

const { can, PERM } = usePerms()
const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)
const navMenu = useSalesNavMenu(project)

const salesStore = useSales()
const contStore = useContract()

const contractAgentList = computed(() => salesStore.contractAgentList)
const allContracts = computed(() => contStore.getContracts)
const teamList = computed(() => salesStore.teamList)
const personList = computed(() => salesStore.personList)

// 필터 상태
const filterTeam = ref<number | null>(null)
const filterPerson = ref<number | null>(null)
const filterMappingStatus = ref<'all' | 'mapped' | 'unmapped'>('all')
const filterApprovalStatus = ref<'all' | 'approved' | 'pending'>('all')
const search = ref('')

const modalRef = ref()
const approvalModalRef = ref()

const loadData = async (projId: number) => {
  await Promise.all([
    salesStore.fetchContractAgentList(projId),
    salesStore.fetchPersonList(undefined, projId),
    salesStore.fetchTeamList(undefined, projId),
    salesStore.fetchPolicyList(projId),
    contStore.fetchAllContracts(projId),
  ])
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

onMounted(() => {
  if (project.value) {
    loadData(project.value)
  }
})

// 계약 ID -> 매핑 정보 Map 생성
const mappingByContractId = computed(() => {
  const map = new Map<number, ContractSalesAgent>()
  contractAgentList.value.forEach(m => {
    map.set(m.contract, m)
  })
  return map
})

// 통합 목록 아이템: 전체 계약 기준 매핑 정보 결합
const combinedList = computed(() => {
  return allContracts.value.map(c => {
    const mapping = mappingByContractId.value.get(c.value)
    return {
      contractId: c.value,
      contractLabel: c.label,
      mapping: mapping || null,
    }
  })
})

const filteredList = computed(() => {
  return combinedList.value.filter(item => {
    const m = item.mapping

    // 매핑 상태 필터
    if (filterMappingStatus.value === 'mapped' && !m) return false
    if (filterMappingStatus.value === 'unmapped' && !!m) return false

    // 정산 승인 상태 필터
    if (filterApprovalStatus.value === 'approved') {
      if (!m || !m.is_settlement_approved) return false
    } else if (filterApprovalStatus.value === 'pending') {
      if (!m || m.is_settlement_approved) return false
    }

    // 팀 필터
    if (filterTeam.value && (!m || m.team !== filterTeam.value)) return false

    // 영업직원 필터
    if (filterPerson.value && (!m || m.sales_person !== filterPerson.value)) return false

    // 검색어 필터 (계약 라벨, 상담사명, 계약번호 등)
    if (search.value.trim()) {
      const q = search.value.trim().toLowerCase()
      const matchLabel = item.contractLabel.toLowerCase().includes(q)
      const matchAgent = m?.sales_person_name?.toLowerCase().includes(q) || false
      const matchMGM = m?.mgm_name?.toLowerCase().includes(q) || false
      if (!matchLabel && !matchAgent && !matchMGM) return false
    }

    return true
  })
})

const openAssignModal = (mapping?: ContractSalesAgent, contractId?: number) => {
  modalRef.value?.open(mapping, contractId)
}

const toggleApproval = (mapping: ContractSalesAgent, label?: string) => {
  approvalModalRef.value?.open(mapping, label)
}

const onApprovalConfirm = async (payload: {
  id: number
  isApproved: boolean
  approvalNote: string
}) => {
  await salesStore.toggleSettlementApproval(payload.id, payload.approvalNote, payload.isApproved)
  if (project.value) {
    await salesStore.fetchContractAgentList(project.value)
  }
}

const onSaved = async () => {
  if (project.value) {
    await salesStore.fetchContractAgentList(project.value)
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
    <CCardBody class="p-3 p-md-4 pb-5">
      <div v-if="!project" class="py-5 text-center text-muted">
        <v-icon icon="mdi-alert-circle-outline" size="large" class="mb-2 text-warning" />
        <h5>프로젝트를 먼저 선택해 주세요.</h5>
        <p class="mb-0 text-secondary">
          상단 프로젝트 선택 메뉴에서 관리하실 프로젝트를 선택하시면 계약 실적 및 담당자 매핑을
          관리할 수 있습니다.
        </p>
      </div>

      <div v-else>
        <!-- 상단 실적 KPI 서머리 -->
        <PerformanceSummary
          :total-contracts="allContracts.length"
          :mapped-list="contractAgentList"
        />

        <!-- 계약 실적 및 영업담당자 매핑 목록 -->
        <CCard class="shadow-sm mb-4">
          <CCardHeader
            class="bg-light d-flex flex-wrap justify-content-between align-items-center py-2"
          >
            <div class="fw-bold d-flex align-items-center mb-1 mb-md-0">
              <v-icon icon="mdi-account-tie" size="small" class="mr-1 text-primary" />
              계약 실적 &amp; 영업 담당자 매핑 대장
              <CBadge color="primary" class="ml-2" shape="rounded-pill">
                {{ filteredList.length }}건
              </CBadge>
            </div>

            <div class="d-flex flex-wrap align-items-center gap-2">
              <!-- 매핑 상태 필터 -->
              <CFormSelect v-model="filterMappingStatus" style="width: 140px">
                <option value="all">전체 계약</option>
                <option value="mapped">배정 완료</option>
                <option value="unmapped">미배정 계약</option>
              </CFormSelect>

              <!-- 정산 승인 상태 필터 -->
              <CFormSelect v-model="filterApprovalStatus" style="width: 140px">
                <option value="all">전체 승인상태</option>
                <option value="approved">정산 승인건</option>
                <option value="pending">정산 보류건</option>
              </CFormSelect>

              <!-- 팀 필터 -->
              <CFormSelect v-model.number="filterTeam" style="width: 140px">
                <option :value="null">전체 팀</option>
                <option v-for="t in teamList" :key="t.id" :value="t.id">
                  {{ t.name }}
                </option>
              </CFormSelect>

              <!-- 담당직원 필터 -->
              <CFormSelect v-model.number="filterPerson" style="width: 140px">
                <option :value="null">전체 상담사</option>
                <option v-for="p in personList" :key="p.id" :value="p.id">
                  {{ p.name }}
                </option>
              </CFormSelect>

              <!-- 검색창 -->
              <CFormInput
                v-model="search"
                placeholder="계약/계약자/동호수/상담사"
                style="width: 180px"
              />

              <!-- 배정 버튼 -->
              <v-btn
                v-if="can(PERM.SALES_MANAGE)"
                color="primary"
                size="small"
                @click="openAssignModal()"
              >
                <v-icon icon="mdi-plus" size="small" class="mr-1" />
                담당자 배정
              </v-btn>
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
                <col style="width: 22%" />
                <col style="width: 10%" />
                <col style="width: 10%" />
                <col style="width: 13%" />
                <col style="width: 9%" />
                <col style="width: 14%" />
                <col style="width: 13%" />
                <col style="width: 9%" />
              </colgroup>
              <CTableHead :color="TableSecondary">
                <CTableRow>
                  <CTableHeaderCell>계약 정보 (일련번호 / 계약자 / 유니트)</CTableHeaderCell>
                  <CTableHeaderCell>담당 상담사</CTableHeaderCell>
                  <CTableHeaderCell>소속 팀</CTableHeaderCell>
                  <CTableHeaderCell>적용 수수료 정책</CTableHeaderCell>
                  <CTableHeaderCell>성과 인정일</CTableHeaderCell>
                  <CTableHeaderCell>정산 승인 상태</CTableHeaderCell>
                  <CTableHeaderCell>정산 반영 현황</CTableHeaderCell>
                  <CTableHeaderCell>관리</CTableHeaderCell>
                </CTableRow>
              </CTableHead>

              <CTableBody>
                <CTableRow v-for="item in filteredList" :key="item.contractId">
                  <!-- 계약 라벨 -->
                  <CTableDataCell class="text-left fw-bold">
                    <v-icon
                      icon="mdi-file-document-outline"
                      size="x-small"
                      class="mr-1 text-muted"
                    />
                    {{ item.contractLabel }}
                    <span
                      v-if="item.mapping?.mgm_name"
                      class="badge bg-warning text-body ml-1 font-weight-normal"
                    >
                      MGM: {{ item.mapping.mgm_name }}
                    </span>
                  </CTableDataCell>

                  <!-- 담당 영업직원 -->
                  <CTableDataCell>
                    <span v-if="item.mapping" class="fw-bold text-primary">
                      {{ item.mapping.sales_person_name }}
                    </span>
                    <CBadge v-else color="secondary" shape="rounded-pill"> 미배정 </CBadge>
                  </CTableDataCell>

                  <!-- 소속 팀 -->
                  <CTableDataCell>
                    <span v-if="item.mapping?.team_name">
                      {{ item.mapping.team_name }}
                    </span>
                    <span v-else class="text-muted">-</span>
                  </CTableDataCell>

                  <!-- 적용 정책 -->
                  <CTableDataCell class="small text-truncate">
                    <v-chip
                      v-if="item.mapping?.policy_name"
                      size="x-small"
                      class="bg-light text-body border"
                    >
                      {{ item.mapping.policy_name }}
                    </v-chip>
                    <span v-else-if="item.mapping" class="text-muted small">기본 정책</span>
                    <span v-else class="text-muted">-</span>
                  </CTableDataCell>

                  <!-- 성과 인정일 -->
                  <CTableDataCell class="font-monospace">
                    {{ item.mapping?.contract_date || '-' }}
                  </CTableDataCell>

                  <!-- 정산 승인 여부 (원클릭 토글) -->
                  <CTableDataCell>
                    <template v-if="item.mapping">
                      <button
                        type="button"
                        class="btn btn-sm py-0 px-2 fw-semibold"
                        :class="
                          item.mapping.is_settlement_approved
                            ? 'btn-success text-white'
                            : 'btn-outline-danger'
                        "
                        :disabled="!can(PERM.SALES_MANAGE)"
                        title="클릭하여 승인 / 보류 상태를 변경합니다."
                        @click="toggleApproval(item.mapping, item.contractLabel)"
                      >
                        <v-icon
                          :icon="
                            item.mapping.is_settlement_approved
                              ? 'mdi-check-circle'
                              : 'mdi-alert-circle'
                          "
                          size="x-small"
                          class="mr-1"
                        />
                        {{ item.mapping.is_settlement_approved ? '정산 승인' : '정산 보류' }}
                      </button>
                      <div
                        v-if="!item.mapping.is_settlement_approved && item.mapping.approval_note"
                        class="small text-danger mt-1 text-truncate"
                        style="max-width: 140px"
                        :title="item.mapping.approval_note"
                      >
                        {{ item.mapping.approval_note }}
                      </div>
                    </template>
                    <span v-else class="text-muted">-</span>
                  </CTableDataCell>

                  <!-- 정산 반영 현황 -->
                  <CTableDataCell>
                    <v-chip
                      v-if="item.mapping?.is_settled"
                      size="x-small"
                      class="bg-indigo-lighten-2 text-white"
                      :title="item.mapping.settled_period_title || ''"
                    >
                      <v-icon icon="mdi-check-all" size="x-small" class="mr-1" />
                      {{
                        item.mapping.settled_period_title
                          ? item.mapping.settled_period_title
                          : '정산 완료'
                      }}
                    </v-chip>
                    <span v-else-if="item.mapping" class="badge bg-secondary"> 미정산 </span>
                    <span v-else class="text-muted">-</span>
                  </CTableDataCell>

                  <!-- 관리 액션 -->
                  <CTableDataCell>
                    <template v-if="can(PERM.SALES_MANAGE)">
                      <v-btn
                        v-if="item.mapping"
                        size="x-small"
                        color="success"
                        @click="openAssignModal(item.mapping, item.contractId)"
                      >
                        수정
                      </v-btn>
                      <v-btn
                        v-else
                        size="x-small"
                        color="primary"
                        @click="openAssignModal(undefined, item.contractId)"
                      >
                        배정하기
                      </v-btn>
                    </template>
                    <span v-else class="text-muted">-</span>
                  </CTableDataCell>
                </CTableRow>

                <CTableRow v-if="filteredList.length === 0">
                  <CTableDataCell colspan="8" class="py-5 text-center text-muted">
                    표시할 분양 계약 실적 데이터가 없습니다.
                  </CTableDataCell>
                </CTableRow>
              </CTableBody>
            </CTable>
          </CCardBody>
        </CCard>
      </div>
    </CCardBody>

    <!-- 영업 담당자 배정/수정 모달 -->
    <ContractAgentModal
      v-if="project"
      ref="modalRef"
      :project="project"
      :contract-options="allContracts"
      :mapped-contract-ids="Array.from(mappingByContractId.keys())"
      @saved="onSaved"
    />

    <!-- 정산 승인 / 보류 폼 모달 -->
    <SettlementApprovalModal ref="approvalModalRef" @confirm="onApprovalConfirm" />
  </ContentBody>
</template>
