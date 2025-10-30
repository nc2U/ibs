<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin2'
import { useCompany } from '@/store/pinia/company'
import { write_human_resource } from '@/utils/pageAuth'
import type { Company } from '@/store/types/settings.ts'
import type { Grade, ComFilter } from '@/store/types/company'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import HrAuthGuard from '@/components/AuthGuard/HrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddGrade from './components/AddGrade.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import GradeList from './components/GradeList.vue'

// 직급 = Grade
const listControl = ref()

const dataFilter = ref<ComFilter>({
  page: 1,
  com: 1,
  q: '',
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(
  () => `/excel/grades/?company=${company.value}&search=${dataFilter.value.q}`,
)

const listFiltering = (payload: ComFilter) => {
  dataFilter.value = payload
  if (company.value)
    fetchGradeList({
      page: payload.page,
      com: payload.com,
      q: payload.q,
    })
}

const fetchGradeList = (payload: ComFilter) => comStore.fetchGradeList(payload)
const fetchAllPositionList = (com?: number) => comStore.fetchAllPositionList(com)

const createGrade = (payload: Grade, p?: number, c?: number) => comStore.createGrade(payload, p, c)
const updateGrade = (payload: Grade, p?: number, c?: number) => comStore.updateGrade(payload, p, c)
const deleteGrade = (pk: number, com: number) => comStore.deleteGrade(pk, com)

const multiSubmit = (payload: Grade) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (!!payload.pk) updateGrade(payload, page, company.value)
    else createGrade(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deleteGrade(pk, company.value)
}

const pageSelect = (num: number) => {
  dataFilter.value.page = num
  if (company.value) {
    dataFilter.value.com = company.value
    fetchGradeList(dataFilter.value)
  }
}

const dataSetup = (pk: number) => {
  fetchGradeList({ com: pk })
  fetchAllPositionList(pk)
}

const dataReset = () => {
  comStore.gradeList = []
  comStore.allPositionList = []
}

const comSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onMounted(async () => {
  dataSetup(company.value || comStore.initComId)
  loading.value = false
})
</script>

<template>
  <HrAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="CompanySelect"
      @com-select="comSelect"
    />
    <ContentBody>
      <CCardBody>
        <ListController ref="listControl" @list-filtering="listFiltering" />
        <AddGrade v-if="write_human_resource" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow title="직급 목록" excel :url="excelUrl" filename="직급_목록" :disabled="!company" />
        <GradeList @multi-submit="multiSubmit" @on-delete="onDelete" @page-select="pageSelect" />
      </CCardBody>
    </ContentBody>
  </HrAuthGuard>
</template>
