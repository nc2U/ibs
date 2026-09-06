<script lang="ts" setup>
import { ref, computed, watch, onMounted } from 'vue'
import { navMenu, pageTitle } from '@/views/sales/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useSales } from '@/store/pinia/sales'
import { useContract } from '@/store/pinia/contract'
import type { Project } from '@/store/types/project'
import type { ContractSalesAgent } from '@/store/types/sales'
import { TableSecondary } from '@/utils/cssMixins'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PerformanceSummary from './components/PerformanceSummary.vue'
import ContractAgentModal from './components/ContractAgentModal.vue'

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

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
const search = ref('')

const modalRef = ref()

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
    <div v-if="!project" class="py-5 text-center text-muted">
      <v-icon icon="mdi-alert-circle-outline" size="large" class="mb-2 text-warning" />
      <h5>프로젝트를 먼저 선택해 주세요.</h5>
      <p class="mb-0 text-secondary">
        상단 프로젝트 선택 메뉴에서 관리하실 프로젝트를 선택하시면 계약 실적 및 담당자 매핑을 관리할 수 있습니다.
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
        <CCardHeader class="bg-light d-flex flex-wrap justify-content-between align-items-center py-2">
          <div class="fw-bold d-flex align-items-center mb-1 mb-md-0">
            <v-icon icon="mdi-account-tie" size="small" class="mr-1 text-primary" />
            계약 실적 &amp; 영업 담당자 매핑 대장
            <CBadge color="primary" class="ml-2" shape="rounded-pill">
              {{ filteredList.length }}건
            </CBadge>
          </div>

          <div class="d-flex flex-wrap align-items-center gap-2">
            <!-- 매핑 상태 필터 -->
            <CFormSelect v-model="filterMappingStatus" size="sm" style="width: 120px">
              <option value="all">전체 계약</option>
              <option value="mapped">배정 완료</option>
              <option value="unmapped">미배정 계약</option>
            </CFormSelect>

            <!-- 팀 필터 -->
            <CFormSelect v-model.number="filterTeam" size="sm" style="width: 130px">
              <option :value="null">전체 팀</option>
              <option v-for="t in teamList" :key="t.id" :value="t.id">
                {{ t.name }}
              </option>
            </CFormSelect>

            <!-- 담당직원 필터 -->
            <CFormSelect v-model.number="filterPerson" size="sm" style="width: 130px">
              <option :value="null">전체 상담사</option>
              <option v-for="p in personList" :key="p.id" :value="p.id">
                {{ p.name }}
              </option>
            </CFormSelect>

            <!-- 검색창 -->
            <CFormInput
              v-model="search"
              size="sm"
              placeholder="계약/계약자/동호수/상담사"
              style="width: 180px"
            />

            <!-- 배정 버튼 -->
            <v-btn color="primary" size="small" @click="openAssignModal()">
              <v-icon icon="mdi-plus" size="small" class="mr-1" />
              담당자 배정
            </v-btn>
          </div>
        </CCardHeader>

        <CCardBody class="p-0">
          <CTable hover responsive bordered align="middle" class="mb-0 text-center text-body small">
            <colgroup>
              <col style="width: 25%" />
              <col style="width: 12%" />
              <col style="width: 12%" />
              <col style="width: 14%" />
              <col style="width: 11%" />
              <col style="width: 14%" />
              <col style="width: 12%" />
            </colgroup>
            <CTableHead :color="TableSecondary">
              <CTableRow>
                <CTableHeaderCell>계약 정보 (일련번호 / 계약자 / 유니트)</CTableHeaderCell>
                <CTableHeaderCell>담당 영업직원 (상담사)</CTableHeaderCell>
                <CTableHeaderCell>소속 팀</CTableHeaderCell>
                <CTableHeaderCell>적용 수수료 정책</CTableHeaderCell>
                <CTableHeaderCell>성과 인정일</CTableHeaderCell>
                <CTableHeaderCell>MGM 연계 정보</CTableHeaderCell>
                <CTableHeaderCell>관리</CTableHeaderCell>
              </CTableRow>
            </CTableHead>

            <CTableBody>
              <CTableRow v-for="item in filteredList" :key="item.contractId">
                <!-- 계약 라벨 -->
                <CTableDataCell class="text-left fw-bold">
                  <v-icon icon="mdi-file-document-outline" size="x-small" class="mr-1 text-muted" />
                  {{ item.contractLabel }}
                </CTableDataCell>

                <!-- 담당 영업직원 -->
                <CTableDataCell>
                  <span v-if="item.mapping" class="fw-bold text-primary">
                    {{ item.mapping.sales_person_name }}
                  </span>
                  <CBadge v-else color="danger" shape="rounded-pill">
                    미배정
                  </CBadge>
                </CTableDataCell>

                <!-- 소속 팀 -->
                <CTableDataCell>
                  <span v-if="item.mapping?.team_name" class="small">
                    {{ item.mapping.team_name }}
                  </span>
                  <span v-else class="text-muted">-</span>
                </CTableDataCell>

                <!-- 적용 정책 -->
                <CTableDataCell class="small text-truncate">
                  <span v-if="item.mapping?.policy_name" class="badge bg-light text-dark border">
                    {{ item.mapping.policy_name }}
                  </span>
                  <span v-else-if="item.mapping" class="text-muted small">기본 정책</span>
                  <span v-else class="text-muted">-</span>
                </CTableDataCell>

                <!-- 성과 인정일 -->
                <CTableDataCell class="font-monospace small">
                  {{ item.mapping?.contract_date || '-' }}
                </CTableDataCell>

                <!-- MGM 연계 정보 -->
                <CTableDataCell class="small text-left">
                  <div v-if="item.mapping?.mgm_name">
                    <span class="badge bg-warning text-dark mr-1">MGM</span>
                    <strong>{{ item.mapping.mgm_name }}</strong>
                    <div v-if="item.mapping.mgm_fee" class="text-muted font-monospace">
                      {{ item.mapping.mgm_fee.toLocaleString() }}원
                    </div>
                  </div>
                  <span v-else class="text-muted">-</span>
                </CTableDataCell>

                <!-- 관리 액션 -->
                <CTableDataCell>
                  <v-btn
                    v-if="item.mapping"
                    size="x-small"
                    variant="tonal"
                    color="primary"
                    @click="openAssignModal(item.mapping, item.contractId)"
                  >
                    수정
                  </v-btn>
                  <v-btn
                    v-else
                    size="x-small"
                    color="success"
                    @click="openAssignModal(undefined, item.contractId)"
                  >
                    배정하기
                  </v-btn>
                </CTableDataCell>
              </CTableRow>

              <CTableRow v-if="filteredList.length === 0">
                <CTableDataCell colspan="7" class="py-5 text-center text-muted">
                  표시할 분양 계약 실적 데이터가 없습니다.
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </CCardBody>
      </CCard>
    </div>

    <!-- 영업 담당자 배정/수정 모달 -->
    <ContractAgentModal
      v-if="project"
      ref="modalRef"
      :project="project"
      :contract-options="allContracts"
      @saved="onSaved"
    />
  </ContentBody>
</template>
