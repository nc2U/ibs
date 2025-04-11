<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin2'
import { numFormat } from '@/utils/baseMixins'
import { useProject } from '@/store/pinia/project'
import { useSite, type OwnerFilter } from '@/store/pinia/project_site'
import { write_project_site } from '@/utils/pageAuth'
import { type Relation, type SiteOwner } from '@/store/types/project'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ListController from '@/views/projects/SiteOwner/components/ListController.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import AddSiteOwner from '@/views/projects/SiteOwner/components/AddSiteOwner.vue'
import SiteOwnerList from '@/views/projects/SiteOwner/components/SiteOwnerList.vue'

const listControl = ref()

const dataFilter = ref<OwnerFilter>({
  project: null,
  limit: '',
  page: 1,
  sort: '',
  search: '',
})

const projStore = useProject()
const project = computed(() => projStore.project?.pk)
const isReturned = computed(() => projStore.project?.is_returned_area)

const siteStore = useSite()
const getOwnersTotal = computed(() => siteStore.getOwnersTotal?.owned_area)

const excelUrl = computed(() => {
  const url = `/excel/sites-by-owner/?project=${project.value}`
  const filter = dataFilter.value
  let queryStr = filter.sort ? `&own_sort=${filter.sort}` : ''
  queryStr = filter.search ? `${queryStr}&search=${filter.search}` : queryStr
  return `${url}${queryStr}`
})

const listFiltering = (payload: OwnerFilter) => {
  dataFilter.value = payload
  if (project.value) siteStore.fetchSiteOwnerList(payload)
}

const pageSelect = (page: number) => {
  dataFilter.value.project = project.value as number
  dataFilter.value.page = page
  if (project.value) siteStore.fetchSiteOwnerList(dataFilter.value)
}

type inputData = SiteOwner & {
  limit: number
  page: number
  sort: string
  use_consent: '' | '0' | '1'
  search: string
}

const onCreate = (payload: inputData) => siteStore.createSiteOwner(payload)

const onUpdate = (payload: inputData) => siteStore.updateSiteOwner(payload)

const relationPatch = (payload: Relation) => {
  const { page, sort, search } = dataFilter.value
  if (project.value) {
    const data = { project: project.value, page, sort, search, ...payload }
    siteStore.patchRelation(data)
  }
}

const multiSubmit = (payload: SiteOwner) => {
  const { limit, page, sort, search } = dataFilter.value
  const submitData = { ...payload, limit, page, sort, search } as inputData
  if (payload.pk) onUpdate(submitData)
  else onCreate(submitData)
}

const onDelete = (payload: { pk: number; project: number }) => {
  const { pk, project } = payload
  siteStore.deleteSiteOwner(pk, project)
}

const dataSetup = (pk: number) => {
  siteStore.fetchAllSites(pk)
  siteStore.fetchSiteOwnerList({ project: pk })
}

const dataReset = () => {
  siteStore.siteOwnerList = []
  siteStore.siteOwnerCount = 0
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

onBeforeMount(() => dataSetup(project.value || projStore.initProjId))
</script>

<template>
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
        @list-filtering="listFiltering"
      />
      <AddSiteOwner
        v-if="write_project_site"
        :project="project as number"
        @multi-submit="multiSubmit"
      />
      <TableTitleRow title="부지 소유자 목록" excel :url="excelUrl" :disabled="!project">
        <span v-if="project" class="pt-1 text-success">
          소유자 면적 :
          {{ numFormat(getOwnersTotal as number, 2) }}m<sup>2</sup> ({{
            numFormat((getOwnersTotal as number) * 0.3025, 2)
          }}평) 등록
        </span>
      </TableTitleRow>
      <SiteOwnerList
        :is-returned="isReturned"
        :limit="dataFilter.limit || 10"
        @page-select="pageSelect"
        @relation-patch="relationPatch"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
    </CCardBody>
  </ContentBody>
</template>
