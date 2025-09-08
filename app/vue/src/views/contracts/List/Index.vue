<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProject } from '@/store/pinia/project'
import type { Project } from '@/store/types/project'
import { useProjectData } from '@/store/pinia/project_data'
import { type ContFilter, useContract } from '@/store/pinia/contract'
import { navMenu, pageTitle } from '@/views/contracts/_menu/headermixin'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContractSummary from './components/ContractSummary.vue'
import ListController from '@/views/contracts/List/components/ListController.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import SelectItems from '@/views/contracts/List/components/SelectItems.vue'
import ContractList from '@/views/contracts/List/components/ContractList.vue'
import { CCardBody } from '@coreui/vue'

const route = useRoute()
const listControl = ref()
const status = ref('2')
const limit = ref(10)

const highlightId = computed(() => {
  const id = route.query.highlight_id
  return id ? parseInt(id as string, 10) : null
})

const currentFilters = ref<ContFilter>({ project: null })

const visible = ref(false)
const unitSet = ref(false)

const filteredStr = ref(`&status=${status.value}`)
const printItems = ref(['1', '3', '4', '5', '8', '13', '14'])

const projStore = useProject()
const project = computed<Project | null>(() => projStore.project)
watch(project, nVal => {
  unitSet.value = nVal?.is_unit_set || false
  if (!!nVal)
    if (nVal?.is_unit_set && !printItems.value.includes('6-7')) printItems.value.splice(4, 0, '6-7')
})

const excelUrl = computed(() => {
  const pk = project.value ? project.value?.pk : ''
  const items = printItems.value.join('-')
  return `/excel/contracts/?project=${pk}${filteredStr.value}&col=${items}`
})

const contStore = useContract()

const fetchOrderGroupList = (pk: number) => contStore.fetchOrderGroupList(pk)

const fetchContractList = (payload: ContFilter) => contStore.fetchContractList(payload)
const findContractPage = (highlightId: number, filters: ContFilter) =>
  contStore.findContractPage(highlightId, filters)
const fetchSubsSummaryList = (pk: number) => contStore.fetchSubsSummaryList(pk)
const fetchContSummaryList = (pk: number) => contStore.fetchContSummaryList(pk)

const proDataStore = useProjectData()

const fetchTypeList = (projId: number) => proDataStore.fetchTypeList(projId)
const fetchBuildingList = (projId: number) => proDataStore.fetchBuildingList(projId)

const pageSelect = (page: number) => listControl.value.listFiltering(page)

const onContFiltering = (payload: ContFilter) => {
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
  filteredStr.value = `&limit=${limit.value}&status=${status}&group=${order_group}&type=${unit_type}&dong=${building}&is_null=${is_unit}&quali=${qualification}&sup=${is_sup_cont}&sdate=${from_date}&edate=${to_date}&q=${search}`

  // 현재 필터 상태 저장
  currentFilters.value = { ...payload }

  if (payload.project) fetchContractList(payload)
}
const setItems = (arr: string[]) => (printItems.value = arr)

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

const loadHighlightPage = async () => {
  if (highlightId.value && project.value?.pk) {
    try {
      // 기본 필터 조건으로 해당 항목이 몇 번째 페이지에 있는지 찾기
      const filters = {
        ...currentFilters.value,
        project: project.value.pk,
        limit: limit.value,
        status: status.value,
      }

      const targetPage = await findContractPage(highlightId.value, filters)

      // 해당 페이지로 이동 (1페이지여도 page 값 명시적 설정)
      filters.page = targetPage
      currentFilters.value = { ...filters }
      await fetchContractList(filters)
    } catch (error) {
      console.error('Error finding highlight page:', error)
      // 오류 발생시 기본 첫 페이지 로드
      await fetchContractList({ project: project.value.pk })
    }
  } else if (highlightId.value && !project.value?.pk) {
    console.warn('Highlight ID present but no project selected')
  }
}

const dataSetup = async (proj: number) => {
  await fetchOrderGroupList(proj)
  await fetchTypeList(proj)
  await fetchBuildingList(proj)

  // 초기 필터 설정
  currentFilters.value = { project: proj, limit: limit.value, status: status.value }

  // 하이라이트 항목이 있으면 해당 페이지로 이동 후 스크롤
  if (highlightId.value) await loadHighlightPage()
  else await fetchContractList({ project: proj })

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
  proDataStore.buildingList = []
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const router = useRouter()

const loading = ref(true)
onBeforeMount(async () => {
  if (route.query?.status) {
    await router.replace({ name: '계약 내역 조회' })
    status.value = '1'
  }
  await dataSetup(project.value?.pk || projStore.initProjId)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentHeader
    :page-title="pageTitle"
    :nav-menu="navMenu"
    selector="ProjectSelect"
    @proj-select="projSelect"
  >
    <ContractSummary :project="project ?? undefined" />
  </ContentHeader>

  <ContentBody>
    <CCardBody class="pb-5">
      <ListController ref="listControl" :status="status" @cont-filtering="onContFiltering" />
      <TableTitleRow title="계약현황" excel :url="excelUrl" :disabled="!project">
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
        :highlight-id="highlightId ?? undefined"
        :current-page="currentFilters.page || 1"
        @page-select="pageSelect"
      />
    </CCardBody>
  </ContentBody>
</template>
