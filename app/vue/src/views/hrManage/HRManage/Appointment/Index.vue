<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue'
import { navMenu1, navMenu2, pageTitle } from '@/views/hrManage/_menu/headermixin2.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Company } from '@/store/types/settings.ts'
import { type PersonnelOrder, type PersonnelOrderFilter } from '@/store/types/company.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddAppointment from './components/AddAppointment.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import AppointmentList from './components/AppointmentList.vue'

const { canGlobal, PERM } = usePerms()
const isHrManager = computed(
  () =>
    canGlobal(PERM.HQ_HR_WORK_READ) ||
    canGlobal(PERM.HQ_HR_WORK_CREATE) ||
    canGlobal(PERM.HQ_HR_WORK_UPDATE),
)
const navMenu = computed(() => (!isHrManager.value ? navMenu1 : navMenu2))
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const dataFilter = ref<PersonnelOrderFilter>({
  page: 1,
  com: 1,
  staff: '',
  order_type: '',
  department: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(() => {
  const url = `/excel/appointments/?company=${company.value}`
  const filter = dataFilter.value
  let query = ''
  query = filter.staff ? `${query}&staff=${filter.staff}` : query
  query = filter.order_type ? `${query}&order_type=${filter.order_type}` : query
  query = filter.department ? `${query}&department=${filter.department}` : query
  query = filter.q ? `${query}&search=${filter.q}` : query
  return `${url}${query}`
})

const listFiltering = (payload: PersonnelOrderFilter) => {
  dataFilter.value = payload
  if (company.value)
    fetchPersonnelOrderList({
      page: payload.page,
      com: payload.com,
      staff: payload.staff,
      order_type: payload.order_type,
      department: payload.department,
      q: payload.q,
    })
}

const fetchPersonnelOrderList = (payload: PersonnelOrderFilter) =>
  comStore.fetchPersonnelOrderList(payload)
const fetchAllDepartList = (com?: number) => comStore.fetchAllDepartList(com)
const fetchAllGradeList = (com?: number) => comStore.fetchAllGradeList(com)
const fetchAllPositionList = (com?: number) => comStore.fetchAllPositionList(com)
const fetchAllDutyList = (com?: number) => comStore.fetchAllDutyList(com)
const fetchAllStaffList = (com?: number) => comStore.fetchAllStaffList(com)

const createPersonnelOrder = (payload: PersonnelOrder, p?: number, c?: number) =>
  comStore.createPersonnelOrder(payload, p, c)
const updatePersonnelOrder = (payload: PersonnelOrder, p?: number, c?: number) =>
  comStore.updatePersonnelOrder(payload, p, c)
const deletePersonnelOrder = (pk: number, com: number) => comStore.deletePersonnelOrder(pk, com)

const multiSubmit = (payload: PersonnelOrder) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (payload.pk) updatePersonnelOrder(payload, page, company.value)
    else createPersonnelOrder(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deletePersonnelOrder(pk, company.value)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    fetchPersonnelOrderList(dataFilter.value)
  }
}

const dataSetup = (pk: number) => {
  fetchPersonnelOrderList({ com: pk })
  fetchAllDepartList(pk)
  fetchAllGradeList(pk)
  fetchAllPositionList(pk)
  fetchAllDutyList(pk)
  fetchAllStaffList(pk)
}
const dataReset = () => {
  comStore.personnelOrderList = []
  comStore.allDepartList = []
  comStore.allGradeList = []
  comStore.allPositionList = []
  comStore.allDutyList = []
  comStore.allStaffList = []
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
  <ComHrAuthGuard>
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
        <AddAppointment v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="인사 발령 목록"
          excel
          :url="excelUrl"
          filename="인사_발령_목록.xlsx"
          :disabled="!company"
        />
        <AppointmentList
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
