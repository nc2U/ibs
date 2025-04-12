<script lang="ts" setup>
import { ref, computed, onBeforeMount } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin2'
import { useProject } from '@/store/pinia/project'
import { useSite, type ContFilter } from '@/store/pinia/project_site'
import { type SiteContract } from '@/store/types/project'
import { numFormat } from '@/utils/baseMixins'
import { write_project_site } from '@/utils/pageAuth'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ListController from './components/ListController.vue'
import AddSiteContract from './components/AddSiteContract.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import SiteContractList from './components/SiteContractList.vue'

const listControl = ref()

const dataFilter = ref<ContFilter>({
  project: null,
  limit: '',
  page: 1,
  own_sort: '',
  search: '',
})

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

const siteStore = useSite()
const getContsTotal = computed(() => siteStore.getContsTotal?.contracted_area)

const excelUrl = computed(() => {
  const url = `/excel/sites-contracts/?project=${project.value}`
  const filter = dataFilter.value
  let queryStr = filter.own_sort ? `&own_sort=${filter.own_sort}` : ''
  queryStr = filter.search ? `${queryStr}&search=${filter.search}` : queryStr
  return `${url}${queryStr}`
})

const listFiltering = (payload: ContFilter) => {
  if (project.value) {
    payload.project = project.value
    dataFilter.value = payload
    siteStore.fetchSiteContList(payload)
  }
}

const pageSelect = (page: number) => {
  dataFilter.value.project = project.value as number
  dataFilter.value.page = page
  if (project.value) siteStore.fetchSiteContList(dataFilter.value)
}

const onCreate = (payload: FormData) => siteStore.createSiteCont(payload)

const onUpdate = (pk: number, payload: FormData) => siteStore.updateSiteCont(pk, payload)

const multiSubmit = (payload: SiteContract) => {
  const { pk, ...data } = payload as { [key: string]: any }

  const form = new FormData()

  for (const key in data) form.set(key, data[key] ?? '')

  if (payload.pk) onUpdate(pk, form)
  else onCreate(form)
}

const onDelete = (payload: { pk: number; project: number }) => {
  const { pk, project } = payload
  siteStore.deleteSiteCont(pk, project)
}

const dataSetup = (pk: number) => {
  siteStore.fetchAllOwners(pk)
  siteStore.fetchSiteContList({ project: pk })
}

const dataReset = () => {
  siteStore.siteContList = []
  siteStore.siteContCount = 0
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
      <AddSiteContract
        v-if="write_project_site"
        :project="project as number"
        @multi-submit="multiSubmit"
      />
      <TableTitleRow title="부지 매입계약 목록" excel :url="excelUrl" :disabled="!project">
        <span v-if="project" class="text-success" style="padding-top: 7px">
          총 계약 면적 :
          {{ numFormat(getContsTotal as number, 2) }}
          m<sup>2</sup> ({{ numFormat((getContsTotal as number) * 0.3025, 2) }}
          평) 등록
        </span>
      </TableTitleRow>
      <SiteContractList
        :limit="dataFilter.limit || 10"
        @page-select="pageSelect"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
    </CCardBody>
  </ContentBody>
</template>
