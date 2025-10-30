<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin1'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import { write_human_resource } from '@/utils/pageAuth'
import type { Company } from '@/store/types/settings.ts'
import { type Staff, type StaffFilter } from '@/store/types/company'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import HrAuthGuard from '@/components/AuthGuard/HrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddStaff from './components/AddStaff.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import StaffList from './components/StaffList.vue'

const refListControl = ref()

const dataFilter = ref<StaffFilter>({
  page: 1,
  com: 1,
  sort: '',
  dep: '',
  gra: '',
  pos: '',
  dut: '',
  sts: '1',
  q: '',
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(() => {
  const url = `/excel/staffs/?company=${company.value}`
  const filter = dataFilter.value
  let query = ''
  query = filter.sort ? `${query}&sort=${filter.sort}` : query
  query = filter.dep ? `${query}&department=${filter.dep}` : query
  query = filter.gra ? `${query}&grade=${filter.gra}` : query
  query = filter.pos ? `${query}&position=${filter.pos}` : query
  query = filter.dut ? `${query}&duty=${filter.dut}` : query
  query = filter.sts ? `${query}&status=${filter.sts}` : query
  query = filter.q ? `${query}&search=${filter.q}` : query
  return `${url}${query}`
})

const accStore = useAccount()
const fetchUsersList = () => accStore.fetchUsersList()

const listFiltering = (payload: StaffFilter) => {
  dataFilter.value = payload
  if (company.value)
    fetchStaffList({
      page: payload.page,
      com: payload.com,
      sort: payload.sort,
      dep: payload.dep,
      gra: payload.gra,
      pos: payload.pos,
      dut: payload.dut,
      sts: payload.sts,
      q: payload.q,
    })
}

const fetchStaffList = (payload: StaffFilter) => comStore.fetchStaffList(payload)
const fetchAllGradeList = (com?: number) => comStore.fetchAllGradeList(com)
const fetchAllDepartList = (com?: number) => comStore.fetchAllDepartList(com)
const fetchAllPositionList = (com?: number) => comStore.fetchAllPositionList(com)
const fetchAllDutyList = (com?: number) => comStore.fetchAllDutyList(com)

const createStaff = (payload: Staff, p?: number, c?: number) => comStore.createStaff(payload, p, c)
const updateStaff = (payload: Staff, p?: number, c?: number) => comStore.updateStaff(payload, p, c)
const deleteStaff = (pk: number, com: number) => comStore.deleteStaff(pk, com)

const multiSubmit = (payload: Staff) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (payload.pk) updateStaff(payload, page, company.value)
    else createStaff(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deleteStaff(pk, company.value)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    fetchStaffList(dataFilter.value)
  }
}

const dataSetup = (pk: number) => {
  fetchStaffList({ com: pk, sts: '1' })
  fetchAllGradeList(pk)
  fetchAllDepartList(pk)
  fetchAllPositionList(pk)
  fetchAllDutyList(pk)
}
const dataReset = () => {
  comStore.staffList = []
  comStore.allGradeList = []
  comStore.allDepartList = []
  comStore.allPositionList = []
  comStore.allDutyList = []
}

const comSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onMounted(async () => {
  await fetchUsersList()
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
        <ListController ref="refListControl" @list-filtering="listFiltering" />
        <AddStaff v-if="write_human_resource" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow title="직원 목록" excel :url="excelUrl" :disabled="!company" />
        <StaffList @multi-submit="multiSubmit" @on-delete="onDelete" @page-select="pageSelect" />
      </CCardBody>
    </ContentBody>
  </HrAuthGuard>
</template>
