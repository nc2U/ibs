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
import { useProLedger } from '@/store/pinia/proLedger'
import { message } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
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

const { can, PERM } = usePerms()
const canLedgerCreate = computed(() => can(PERM.LEDGER_CREATE))

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

const PAGE_SIZE = 15 // Django 목록 페이지 크기와 동일하게 유지

const excelUrl = computed(() => {
  const f = dataFilter.value
  const params = new URLSearchParams({
    project: String(project.value ?? ''),
    is_imprest: 'true',
    from_date: f.from_date || '',
    to_date: f.to_date || '',
    sort: String(f.sort || ''),
    account_category: String(f.account_category || ''),
    account: String(f.account || ''),
    bank_account: String(f.bank_account || ''),
    contract: String(f.contract || ''),
    search: f.search || '',
  })
  return `/excel/pro-trans/?${params.toString()}`
})

const proStore = useProject()
const project = computed(() => proStore.project?.pk)
const fetchProject = (pk: number) => proStore.fetchProject(pk)

const contStore = useContract()
const getContracts = computed(() => contStore.getContracts)
const getAllContractors = computed(() => contStore.getAllContractors)
const fetchAllContracts = (projId: number) => contStore.fetchAllContracts(projId)
const fetchAllContractors = (projId: number) => contStore.fetchAllContractors(projId)

const proLedgerStore = useProLedger()
const proAccounts = computed(() => proLedgerStore.proAccounts)
const transferFeePk = computed(() => proLedgerStore.transferFeePk)
const allProBankList = computed(() => proLedgerStore.allProBankList)
const dataFilter = computed(() => proLedgerStore.proBankTransFilter as Filter)
const proBankTransCount = computed(() => proLedgerStore.proBankTransCount)

provide('proAccounts', proAccounts)
provide('transferFeePk', transferFeePk)
provide('allProBankList', allProBankList)
provide('proBankTransCount', proBankTransCount)
provide('getContracts', getContracts)
provide('getAllContractors', getAllContractors)

const fetchProjectAccounts = () => proLedgerStore.fetchProjectAccounts()
const fetchProBankAccList = (pk: number) => proLedgerStore.fetchProBankAccList(pk)
const fetchAllProBankAccList = (pk: number) => proLedgerStore.fetchAllProBankAccList(pk)
const createProBankAcc = (payload: any) => proLedgerStore.createProBankAcc(payload)
const updateProBankAcc = (payload: any) => proLedgerStore.updateProBankAcc(payload)

const onBankCreate = (payload: any) => createProBankAcc(payload)
const onBankUpdate = (payload: any) => updateProBankAcc(payload)

const fetchProBankTransList = (payload: Filter) => proLedgerStore.fetchProBankTransList(payload)
const findProBankTransPage = (highlightId: number, filters: Filter) =>
  proLedgerStore.findProBankTransPage(highlightId, filters)
const fetchProLedgerCalculation = (com: number) => proLedgerStore.fetchProLedgerCalculation(com)

const pageSelect = (page: number) => listControl.value?.listFiltering(page)

const listFiltering = (payload: Filter) => {
  // 필터링 시 query string 정리
  clearQueryString()
  if (project.value) payload.project = project.value
  if (project.value) fetchProBankTransList({ ...payload, is_imprest: 'true' })
}

const dataSetup = async (pk: number) => {
  // 거래 목록 조회 전에 필터의 project 설정
  proLedgerStore.proBankTransFilter.project = pk
  // 서로 독립적인 호출은 병렬로 실행
  await Promise.all([
    fetchProject(pk),
    fetchAllContracts(pk),
    fetchAllContractors(pk),
    fetchProBankAccList(pk),
    fetchAllProBankAccList(pk),
  ])
  await Promise.all([
    fetchProBankTransList({ project: pk, is_imprest: 'true' }),
    fetchProLedgerCalculation(pk),
  ])
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
    await dataSetup(target)
  }
}

// Query string 정리 함수
const clearQueryString = () => {
  if (route.query.highlight_id) {
    // highlight_id만 제거하고 나머지 query(project 등)는 보존
    const { highlight_id: _omit, ...rest } = route.query
    router
      .replace({
        name: route.name,
        params: route.params,
        query: rest,
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
        limit: PAGE_SIZE,
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
  try {
    // URL에서 프로젝트 ID가 지정되어 있으면 해당 프로젝트로 전환
    let projectId = project.value || proStore.currentProject
    if (urlProjectId.value && urlProjectId.value !== projectId) {
      // 프로젝트 전환 (query string 정리 건너뛰기)
      await projSelect(urlProjectId.value, true)
      projectId = urlProjectId.value
    }

    await fetchProjectAccounts()

    if (projectId) {
      // 하이라이트 항목이 있으면 해당 페이지로 이동 후 스크롤
      if (highlightId.value) {
        await loadHighlightPage()
      } else {
        await dataSetup(projectId)
      }
      await scrollToHighlight()
    }
  } catch (err) {
    console.error('Error loading page:', err)
    message('warning', '알림!', '페이지 로딩 중 에러가 발생하였습니다.')
  } finally {
    loading.value = false
  }
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
        <div v-if="route.name === '운영비 내역 관리'">
          <ListController
            ref="listControl"
            :project="project as number"
            :data-filter="dataFilter"
            @list-filtering="listFiltering"
          />

          <AddProTrans
            v-if="canLedgerCreate"
            :project="project as number"
          />

          <TableTitleRow
            title="운영비용 입출금 관리"
            color="indigo"
            excel
            :url="excelUrl"
            filename="PR운영비용_출납내역.xls"
            :disabled="!project"
          />
          <ProTransList
            :project="project as number"
            :highlight-id="highlightId ?? undefined"
            :current-page="dataFilter.page || 1"
            @on-bank-create="onBankCreate"
            @on-bank-update="onBankUpdate"
            @page-select="pageSelect"
          />
        </div>

        <div
          v-else-if="
            route.name === '운영비 내역 관리 - 수정' || route.name === '운영비 내역 관리 - 생성'
          "
        >
          <ProTransForm :project="project as number" />
        </div>
      </CCardBody>
    </ContentBody>
  </ProLedgerAuthGuard>
</template>
