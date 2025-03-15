<script setup lang="ts">
import { ref, computed, onBeforeMount, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/comDocs/_menu/headermixin'
import {
  onBeforeRouteUpdate,
  type RouteLocationNormalizedLoaded as LoadedRoute,
  useRoute,
  useRouter,
} from 'vue-router'
import { useWork } from '@/store/pinia/work'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import { type SuitCaseFilter as cFilter, useDocs } from '@/store/pinia/docs'
import type { AFile, Link, SuitCase } from '@/store/types/docs'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ListController from '@/components/LawSuitCase/ListController.vue'
import CaseView from '@/components/LawSuitCase/CaseView.vue'
import CaseList from '@/components/LawSuitCase/CaseList.vue'
import CaseForm from '@/components/LawSuitCase/CaseForm.vue'

const fController = ref()
const mainViewName = ref('본사 소송 사건')
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

const listFiltering = (payload: cFilter) => {
  payload.limit = payload.limit || 10
  caseFilter.value.company = company.value as number
  if (!payload.issue_project) {
    caseFilter.value.company = company.value ?? ''
    caseFilter.value.issue_project = comStore.company?.com_issue_project ?? ''
    caseFilter.value.is_real_dev = 'false'
  } else {
    caseFilter.value.issue_project = payload.issue_project
    caseFilter.value.is_real_dev = ''
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
  listFiltering(caseFilter.value)
}

const accStore = useAccount()
const writeAuth = computed(() => accStore.writeComDocs)

const comStore = useCompany()
const company = computed(() => comStore.company?.pk)

const workStore = useWork()
const getAllProjects = computed(() => workStore.getAllProjects)

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
const patchLink = (payload: Link) => docStore.patchLink(payload)
const patchFile = (payload: AFile) => docStore.patchFile(payload)
const linkHit = async (pk: number) => {
  const link = (await fetchLink(pk)) as Link
  link.hit = (link.hit as number) + 1
  await patchLink(link)
}
const fileHit = async (pk: number) => {
  const file = (await fetchFile(pk)) as AFile
  const hit = (file.hit as number) + 1
  await patchFile({ pk, hit })
}

const [route, router] = [useRoute() as LoadedRoute & { name: string }, useRouter()]

watch(route, val => {
  if (val.params.caseId) fetchSuitCase(Number(val.params.caseId))
  else docStore.removeSuitcase()
})

const onSubmit = (payload: SuitCase) => {
  if (!!company.value)
    if (payload.pk) {
      updateSuitCase(payload)
      router.replace({
        name: `${mainViewName.value} - 보기`,
        params: { caseId: payload.pk },
      })
    } else {
      payload.issue_project = caseFilter.value.issue_project || null
      createSuitCase(payload)
      router.replace({ name: `${mainViewName.value}` })
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

const dataSetup = (pk: number, caseId?: string | string[]) => {
  caseFilter.value.company = pk
  workStore.fetchAllIssueProjectList(pk, '2', '')
  fetchAllSuitCaseList({ company: pk, is_real_dev: 'false' })
  fetchSuitCaseList(caseFilter.value)
  if (caseId) fetchSuitCase(Number(caseId))
}

const dataReset = () => {
  caseFilter.value.issue_project = ''
  caseFilter.value.is_real_dev = 'false'
  docStore.removeSuitcase()
  docStore.removeSuitcaseList()
  docStore.suitcaseCount = 0
  router.replace({ name: `${mainViewName.value}` })
}

const comSelect = (target: number | null) => {
  if (fController.value) fController.value.resetForm(false)
  dataReset()
  if (!!target) dataSetup(target)
  else docStore.removeSuitcaseList()
}

const caseRenewal = (page: number) => {
  caseFilter.value.page = page
  fetchSuitCaseList(caseFilter.value)
}

onBeforeRouteUpdate(() => dataSetup(company.value || comStore.initComId, route.params?.caseId))

onBeforeMount(() => dataSetup(company.value || comStore.initComId, route.params?.caseId))
</script>

<template>
  <ContentHeader
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
          :projects="getAllProjects"
          :case-filter="caseFilter"
          @list-filter="listFiltering"
        />

        <TableTitleRow title="본사 소송 사건 목록" excel :url="excelUrl" :disabled="!company" />

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
          :get-suit-case="getSuitCase"
          :view-route="mainViewName"
          :write-auth="writeAuth"
          @on-submit="onSubmit"
        />
      </div>

      <div v-else-if="route.name.includes('수정')">
        <CaseForm
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
</template>
