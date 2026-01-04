<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, provide, ref } from 'vue'
import {
  onBeforeRouteLeave,
  type RouteLocationNormalizedLoaded as Loaded,
  useRoute,
  useRouter,
} from 'vue-router'
import { navMenu, pageTitle } from '@/views/proLedger/_menu/headermixin'
import { useProject } from '@/store/pinia/project.ts'
import { useContract } from '@/store/pinia/contract.ts'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import { write_project_cash } from '@/utils/pageAuth'
import { useProLedger } from '@/store/pinia/proLedger'
import { type DataFilter as Filter } from '@/store/types/proLedger'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProLedgerAuthGuard from '@/components/AuthGuard/ProLedgerAuthGuard.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ListController from './components/ListController.vue'
import AddProTrans from './components/AddProTrans.vue'
import ProTransList from './components/ProTransList.vue'
import ProTransForm from './components/ProTransForm.vue'

const listControl = ref()
const [route, router] = [useRoute() as Loaded & { name: string }, useRouter()]

const highlightId = computed(() => {
  const id = route.query.highlight_id
  return id ? parseInt(id as string, 10) : null
})

// URL에서 project 파라미터 읽기
const urlProjectId = computed(() => {
  const id = route.query.project
  return id ? parseInt(id as string, 10) : null
})

const excelUrl = computed(() => {
  const from_date = dataFilter.value.from_date || ''
  const to_date = dataFilter.value.to_date || ''
  const sort = dataFilter.value.sort || ''
  const account = dataFilter.value.account || ''
  const account_category = dataFilter.value.account_category || ''
  const bank_account = dataFilter.value.bank_account || ''
  const contract = dataFilter.value.contract || ''
  const search = dataFilter.value.search || ''
  const url = `/excel/pro-transaction/?project=${project.value}&is_imprest=true`
  return `${url}&from_date=${from_date}&to_date=${to_date}&sort=${sort}&account_category=${account_category}&account=${account}&bank_account=${bank_account}&contract=${contract}&search=${search}`
})

const proStore = useProject()
const project = computed(() => proStore.project?.pk)
const fetchProject = (pk: number) => proStore.fetchProject(pk)

const contStore = useContract()
const getContracts = computed(() => contStore.getContracts)
const getAllContractors = computed(() => contStore.getAllContractors)
const fetchAllContracts = (projId: number) => contStore.fetchAllContracts(projId)
const fetchAllContractors = (projId: number) => contStore.fetchAllContractors(projId)

const comLedgerStore = useComLedger()
const fetchBankCodeList = () => comLedgerStore.fetchBankCodeList()

const proLedgerStore = useProLedger()
const proAccounts = computed(() => proLedgerStore.proAccounts)
const allProBankList = computed(() => proLedgerStore.allProBankList)
const dataFilter = computed(() => proLedgerStore.proBankTransFilter)
const proBankTransCount = computed(() => proLedgerStore.proBankTransCount)

provide('proAccounts', proAccounts)
provide('allProBankList', allProBankList)
provide('proBankTransCount', proBankTransCount)
provide('getContracts', getContracts)
provide('getAllContractors', getAllContractors)

const fetchProjectAccounts = () => proLedgerStore.fetchProjectAccounts()
const fetchProBankAccList = (pk: number) => proLedgerStore.fetchProBankAccList(pk)
const fetchAllProBankAccList = (pk: number) => proLedgerStore.fetchAllProBankAccList(pk)

const fetchProBankTransList = (payload: Filter) => proLedgerStore.fetchProBankTransList(payload)
const findProBankTransPage = (highlightId: number, filters: Filter) =>
  proLedgerStore.findProBankTransPage(highlightId, filters)
const fetchProLedgerCalculation = (com: number) => proLedgerStore.fetchProLedgerCalculation(com)

const pageSelect = (page: number) => listControl.value.listFiltering(page)

const listFiltering = (payload: Filter) => {
  // 필터링 시 query string 정리
  clearQueryString()
  if (project.value) payload.project = project.value
  if (project.value) fetchProBankTransList({ is_imprest: 'true', ...payload })
}

const dataSetup = async (pk: number) => {
  await fetchProject(pk)
  await fetchAllContracts(pk)
  await fetchAllContractors(pk)
  await fetchProBankAccList(pk)
  await fetchAllProBankAccList(pk)
  await fetchProBankTransList({ project: pk, is_imprest: 'true' })
  await fetchProLedgerCalculation(pk)
  proLedgerStore.proBankTransFilter.project = pk
}

const dataReset = () => {
  proStore.removeProject()
  proLedgerStore.proBankList = []
  proLedgerStore.allProBankList = []
  proLedgerStore.proBankTransList = []
  proLedgerStore.proBankTransCount = 0
  proLedgerStore.proBankTransFilter.project = null
}

const projSelect = async (target: number | null, skipClearQuery = false) => {
  // 프로젝트 변경 시 query string 정리 (URL 파라미터로부터 자동 전환하는 경우는 제외)
  if (!skipClearQuery) {
    clearQueryString()
  }
  dataReset()
  if (!!target) {
    await fetchProject(target)
    await dataSetup(target)
  }
}

// Query string 정리 함수
const clearQueryString = () => {
  if (route.query.highlight_id) {
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

const scrollToHighlight = async () => {
  if (highlightId.value) {
    await nextTick()
    const element = document.querySelector(`[data-cash-id="${highlightId.value}"]`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // highlightId는 computed이므로 URL 파라미터가 있는 동안 자동으로 유지됩니다
    }
  }
}

const loadHighlightPage = async () => {
  if (highlightId.value && project.value) {
    try {
      // 현재 필터 조건으로 해당 항목이 몇 번째 페이지에 있는지 찾기
      const targetPage = await findProBankTransPage(highlightId.value, {
        ...dataFilter.value,
        project: project.value,
        is_imprest: 'true',
        limit: 15, // Django에서 사용하는 페이지 크기와 동일하게 설정
      })
      // 해당 페이지로 이동 (1페이지여도 page 값 명시적 설정)
      proLedgerStore.proBankTransFilter.page = targetPage
      await fetchProBankTransList({
        ...dataFilter.value,
        project: project.value,
        is_imprest: 'true',
      })
    } catch (error) {
      console.error('Error finding highlight page:', error)
    }
  }
}

const loading = ref(true)
onBeforeMount(async () => {
  // URL에서 회사 ID가 지정되어 있으면 해당 회사로 전환
  let projectId = project.value || proStore.initProjId
  if (urlProjectId.value && urlProjectId.value !== projectId) {
    console.log(`Switching to project ${urlProjectId.value} from URL parameter`)
    // 회사 전환 (query string 정리 건너뛰기)
    await projSelect(urlProjectId.value, true)
    projectId = urlProjectId.value
  }

  await fetchBankCodeList()
  await fetchProjectAccounts()

  // 하이라이트 항목이 있으면 해당 페이지로 이동 후 스크롤
  if (highlightId.value) {
    await loadHighlightPage()
  } else {
    await dataSetup(projectId)
  }
  await scrollToHighlight()

  loading.value = false
})

// 다른 라우트로 이동 시 query string 정리
onBeforeRouteLeave(() => {
  clearQueryString()
})
</script>

<template>
  <ProLedgerAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    />
    <ContentBody>
      <CCardBody class="pb-5">
        <div v-if="route.name === 'PR 거래 내역'">
          <ListController
            ref="listControl"
            :project="project as number"
            :data-filter="dataFilter"
            @list-filtering="listFiltering"
          />

          <AddProTrans v-if="write_project_cash" :project="project as number" />

          <TableTitleRow
            title="프로젝트 입출금 관리"
            color="indigo"
            excel
            :url="excelUrl"
            filename="PR자금_출납내역.xls"
            :disabled="!project"
          />
          <ProTransList
            :project="project as number"
            :highlight-id="highlightId ?? undefined"
            :current-page="dataFilter.page || 1"
            @page-select="pageSelect"
          />
        </div>

        <div
          v-else-if="route.name === 'PR 거래 내역 - 수정' || route.name === 'PR 거래 내역 - 생성'"
        >
          <ProTransForm :project="project as number" />
        </div>
      </CCardBody>
    </ContentBody>
  </ProLedgerAuthGuard>
</template>
