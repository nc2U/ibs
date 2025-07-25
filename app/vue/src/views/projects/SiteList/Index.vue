<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin2'
import { useProject } from '@/store/pinia/project'
import { useSite, type SiteFilter } from '@/store/pinia/project_site'
import type { Project, Site } from '@/store/types/project'
import { numFormat } from '@/utils/baseMixins'
import { write_project_site } from '@/utils/pageAuth'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ListController from './components/ListController.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import AddSite from './components/AddSite.vue'
import SiteList from './components/SiteList.vue'

const listControl = ref()

const dataFilter = ref<SiteFilter>({
  project: null,
  limit: '',
  page: 1,
  search: '',
})

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)
const isReturned = computed(() => (projStore.project as Project)?.is_returned_area)

const siteStore = useSite()
const getSitesTotal = computed(() => siteStore.getSitesTotal)
const totalArea = computed(() =>
  isReturned.value ? getSitesTotal.value?.returned : getSitesTotal.value?.official,
)

const rights = ref(false)
const excelUrl = computed(
  () =>
    `/excel/sites/?project=${project.value}&search=${dataFilter.value.search}&rights=${rights.value || ''}`,
)

const listFiltering = (payload: SiteFilter) => {
  payload.project = project.value as number
  dataFilter.value = payload
  if (project.value) siteStore.fetchSiteList(payload)
}

const pageSelect = (page: number) => {
  dataFilter.value.page = page
  if (project.value) siteStore.fetchSiteList({ project: project.value, page })
  listControl.value.listFiltering(page)
}

const onCreate = (payload: { form: FormData; page?: number; search?: string }) =>
  siteStore.createSite(payload)

const onUpdate = (pk: number, payload: { form: FormData; page?: number; search?: string }) =>
  siteStore.updateSite(pk, payload)

const multiSubmit = (payload: Site) => {
  const { page, search } = dataFilter.value
  const { pk, ...data } = payload as { [key: string]: any }

  const form = new FormData()
  for (const key in data) {
    const value = data[key]

    // null, undefined, 빈 문자열은 제외 (숫자 필드 오류 방지 목적)
    if (value !== null && value !== undefined && value !== '') form.set(key, value)
  }

  const submitData = { form, page, search }

  if (pk) onUpdate(pk, submitData)
  else onCreate(submitData)
}

const onDelete = (payload: { pk: number; project: number }) => {
  const { pk, project } = payload
  siteStore.deleteSite(pk, project)
}

const dataSetup = (pk: number) => siteStore.fetchSiteList({ project: pk })

const dataReset = () => {
  siteStore.siteList = []
  siteStore.siteCount = 0
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  await dataSetup(project.value || projStore.initProjId)
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
  />

  <ContentBody>
    <CCardBody class="pb-5">
      <ListController
        ref="listControl"
        :project="project as number"
        :is-returned="isReturned"
        @list-filtering="listFiltering"
      />
      <AddSite v-if="write_project_site" :project="project as number" @multi-submit="multiSubmit" />
      <TableTitleRow title="사업 부지 목록" excel :url="excelUrl" :disabled="!project">
        <span v-if="project" class="text-success" style="padding-top: 7px">
          총 면적 : {{ numFormat(totalArea as number, 2) }}m<sup>2</sup> ({{
            numFormat((totalArea as number) * 0.3025, 2)
          }}
          평) 등록
        </span>
        <span style="padding-top: 7px">
          <CFormCheck v-model="rights" id="include-rights" label="권리제한사항 포함" class="ml-3" />
        </span>
      </TableTitleRow>
      <SiteList
        :is-returned="isReturned"
        :limit="dataFilter.limit || 10"
        @page-select="pageSelect"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
    </CCardBody>
  </ContentBody>
</template>
