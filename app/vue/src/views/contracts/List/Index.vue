<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/contracts/_menu/headermixin'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { useProject } from '@/store/pinia/project'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import { useProjectData } from '@/store/pinia/project_data'
import { useContract } from '@/store/pinia/contract'
import type { Project } from '@/store/types/project'
import type { ContFilter, UnitFilter } from '@/store/types/contract'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContractAuthGuard from '@/components/AuthGuard/ContractAuthGuard.vue'
import ContractSummary from './components/ContractSummary.vue'
import ListController from '@/views/contracts/List/components/ListController.vue'
import AddContract from '@/views/contracts/List/components/AddContract.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import SelectItems from '@/views/contracts/List/components/SelectItems.vue'
import ContractList from '@/views/contracts/List/components/ContractList.vue'

const route = useRoute()
const listControl = ref()
const curr_status = ref<'1' | '2'>('2')
const limit = ref(10)

const highlightId = computed(() => {
  const id = route.query.highlight_id
  return id ? parseInt(id as string, 10) : null
})

// URL에서 project 파라미터 읽기
const urlProjectId = computed(() => {
  const id = route.query.project
  return id ? parseInt(id as string, 10) : null
})

// URL에서 page 파라미터 읽기
const urlPage = computed(() => {
  const page = route.query.page
  return page ? parseInt(page as string, 10) : null
})

const currentFilters = ref<ContFilter>({ project: null })

const visible = ref(false)

const filteredStr = ref(`&status=${curr_status.value}`)
const printItems = ref(['1', '3', '4', '5', '8', '13', '14'])

const excelUrl = computed(() => {
  const pk = project.value ? project.value?.pk : ''
  const items = printItems.value.join('-')
  return `/excel/contracts/?project=${pk}${filteredStr.value}&col=${items}`
})

const title = computed(() => (curr_status.value === '1' ? '청약현황' : '계약현황'))

const projStore = useProject()
const project = computed(() => projStore.project as Project)
const unitSet = computed(() => (projStore.project as Project)?.is_unit_set)
watch(project, nVal => {
  if (!!nVal)
    if (nVal?.is_unit_set && !printItems.value.includes('6-7')) printItems.value.splice(4, 0, '6-7')
})

const contStore = useContract()
const fetchOrderGroupList = (pk: number) => contStore.fetchOrderGroupList(pk)
const fetchContractList = (payload: ContFilter) => contStore.fetchContractList(payload)
const findContractPage = (highlightId: number, filters: ContFilter) =>
  contStore.findContractPage(highlightId, filters)
const fetchSubsSummaryList = (pk: number) => contStore.fetchSubsSummaryList(pk)
const fetchContSummaryList = (pk: number) => contStore.fetchContSummaryList(pk)
const fetchKeyUnitList = (payload: UnitFilter) => contStore.fetchKeyUnitList(payload)
const fetchHouseUnitList = (payload: UnitFilter) => contStore.fetchHouseUnitList(payload)

const proDataStore = useProjectData()
const fetchTypeList = (projId: number) => proDataStore.fetchTypeList(projId)
const fetchBuildingList = (projId: number) => proDataStore.fetchBuildingList(projId)

const proLedgerStore = useProLedger()
const fetchAllProBankAccList = (projId: number) => proLedgerStore.fetchAllProBankAccList(projId)

const pageSelect = (page: number) => {
  // 페이지 변경 시 query string 정리
  clearQueryString()
  listControl.value.listFiltering(page)
}

const onContFiltering = (payload: ContFilter) => {
  // 필터링 시 query string 정리
  clearQueryString()

  const {
    status,
    order_group,
    unit_type,
    building,
    null_unit,
    qualification,
    is_sup_cont,
    from_date,
    to_date,
    search,
  } = payload
  payload.project = project.value?.pk
  const is_unit = null_unit ? '1' : ''
  payload.limit = payload.limit || 10
  limit.value = payload.limit
  curr_status.value = status as '1' | '2'
  filteredStr.value = `&limit=${limit.value}&status=${status}&group=${order_group}&type=${unit_type}&dong=${building}&is_null=${is_unit}&quali=${qualification}&sup=${is_sup_cont}&sdate=${from_date}&edate=${to_date}&q=${search}`

  // 현재 필터 상태 저장
  currentFilters.value = { ...payload }

  if (payload.project) fetchContractList(payload)
}
const setItems = (arr: string[]) => (printItems.value = arr)

const handleSubscription = async () => {
  // 청약 목록으로 전환 (실제 목록은 pinia에서 이미 로드됨)
  curr_status.value = '1'
}

const handleContract = async () => {
  // 계약 목록으로 전환 (청약을 계약으로 전환했을 때)
  curr_status.value = '2'
}

const scrollToHighlight = async () => {
  if (highlightId.value) {
    await nextTick()
    const element = document.querySelector(`[data-contract-id="${highlightId.value}"]`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // highlightId는 computed이므로 URL 파라미터가 있는 동안 자동으로 유지됩니다
    }
  }
}

const loadHighlightPage = async (projectId: number) => {
  if (highlightId.value && projectId) {
    try {
      // 기본 필터 조건으로 해당 항목이 몇 번째 페이지에 있는지 찾기
      const filters = {
        ...currentFilters.value,
        project: projectId,
        limit: limit.value,
        status: curr_status.value,
      }

      // 해당 페이지로 이동 (1페이지여도 page 값 명시적 설정)
      filters.page = await findContractPage(highlightId.value, filters)
      currentFilters.value = { ...filters }
      await fetchContractList(filters)
    } catch (error) {
      console.error('Error finding highlight page:', error)
      // 오류 발생시 기본 첫 페이지 로드
      await fetchContractList({ project: projectId })
    }
  }
}

const dataSetup = async (proj: number, initialPage?: number) => {
  await fetchOrderGroupList(proj)
  await fetchTypeList(proj)
  await fetchBuildingList(proj)
  await fetchAllProBankAccList(proj)
  await fetchKeyUnitList({ project: proj })
  await fetchHouseUnitList({ project: proj })

  // 초기 필터 설정 (URL에서 page가 있으면 해당 페이지로)
  currentFilters.value = {
    project: proj,
    limit: limit.value,
    status: curr_status.value,
    ...(initialPage && { page: initialPage }),
  }

  // page 파라미터가 명시적으로 있으면 그 페이지를 사용하고 스크롤만
  // page가 없고 highlight_id만 있으면 자동으로 페이지 찾기
  if (highlightId.value && !initialPage) {
    // highlight_id만 있을 때: 자동으로 해당 항목이 있는 페이지 찾기
    await loadHighlightPage(proj)
  } else {
    // page가 명시되었거나 highlight_id가 없을 때: 지정된 페이지 로드
    await fetchContractList(currentFilters.value)
  }

  // 하이라이트 처리 후에도 목록이 비어있다면 기본 목록 로드
  if (highlightId.value && contStore.contractList.length === 0)
    await fetchContractList({ project: proj })

  await scrollToHighlight()

  await fetchSubsSummaryList(proj)
  await fetchContSummaryList(proj)
}

const dataReset = () => {
  contStore.orderGroupList = []
  contStore.subsSummaryList = []
  contStore.contSummaryList = []
  contStore.contractList = []
  contStore.contractsCount = 0
  contStore.keyUnitList = []
  contStore.houseUnitList = []
  proDataStore.buildingList = []
  proLedgerStore.allProBankList = []
}

const projSelect = async (target: number | null, skipClearQuery = false) => {
  // 프로젝트 변경 시 query string 정리 (URL 파라미터로부터 자동 전환하는 경우는 제외)
  if (!skipClearQuery) clearQueryString()

  dataReset()
  if (!!target) {
    await projStore.fetchProject(target)

    // 수동 프로젝트 선택 시에는 하이라이트 없이 일반 목록만 로드
    if (!skipClearQuery) {
      // 수동 선택 시에는 하이라이트 기능 비활성화
      await fetchOrderGroupList(target)
      await fetchTypeList(target)
      await fetchBuildingList(target)
      currentFilters.value = { project: target, limit: limit.value, status: curr_status.value }
      await fetchContractList({ project: target })
      await fetchSubsSummaryList(target)
      await fetchContSummaryList(target)
    } else {
      // 슬랙 링크 등 자동 전환 시에만 하이라이트 기능 사용
      // URL에서 page가 있으면 해당 페이지로 진입
      await dataSetup(target, urlPage.value ?? undefined)
    }

    // ContentHeader 강제 리렌더링으로 ProjectSelect 업데이트
    headerKey.value++
  }
}

const router = useRouter()

// ContentHeader 강제 리렌더링용
const headerKey = ref(0)

// Query string 정리 함수
const clearQueryString = () => {
  if (route.query.page || route.query.highlight_id) {
    router
      .replace({
        name: route.name,
        params: route.params,
        // query를 빈 객체로 설정하여 모든 query string 제거
        query: {},
      })
      .catch(() => {
        // 같은 경로로의 이동에서 발생하는 NavigationDuplicated 에러 무시
      })
  }
}

onBeforeRouteUpdate(async to => {
  // URL에서 프로젝트 ID 파라미터 확인
  const toProjectId = to.query.project ? parseInt(to.query.project as string, 10) : null
  const toPage = to.query.page ? parseInt(to.query.page as string, 10) : undefined

  if (toProjectId && toProjectId !== project.value?.pk) {
    await projSelect(toProjectId, true)
  } else {
    // URL에 highlight_id가 있으면 하이라이트 기능이 필요한 경우이므로 dataSetup 실행
    if (to.query.highlight_id) {
      await dataSetup(project.value?.pk || projStore.initProjId, toPage)
    }
    // 단순히 project 파라미터만 있는 경우는 이미 올바른 프로젝트가 선택되어 있으므로 추가 작업 불필요
  }
})

// 다른 라우트로 이동 시 query string 정리
onBeforeRouteLeave(() => {
  clearQueryString()
})

const loading = ref(true)
onBeforeMount(async () => {
  if (route.query?.status) {
    await router.replace({ name: '계약 내역 조회' })
    curr_status.value = '1'
  }

  // URL에서 프로젝트 ID가 지정되어 있으면 해당 프로젝트로 전환
  let projectId = project.value?.pk || projStore.initProjId

  if (urlProjectId.value && urlProjectId.value !== projectId) {
    // 프로젝트 전환 (query string 정리 건너뛰기)
    await projSelect(urlProjectId.value, true)
  } else {
    // URL에 프로젝트 파라미터가 없거나 같은 경우 일반 데이터 설정
    // URL에 page 파라미터가 있으면 해당 페이지로 진입
    await dataSetup(projectId, urlPage.value ?? undefined)
  }

  loading.value = false
})
</script>

<template>
  <ContractAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :key="headerKey"
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    >
      <ContractSummary :project="project ?? undefined" />
    </ContentHeader>

    <ContentBody>
      <CCardBody class="pb-5">
        <ListController ref="listControl" :status="curr_status" @cont-filtering="onContFiltering" />
        <AddContract
          :project="project?.pk"
          :unit-set="unitSet"
          @subscription-created="handleSubscription"
          @contract-converted="handleContract"
        />
        <TableTitleRow
          :title="title"
          excel
          :url="excelUrl"
          :filename="`${title}.xlsx`"
          :disabled="!project"
        >
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
        </TableTitleRow>
        <SelectItems :visible="visible" :unit-set="unitSet" @print-items="setItems" />
        <ContractList
          :limit="limit"
          :unit-set="unitSet"
          :highlight-id="highlightId ?? undefined"
          :current-page="currentFilters.page || 1"
          @page-select="pageSelect"
          @contract-converted="handleContract"
        />
      </CCardBody>
    </ContentBody>
  </ContractAuthGuard>
</template>
