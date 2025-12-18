<script setup lang="ts">
import { ref, computed, onBeforeMount, watch } from 'vue'
import Cookies from 'js-cookie'
import { pageTitle, navMenu } from '@/views/comDocs/_menu/headermixin'
import {
  onBeforeRouteUpdate,
  onBeforeRouteLeave,
  type RouteLocationNormalizedLoaded as LoadedRoute,
  useRoute,
  useRouter,
} from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import type { Company } from '@/store/types/settings.ts'
import { type SuitCaseFilter as cFilter, useDocs } from '@/store/pinia/docs'
import type { AFile, Link, SuitCase } from '@/store/types/docs'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComDocsAuthGuard from '@/components/AuthGuard/ComDocsAuthGuard.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ListController from '@/components/LawSuitCase/ListController.vue'
import CaseView from '@/components/LawSuitCase/CaseView.vue'
import CaseList from '@/components/LawSuitCase/CaseList.vue'
import CaseForm from '@/components/LawSuitCase/CaseForm.vue'

const fController = ref()
const mainViewName = ref('본사 소송 사건')

// URL에서 company 파라미터 읽기
const urlCompanyId = computed(() => {
  const id = route.query.company
  return id ? parseInt(id as string, 10) : null
})
const caseFilter = ref<cFilter>({
  company: '',
  issue_project: '',
  is_real_dev: 'false',
  court: '',
  related_case: '',
  sort: '',
  level: '',
  in_progress: '',
  search: '',
  page: 1,
  limit: '',
})

const excelFilter = computed(() => {
  const { is_real_dev, sort, level, court, in_progress, search } = caseFilter.value
  return `is_real_dev=${is_real_dev}&sort=${sort}&level=${level}&court=${court}&in_progress=${in_progress}&search=${search}`
})
const excelUrl = computed(() => `/excel/suitcases/?company=${company.value}&${excelFilter.value}`)

const formTitle = ref<string>('[본사]')
const listFiltering = (payload: cFilter) => {
  payload.limit = payload.limit || 10
  if (!payload.issue_project) {
    caseFilter.value.company = company.value as number
    caseFilter.value.issue_project = (comStore.company as Company)?.com_issue_project ?? ''
    caseFilter.value.is_real_dev = 'false'
    formTitle.value = '[본사]'
  } else {
    caseFilter.value.issue_project = payload.issue_project
    caseFilter.value.is_real_dev = ''
    formTitle.value = getAllProjPks.value.filter(p => p.value == payload.issue_project)[0].label
  }

  caseFilter.value = payload
  const allCaseFilter = payload.issue_project
    ? ({ issue_project: payload.issue_project as number } as cFilter)
    : ({ company: company.value as number, is_real_dev: 'false' } as cFilter)
  fetchAllSuitCaseList(allCaseFilter)
  fetchSuitCaseList({ ...caseFilter.value })
}

const pageSelect = (page: number) => {
  caseFilter.value.page = page
  fetchSuitCaseList(caseFilter.value)
}

const accStore = useAccount()
const writeAuth = computed(() => accStore.writeComDocs)

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)

const workStore = useWork()
const getAllProjPks = computed(() => workStore.getAllProjPks)

const docStore = useDocs()
const suitcase = computed(() => docStore.suitcase)
const suitcaseList = computed(() => docStore.suitcaseList)
const getSuitCase = computed(() => docStore.getSuitCase)

const fetchLink = (pk: number) => docStore.fetchLink(pk)
const fetchFile = (pk: number) => docStore.fetchFile(pk)
const fetchSuitCase = (pk: number) => docStore.fetchSuitCase(pk)
const fetchSuitCaseList = (payload: cFilter) => docStore.fetchSuitCaseList(payload)
const fetchAllSuitCaseList = (payload: cFilter) => docStore.fetchAllSuitCaseList(payload)

const createSuitCase = (payload: SuitCase) => docStore.createSuitCase(payload)
const updateSuitCase = (payload: SuitCase) => docStore.updateSuitCase(payload)
const deleteSuitCase = (pk: number) => docStore.deleteSuitCase(pk)
const patchLink = (pk: number, payload: Link) => docStore.patchLink(pk, payload)
const patchFile = (pk: number, payload: any) => docStore.patchFile(pk, payload)
const linkHit = async (pk: number) => {
  const link = (await fetchLink(pk)) as Link
  link.hit = (link.hit as number) + 1
  await patchLink(pk, link)
}
const fileHit = async (pk: number) => {
  const file = (await fetchFile(pk)) as AFile
  const hit = (file.hit as number) + 1
  await patchFile(pk, { hit })
}

const [route, router] = [useRoute() as LoadedRoute & { name: string }, useRouter()]

watch(route, val => {
  if (val.params.caseId) fetchSuitCase(Number(val.params.caseId))
  else docStore.removeSuitcase()
})

// ContentHeader 강제 리렌더링용
const headerKey = ref(0)

// company 변경을 감지하여 자동으로 데이터 다시 로드
const isInitializing = ref(true)
watch(
  company,
  async (newCompany, oldCompany) => {
    // 초기화 중이거나 URL에서 회사 변경 중인 경우 무시
    if (isInitializing.value) return

    if (newCompany && newCompany !== oldCompany && oldCompany !== undefined)
      await dataSetup(newCompany, route.params?.caseId)
  },
  { immediate: false },
)

const onSubmit = (payload: SuitCase) => {
  if (!!company.value) {
    if (payload.pk) {
      updateSuitCase(payload)
      router.replace({
        name: `${mainViewName.value} - 보기`,
        params: { caseId: payload.pk },
      })
    } else {
      payload.issue_project = ((comStore.company as Company)?.com_issue_project as number) ?? null
      createSuitCase(payload)
      router.replace({ name: `${mainViewName.value}` })
    }
  }
}

const onDelete = (pk: number) => deleteSuitCase(pk)

const agencyFilter = (court: string) => {
  fController.value.courtChange(court)
  caseFilter.value.page = 1
  caseFilter.value.court = court
  listFiltering(caseFilter.value)
}
const agencySearch = (agent: string) => {
  fController.value.searchChange(agent)
  caseFilter.value.page = 1
  caseFilter.value.search = agent
  listFiltering(caseFilter.value)
}

const relatedFilter = (related: number) => {
  fController.value.relatedChange(related)
  caseFilter.value.page = 1
  caseFilter.value.related_case = related
  listFiltering(caseFilter.value)
}

const dataSetup = async (pk: number, caseId?: string | string[]) => {
  caseFilter.value.company = pk

  // workStore.fetchAllIssueProjectList가 회사를 변경하므로 현재 회사 저장
  const targetCompany = pk

  await workStore.fetchAllIssueProjectList(pk, '2', '')

  // workStore 함수가 회사를 변경했다면 다시 원래 회사로 복원
  if (company.value !== targetCompany) {
    Cookies.set('curr-company', `${targetCompany}`)
    await comStore.fetchCompany(targetCompany)
  }

  await fetchAllSuitCaseList({ company: pk, is_real_dev: 'false' })
  await fetchSuitCaseList(caseFilter.value)
  if (caseId) await fetchSuitCase(Number(caseId))
}

const dataReset = () => {
  caseFilter.value.issue_project = ''
  caseFilter.value.is_real_dev = 'false'
  // 사건 리스트만 리셋하고 현재 사건은 유지
  docStore.removeSuitcaseList()
  docStore.suitcaseCount = 0
}

// Query string 정리 함수
const clearQueryString = () => {
  if (Object.keys(route.query).length > 0) {
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

const comSelect = async (target: number | null, skipClearQuery = false) => {
  // 회사 변경 시 query string 정리 (URL 파라미터로부터 자동 전환하는 경우는 제외)
  if (!skipClearQuery) clearQueryString()

  if (fController.value) fController.value.resetForm(false)

  if (!!target) {
    // 쿠키 설정 (ContentHeader와 동일한 방식)
    Cookies.set('curr-company', `${target}`)

    // 회사 변경
    await comStore.fetchCompany(target)

    // 슬랙 링크 진입 시 보기 화면에서 목록으로 이동하지 않음
    const isSlackEntry = skipClearQuery && route.name?.includes('보기')
    if (!isSlackEntry && route.name?.includes('보기')) {
      await router.replace({ name: '본사 소송 사건' })
    }

    // 초기화 중이거나 watch가 비활성화된 경우 직접 데이터 로딩
    if (isInitializing.value) {
      await dataSetup(target, route.params?.caseId)
      // ContentHeader 강제 리렌더링으로 CompanySelect 업데이트
      headerKey.value++
    }
  } else {
    dataReset()
    docStore.removeSuitcaseList()
  }
}

const caseRenewal = (page: number) => {
  caseFilter.value.page = page
  fetchSuitCaseList(caseFilter.value)
}

onBeforeRouteUpdate(async to => {
  // URL에서 회사 ID 파라미터 확인
  const toCompanyId = to.query.company ? parseInt(to.query.company as string, 10) : null

  if (toCompanyId && toCompanyId !== company.value) await comSelect(toCompanyId, true)
  else await dataSetup(company.value || comStore.initComId, to.params?.caseId)
})

const loading = ref(true)
onBeforeMount(async () => {
  // URL에서 회사 ID가 지정되어 있으면 해당 회사로 전환
  let companyId = company.value || comStore.initComId

  if (urlCompanyId.value)
    // 회사 전환 (query string 정리 건너뛰기) 및 사건 로드
    await comSelect(urlCompanyId.value, true)
  else
    // URL에 회사 파라미터가 없는 경우에만 일반 데이터 설정
    await dataSetup(companyId, route.params?.caseId)

  // 초기화 완료 후 watch 활성화
  isInitializing.value = false
  loading.value = false
})

// 다른 라우트로 이동 시 query string 정리
onBeforeRouteLeave(() => {
  clearQueryString()
})
</script>

<template>
  <ComDocsAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :key="headerKey"
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      @com-select="comSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <div v-if="route.name === `${mainViewName}`" class="pt-3">
          <ListController
            ref="fController"
            :com-from="true"
            :company="company ?? undefined"
            :projects="getAllProjPks"
            :case-filter="caseFilter"
            @list-filter="listFiltering"
          />

          <TableTitleRow
            title="본사 소송 사건 목록"
            excel
            :url="excelUrl"
            filename="본사_소송사건.xlsx"
            :disabled="!company"
          />

          <CaseList
            :company="company || undefined"
            :limit="caseFilter.limit || 10"
            :page="caseFilter.page || 1"
            :case-list="suitcaseList"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @page-select="pageSelect"
            @agency-filter="agencyFilter"
            @agency-search="agencySearch"
            @related-filter="relatedFilter"
          />
        </div>

        <div v-else-if="route.name.includes('보기')">
          <CaseView
            :curr-page="caseFilter.page ?? 1"
            :suitcase="suitcase as SuitCase"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @link-hit="linkHit"
            @file-hit="fileHit"
            @case-renewal="caseRenewal"
          />
        </div>

        <div v-else-if="route.name.includes('작성')">
          <CaseForm
            :sort-name="formTitle"
            :get-suit-case="getSuitCase"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @on-submit="onSubmit"
          />
        </div>

        <div v-else-if="route.name.includes('수정')">
          <CaseForm
            :sort-name="formTitle"
            :get-suit-case="getSuitCase"
            :suitcase="suitcase"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @on-submit="onSubmit"
            @on-delete="onDelete"
          />
        </div>
      </CCardBody>
    </ContentBody>
  </ComDocsAuthGuard>
</template>
