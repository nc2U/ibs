<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, ref, watch } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { navMenu, pageTitle } from '@/views/contracts/_menu/headermixin'
import { useAccount } from '@/store/pinia/account'
import { useProject } from '@/store/pinia/project'
import { useProLedger } from '@/store/pinia/proLedger'
import { useProjectData } from '@/store/pinia/project_data'
import { useContract } from '@/store/pinia/contract'
import { usePerms } from '@/composables/usePerms'
import { useDownload } from '@/utils/useDownload'
import type { Project } from '@/store/types/project'
import type { ContFilter, UnitFilter } from '@/store/types/contract'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContractAuthGuard from '@/components/AuthGuard/ContractAuthGuard.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ContractSummary from './components/ContractSummary.vue'
import ListController from './components/ListController.vue'
import AddContract from './components/AddContract.vue'
import SelectItems from './components/SelectItems.vue'
import ContractList from './components/ContractList.vue'

const { can, PERM } = usePerms()
const canContractCreate = computed(() => can(PERM.CONTRACT_CREATE))

const route = useRoute()
const router = useRouter()
const listControl = ref<InstanceType<typeof ListController> | null>(null)
const curr_status = ref<'1' | '2'>('2')
const limit = ref(10)
const loading = ref(true)
const visible = ref(false)

// 쿼리 파라미터 안전 파싱 (NaN 방지)
const parseQueryNumber = (val: unknown): number | null => {
  if (!val) return null
  const parsed = parseInt(String(val), 10)
  return Number.isNaN(parsed) ? null : parsed
}

const highlightId = computed(() => parseQueryNumber(route.query.highlight_id))
const urlProjectId = computed(() => parseQueryNumber(route.query.project))
const urlPage = computed(() => parseQueryNumber(route.query.page))

// 인쇄/엑셀 컬럼 관리
const defaultPrintItems = ['1', '3', '4', '5', '8', '13', '14']
const printItems = ref<string[]>([...defaultPrintItems])

// 스토어
const accountStore = useAccount()
const isWorkManager = computed(() => !!accountStore.workManager)
const { downloadExcel, downloadState } = useDownload()
const refCoopRegistryModal = ref<InstanceType<typeof FormModal> | null>(null)
const coopExportPurpose = ref('조합설립·변경인가 제출')

const openCoopRegistryModal = () => {
  coopExportPurpose.value = '조합설립·변경인가 제출'
  refCoopRegistryModal.value?.callModal()
}

const submitCoopRegistryExport = async () => {
  const pk = project.value?.pk
  const purpose = coopExportPurpose.value.trim()
  if (!pk || !purpose) return

  const params = new URLSearchParams()
  params.set('project', String(pk))
  params.set('purpose', purpose)
  const f = currentFilters.value
  if (f.order_group) params.set('group', String(f.order_group))
  if (f.unit_type) params.set('type', String(f.unit_type))
  if (f.qualification) params.set('quali', String(f.qualification))

  await downloadExcel(
    `/excel/coop-registry/?${params.toString()}`,
    `${project.value?.name || 'project'}_인가제출용_명부.xlsx`,
  )
  refCoopRegistryModal.value?.close()
}

const projStore = useProject()
const contStore = useContract()
const proDataStore = useProjectData()
const proLedgerStore = useProLedger()

const project = computed<Project | null>(() => (projStore.project as Project) || null)
const unitSet = computed(() => !!project.value?.is_unit_set)

// 단지 설정 여부에 따른 엑셀 출력항목 동기화
watch(
  unitSet,
  isSet => {
    if (isSet && !printItems.value.includes('6-7')) {
      printItems.value.splice(4, 0, '6-7')
    } else if (!isSet && printItems.value.includes('6-7')) {
      printItems.value = printItems.value.filter(item => item !== '6-7')
    }
  },
  { immediate: true },
)

// 엑셀 내보내기 URL 생성 (URLSearchParams 활용 및 status, ordering 파라미터 연동)
const currentFilters = ref<ContFilter>({})

const excelUrl = computed(() => {
  const pk = project.value?.pk
  if (!pk) return ''

  const params = new URLSearchParams()
  params.set('project', String(pk))
  params.set('status', curr_status.value)
  params.set('is_contract', curr_status.value === '2' ? 'true' : 'false')
  params.set('col', printItems.value.join('-'))
  params.set('limit', String(limit.value))

  const f = currentFilters.value
  if (f.order_group) params.set('group', String(f.order_group))
  if (f.unit_type) params.set('type', String(f.unit_type))
  if (f.building) params.set('dong', String(f.building))
  if (f.null_unit) params.set('is_null', '1')
  if (f.qualification) params.set('quali', String(f.qualification))
  if (f.change_type) params.set('change_type', String(f.change_type))
  if (f.is_completed) params.set('completed', String(f.is_completed))
  if (f.is_sup_cont) params.set('sup', String(f.is_sup_cont))
  if (f.from_date) params.set('sdate', String(f.from_date))
  if (f.to_date) params.set('edate', String(f.to_date))
  if (f.search) params.set('q', String(f.search))

  if (f.ordering) {
    const orderList = [
      '-created',
      'created',
      '-contractor__contract_date',
      'contractor__contract_date',
      '-serial_number',
      'serial_number',
      '-contractor__name',
      'contractor__name',
    ]
    const orderIdx = orderList.indexOf(String(f.ordering))
    if (orderIdx !== -1) params.set('order', String(orderIdx))
  }

  return `/excel/contracts/?${params.toString()}`
})

const title = computed(() => (curr_status.value === '1' ? '청약현황' : '계약현황'))

// 하이라이트 위치로 스크롤 이동
const scrollToHighlight = async () => {
  if (!highlightId.value) return
  await nextTick()
  setTimeout(() => {
    const element = document.querySelector(`[data-contract-id="${highlightId.value}"]`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, 100)
}

// 데이터 초기화
const dataReset = () => {
  contStore.orderGroupList = []
  contStore.subsSummaryList = []
  contStore.contSummaryList = []
  contStore.contractList = []
  contStore.contractsCount = 0
  contStore.keyUnitList = []
  contStore.houseUnitList = []
  proDataStore.buildingList = []
  proDataStore.unitTypeList = []
  proLedgerStore.allProBankList = []
}

// 병렬 데이터 로딩 (Waterfall 제거)
const loadProjectMeta = async (projId: number) => {
  await Promise.all([
    contStore.fetchOrderGroupList(projId),
    proDataStore.fetchTypeList(projId),
    proDataStore.fetchBuildingList(projId),
    proLedgerStore.fetchAllProBankAccList(projId),
    contStore.fetchKeyUnitList({ project: projId } as UnitFilter),
    contStore.fetchHouseUnitList({ project: projId } as UnitFilter),
  ])
}

const loadSummaryData = async (projId: number) => {
  await Promise.all([
    contStore.fetchSubsSummaryList(projId),
    contStore.fetchContSummaryList(projId),
  ])
}

const loadHighlightPage = async (projectId: number) => {
  if (!highlightId.value || !projectId) return
  try {
    const filters: ContFilter = {
      ...contStore.contractFilter,
      project: projectId,
      limit: limit.value,
      status: curr_status.value,
    }
    filters.page = await contStore.findContractPage(highlightId.value, filters)
    await contStore.fetchContractList(filters)
  } catch (error) {
    console.error('Error finding highlight page:', error)
    await contStore.fetchContractList({
      project: projectId,
      limit: limit.value,
      status: curr_status.value,
    })
  }
}

// 전체 데이터 세팅
const dataSetup = async (projId: number, initialPage?: number) => {
  await loadProjectMeta(projId)

  const filters: ContFilter = {
    ...currentFilters.value,
    project: projId,
    limit: limit.value,
    status: curr_status.value,
    ...(initialPage && { page: initialPage }),
  }

  if (highlightId.value && !initialPage) {
    await loadHighlightPage(projId)
  } else {
    await contStore.fetchContractList(filters)
  }

  if (highlightId.value && contStore.contractList.length === 0) {
    await contStore.fetchContractList({
      project: projId,
      limit: limit.value,
      status: curr_status.value,
    })
  }

  await scrollToHighlight()
  await loadSummaryData(projId)
}

let isLeaving = false

// 임시 쿼리만 선택적으로 정리 (project 등 다른 쿼리 보존)
const clearTransientQueries = () => {
  if (isLeaving) return
  if (route.query.page || route.query.highlight_id) {
    const nextQuery = { ...route.query }
    delete nextQuery.page
    delete nextQuery.highlight_id
    router.replace({ query: nextQuery }).catch(() => {})
  }
}

const pageSelect = (page: number) => {
  clearTransientQueries()
  listControl.value?.listFiltering(page)
}

const onContFiltering = (payload: ContFilter) => {
  clearTransientQueries()
  limit.value = typeof payload.limit === 'number' && payload.limit > 0 ? payload.limit : 10
  payload.limit = limit.value
  currentFilters.value = { ...payload }
  payload.status = curr_status.value
  payload.project = project.value?.pk

  if (payload.project) {
    contStore.fetchContractList(payload)
  }
}

// 탭 전환 감시 (중복 호출 방지 및 통계 최신화)
watch(curr_status, async (newStatus, oldStatus) => {
  if (newStatus !== oldStatus && listControl.value) {
    listControl.value.listFiltering(1)
    if (project.value?.pk) {
      await loadSummaryData(project.value.pk)
    }
  }
})

// 상태 전환 핸들러 (이중 호출 제거)
const handleStatusChange = async (targetStatus: '1' | '2') => {
  if (curr_status.value !== targetStatus) {
    curr_status.value = targetStatus
  } else {
    listControl.value?.listFiltering(1)
    if (project.value?.pk) {
      await loadSummaryData(project.value.pk)
    }
  }
}

const onContractUpdated = async () => {
  if (project.value?.pk) {
    await loadSummaryData(project.value.pk)
  }
}

const projSelect = async (target: number | null, isAuto = false) => {
  if (!isAuto) clearTransientQueries()
  dataReset()

  if (target) {
    if (isAuto) await projStore.fetchProject(target)
    await dataSetup(target, isAuto ? (urlPage.value ?? undefined) : undefined)
  }
}

onBeforeRouteUpdate(async to => {
  const toProjectId = parseQueryNumber(to.query.project)
  const toPage = parseQueryNumber(to.query.page) ?? undefined

  if (toProjectId && toProjectId !== project.value?.pk) {
    await projSelect(toProjectId, true)
  } else if (to.query.highlight_id || to.query.page) {
    const currentProjId = project.value?.pk || projStore.currentProject
    if (currentProjId) {
      await dataSetup(currentProjId, toPage)
    }
  }
})

onBeforeRouteLeave(() => {
  isLeaving = true
})

onBeforeMount(async () => {
  const storedFilter = contStore.contractFilter
  if (storedFilter.status) curr_status.value = storedFilter.status as '1' | '2'
  if (storedFilter.limit) limit.value = storedFilter.limit

  if (route.query.status === '1' || route.query.status === '2') {
    curr_status.value = route.query.status
  }

  const targetProjectId = urlProjectId.value || project.value?.pk || projStore.currentProject

  if (targetProjectId) {
    if (project.value?.pk !== targetProjectId) {
      await projSelect(targetProjectId, true)
    } else {
      await dataSetup(targetProjectId, urlPage.value ?? undefined)
    }
  }

  loading.value = false
})
</script>

<template>
  <ContractAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect($event, false)"
    >
      <ContractSummary :project="project ?? undefined" />
    </ContentHeader>

    <ContentBody>
      <CCardBody class="pb-5">
        <ListController ref="listControl" @cont-filtering="onContFiltering" />
        <AddContract
          v-if="canContractCreate"
          :project="project?.pk"
          :unit-set="unitSet"
          @subscription-created="handleStatusChange('1')"
          @contract-converted="handleStatusChange('2')"
        />
        <TableTitleRow excel :url="excelUrl" :filename="`${title}.xlsx`" :disabled="!project?.pk">
          <template #title>
            <v-tabs v-model="curr_status" density="compact" class="mb-0">
              <v-tab value="2" variant="tonal" :active="curr_status === '2'">계약 현황</v-tab>
              <v-tab value="1" variant="tonal" :active="curr_status === '1'">청약 현황</v-tab>
            </v-tabs>
          </template>
          <v-btn
            size="small"
            rounded="0"
            flat
            class="text-blue-accent-4 mt-1"
            style="font-size: 0.825em"
            @click="visible = !visible"
          >
            [엑셀 출력항목 선택]
          </v-btn>
          <v-btn
            v-if="isWorkManager && curr_status === '2'"
            size="small"
            color="warning"
            variant="tonal"
            prepend-icon="mdi-shield-account-outline"
            class="mt-1 ms-2"
            :disabled="!project?.pk || downloadState.isDownloading"
            @click="openCoopRegistryModal"
          >
            인가 제출용 명부
          </v-btn>
        </TableTitleRow>
        <SelectItems :visible="visible" :unit-set="unitSet" v-model:print-items="printItems" />
        <ContractList
          :limit="limit"
          :unit-set="unitSet"
          :highlight-id="highlightId ?? undefined"
          :current-page="contStore.contractFilter.page || 1"
          :border-top="!visible"
          @page-select="pageSelect"
          @contract-converted="handleStatusChange('2')"
          @contract-updated="onContractUpdated"
        />
      </CCardBody>
    </ContentBody>

    <!-- 조합 인가/행정청 제출용 명부 다운로드 모달 (슈퍼유저 / 업무관리자 전용) -->
    <FormModal ref="refCoopRegistryModal">
      <template #icon>
        <v-icon icon="mdi-file-excel-outline" size="small" color="warning" class="me-2" />
      </template>
      <template #header>인가 제출용 조합원·계약자 명부 다운로드</template>
      <template #default>
        <CForm @submit.prevent="submitCoopRegistryExport">
          <CModalBody class="text-body">
            <CAlert color="warning" class="py-2 text-xs">
              본 엑셀 파일에는 계약자 주민등록번호 원문이 포함되며, 출력자·일시·IP·사유가 감사
              로그에 영구 기록됩니다.
            </CAlert>
            <div>
              <CFormLabel class="required">출력 사유</CFormLabel>
              <CFormInput
                v-model="coopExportPurpose"
                maxlength="150"
                required
                placeholder="예: 조합설립 변경인가 신청서 제출"
              />
            </div>
          </CModalBody>
          <CModalFooter>
            <v-btn
              color="warning"
              size="small"
              type="submit"
              :disabled="!coopExportPurpose.trim() || downloadState.isDownloading"
              :loading="downloadState.isDownloading"
            >
              감사로그 기록 후 다운로드
            </v-btn>
            <v-btn color="light" size="small" flat @click="refCoopRegistryModal?.close()">
              닫기
            </v-btn>
          </CModalFooter>
        </CForm>
      </template>
    </FormModal>
  </ContractAuthGuard>
</template>
