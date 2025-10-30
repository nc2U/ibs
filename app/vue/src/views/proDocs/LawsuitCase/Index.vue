<script lang="ts" setup>
import { ref, computed, watch, onBeforeMount } from 'vue'
import { pageTitle, navMenu } from '@/views/proDocs/_menu/headermixin1'
import { useAccount } from '@/store/pinia/account'
import { useProject } from '@/store/pinia/project'
import {
  onBeforeRouteUpdate,
  type RouteLocationNormalizedLoaded as LoadedRoute,
  useRoute,
  useRouter,
} from 'vue-router'
import { type SuitCaseFilter as cFilter, useDocs } from '@/store/pinia/docs'
import type { AFile, Link, SuitCase } from '@/store/types/docs'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProDocsAuthGuard from '@/components/AuthGuard/ProDocsAuthGuard.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ListController from '@/components/LawSuitCase/ListController.vue'
import CaseView from '@/components/LawSuitCase/CaseView.vue'
import CaseList from '@/components/LawSuitCase/CaseList.vue'
import CaseForm from '@/components/LawSuitCase/CaseForm.vue'

const fController = ref()
const mainViewName = ref('PR 소송 사건')
const caseFilter = ref<cFilter>({
  company: '',
  project: '',
  is_real_dev: '',
  court: '',
  related_case: '',
  sort: '',
  level: '',
  in_progress: '',
  search: '',
  page: 1,
  limit: '',
})

const excelFilter = computed(
  // Todo 퀴리 점검 할 것
  () => {
    const { is_real_dev, sort, level, court, in_progress, search } = caseFilter.value
    return `project=${project.value}&is_real_dev=${is_real_dev}&sort=${sort}&level=${level}&court=${court}&in_progress=${in_progress}&search=${search}`
  },
)
const excelUrl = computed(() => `/excel/suitcases/?company=${company.value}&${excelFilter.value}`)

const listFiltering = (payload: cFilter) => {
  payload.limit = payload.limit || 10
  payload.is_real_dev = 'true'
  payload.project = project.value ?? ''
  caseFilter.value = payload
  if (company.value) fetchSuitCaseList({ ...caseFilter.value })
}

const pageSelect = (page: number) => {
  caseFilter.value.page = page
  fetchSuitCaseList(caseFilter.value)
}

const accStore = useAccount()
const writeAuth = computed(() => accStore.writeProDocs)

const projStore = useProject()
const project = computed(() => projStore.project?.pk)
const projName = computed(() => projStore.project?.name)
const company = computed(() => projStore.project?.company)

const docStore = useDocs()
const suitcase = computed(() => docStore.suitcase)
const suitcaseList = computed(() => docStore.suitcaseList)
const getSuitCase = computed(() => docStore.getSuitCase)

const fetchLink = (pk: number) => docStore.fetchLink(pk)
const fetchFile = (pk: number) => docStore.fetchFile(pk)
const fetchSuitCase = (pk: number) => docStore.fetchSuitCase(pk)
const fetchSuitCaseList = (payload: cFilter) => docStore.fetchSuitCaseList(payload)
const fetchAllSuitCaseList = (payload: cFilter) => docStore.fetchAllSuitCaseList(payload)

const createSuitCase = (payload: SuitCase & { isProject?: boolean }) =>
  docStore.createSuitCase(payload)
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

const casesRenewal = (page: number) => {
  caseFilter.value.page = page
  fetchSuitCaseList(caseFilter.value)
}

const onSubmit = (payload: SuitCase & { is_real_dev?: boolean }) => {
  if (payload.pk) {
    updateSuitCase(payload)
    router.replace({
      name: `${mainViewName.value} - 보기`,
      params: { caseId: payload.pk },
    })
  } else {
    payload.issue_project = projStore.project?.issue_project as number
    payload.is_real_dev = true
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
  caseFilter.value.company = company.value ?? ''
  caseFilter.value.project = pk
  fetchAllSuitCaseList({ company: company.value ?? '', is_real_dev: 'true', project: pk })
  fetchSuitCaseList(caseFilter.value)
  if (caseId) fetchSuitCase(Number(caseId))
}

const dataReset = () => {
  docStore.suitcaseList = []
  docStore.suitcaseCount = 0
  caseFilter.value.project = ''
  router.replace({ name: `${mainViewName.value}` })
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

onBeforeRouteUpdate(() => {
  const proj = project.value || projStore.initProjId
  dataSetup(proj, route.params?.caseId)
})

const loading = ref(true)
onBeforeMount(async () => {
  const proj = project.value || projStore.initProjId
  dataSetup(proj, route.params?.caseId)
  loading.value = false
})
</script>

<template>
  <ProDocsAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <div v-if="route.name === `${mainViewName}`" class="pt-3">
          <ListController
            ref="fController"
            :case-filter="caseFilter"
            @list-filter="listFiltering"
          />

          <TableTitleRow title="PR 소송 사건 목록" excel :url="excelUrl" :disabled="!project" />

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
            :suitcase="suitcase as SuitCase"
            :view-route="mainViewName"
            :curr-page="caseFilter.page ?? 1"
            :write-auth="writeAuth"
            @link-hit="linkHit"
            @file-hit="fileHit"
            @cases-renewal="casesRenewal"
          />
        </div>

        <div v-else-if="route.name.includes('작성')">
          <CaseForm
            :sort-name="projName"
            :get-suit-case="getSuitCase"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @on-submit="onSubmit"
          />
        </div>

        <div v-else-if="route.name.includes('수정')">
          <CaseForm
            :sort-name="projName"
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
  </ProDocsAuthGuard>
</template>
