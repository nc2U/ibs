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
import type { DataFilter as Filter, ProjectBank } from '@/store/types/proLedger'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProLedgerAuthGuard from '@/components/AuthGuard/ProLedgerAuthGuard.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ListController from '@/views/proLedger/Manage/components/ListController.vue'
import AddProTrans from '@/views/proLedger/Manage/components/AddProTrans.vue'
import ProTransList from '@/views/proLedger/Manage/components/ProTransList.vue'
import ProTransForm from '@/views/proLedger/Manage/components/ProTransForm.vue'

const { can, PERM } = usePerms()
const proStore = useProject()
const project = computed(() => proStore.project?.pk)
const canLedgerCreate = computed(() =>
  project.value ? can(PERM.LEDGER_CREATE, project.value) : can(PERM.LEDGER_CREATE),
)
const canAccessProject = (projId?: number | null) =>
  projId ? can(PERM.LEDGER_READ, projId) : can(PERM.LEDGER_READ)

const listControl = ref()
const [route, router] = [useRoute() as Loaded & { name: string }, useRouter()]

const highlightId = computed(() => {
  const id = route.query.highlight_id
  if (!id) return null
  const parsed = parseInt(String(id), 10)
  return Number.isNaN(parsed) ? null : parsed
})

// URL에서 project 파라미터 읽기
const urlProjectId = computed(() => {
  const id = route.query.project
  if (!id) return null
  const parsed = parseInt(String(id), 10)
  return Number.isNaN(parsed) ? null : parsed
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

const onBankCreate = (payload: ProjectBank) =>
  proLedgerStore.createProBankAcc({
    ...payload,
    project: payload.project ?? project.value ?? null,
    is_imprest: payload.is_imprest ?? true,
  })
const onBankUpdate = (payload: ProjectBank) =>
  proLedgerStore.updateProBankAcc({
    ...payload,
    project: payload.project ?? project.value ?? null,
  })

const fetchProBankTransList = (payload: Filter) => proLedgerStore.fetchProBankTransList(payload)
const findProBankTransPage = (targetHighlightId: number, filters: Filter) =>
  proLedgerStore.findProBankTransPage(targetHighlightId, filters)
const fetchProLedgerCalculation = (com: number) => proLedgerStore.fetchProLedgerCalculation(com)

const pageSelect = (page: number) => listControl.value?.listFiltering(page)

const listFiltering = (payload: Filter) => {
  clearQueryString()
  if (project.value && canAccessProject(project.value)) {
    payload.project = project.value
    fetchProBankTransList({ ...payload, is_imprest: 'true' })
  }
}

const dataSetup = async (pk: number, targetHighlightId: number | null = null) => {
  if (!canAccessProject(pk)) return
  proLedgerStore.proBankTransFilter.project = pk
  await Promise.all([
    fetchProject(pk),
    fetchAllContracts(pk),
    fetchAllContractors(pk),
    fetchProBankAccList(pk),
    fetchAllProBankAccList(pk),
  ])
  const baseFilter: Filter = { ...dataFilter.value, project: pk, is_imprest: 'true' }
  if (targetHighlightId) {
    const targetPage = await findProBankTransPage(targetHighlightId, {
      ...baseFilter,
      limit: PAGE_SIZE,
    })
    baseFilter.page = targetPage
    proLedgerStore.proBankTransFilter.page = targetPage
  }
  await Promise.all([fetchProBankTransList(baseFilter), fetchProLedgerCalculation(pk)])
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
  if (!skipClearQuery) {
    clearQueryString()
  }
  dataReset()
  if (target) {
    await dataSetup(target)
  }
}

// Query string 정리 함수
const clearQueryString = () => {
  if (route.query.highlight_id) {
    const rest = { ...route.query }
    delete rest.highlight_id
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
    }
  }
}

const loading = ref(true)
onBeforeMount(async () => {
  try {
    const targetProjectId = urlProjectId.value || project.value || proStore.currentProject
    if (!canAccessProject(targetProjectId)) return

    await fetchProjectAccounts()

    if (targetProjectId) {
      await dataSetup(targetProjectId, highlightId.value)
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
  <ProLedgerAuthGuard :project="project">
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
            imprest-only
            :data-filter="dataFilter"
            @list-filtering="listFiltering"
          />

          <AddProTrans
            v-if="canLedgerCreate"
            :project="project as number"
            route-name="운영비 내역 관리 - 생성"
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
            is-imprest
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
          <ProTransForm :project="project as number" is-imprest />
        </div>
      </CCardBody>
    </ContentBody>
  </ProLedgerAuthGuard>
</template>
