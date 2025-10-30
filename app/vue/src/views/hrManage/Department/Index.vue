<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin1'
import { useCompany } from '@/store/pinia/company'
import { write_human_resource } from '@/utils/pageAuth'
import type { Company } from '@/store/types/settings.ts'
import { type Department as Depart, type DepFilter } from '@/store/types/company'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import HrAuthGuard from '@/components/AuthGuard/HrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddDepartment from './components/AddDepartment.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import DepartmentList from './components/DepartmentList.vue'

const listControl = ref()

const dataFilter = ref<DepFilter>({
  page: 1,
  com: undefined,
  upp: '',
  q: '',
})

const comStore = useCompany()
const getPkDeparts = computed(() => comStore.getPkDeparts)
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(() => {
  const url = `/excel/departs/?company=${company.value}`
  const filter = dataFilter.value
  let queryStr = filter.upp ? `&upper_depart=${filter.upp}` : ''
  queryStr = filter.q ? `${queryStr}&search=${filter.q}` : queryStr
  return `${url}${queryStr}`
})

const listFiltering = (payload: DepFilter) => {
  dataFilter.value = payload
  if (company.value)
    fetchDepartmentList({
      page: payload.page,
      com: payload.com,
      upp: payload.upp,
      q: payload.q,
    })
}

const fetchDepartmentList = (payload: DepFilter) => comStore.fetchDepartmentList(payload)
const fetchAllDepartList = (com?: number) => comStore.fetchAllDepartList(com)

const createDepartment = (payload: Depart, p?: number, c?: number) =>
  comStore.createDepartment(payload, p, c)
const updateDepartment = (payload: Depart, p?: number, c?: number) =>
  comStore.updateDepartment(payload, p, c)
const deleteDepartment = (pk: number, com: number) => comStore.deleteDepartment(pk, com)

const multiSubmit = (payload: Depart) => {
  const { page } = dataFilter.value
  if (!!payload.pk) updateDepartment(payload, page, company.value as number)
  else {
    if (payload.upper_depart) payload.level = getLevel(payload.upper_depart)
    createDepartment(payload, page, company.value as number)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deleteDepartment(pk, company.value)
}

const pageSelect = (num: number) => {
  dataFilter.value.page = num
  if (company.value) {
    dataFilter.value.com = company.value
    fetchDepartmentList(dataFilter.value)
  }
}

const getLevel = (up: number) => getPkDeparts.value.filter(d => d.value === up)[0].level + 1

const dataSetup = (pk: number) => {
  fetchAllDepartList(pk)
  fetchDepartmentList({ com: pk })
}

const dataReset = () => {
  comStore.departmentList = []
  comStore.allDepartList = []
}

const comSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onMounted(async () => {
  dataFilter.value.com = comStore.initComId
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
        <AddDepartment v-if="write_human_resource" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow title="부서 목록" excel :url="excelUrl" filename="부서_목록.xlsx" :disabled="!company" />
        <DepartmentList
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
          @page-select="pageSelect"
        />
      </CCardBody>
    </ContentBody>
  </HrAuthGuard>
</template>
