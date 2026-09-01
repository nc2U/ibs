<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue'
import { pageTitle, navMenu1, navMenu2 } from '@/views/hrManage/_menu/headermixin3'
import { useCompany } from '@/store/pinia/company.ts'
import type { Company } from '@/store/types/settings.ts'
import type { StaffLeaveUsage, StaffLeaveUsageFilter } from '@/store/types/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddLeaveUsage from './components/AddLeaveUsage.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import LeaveUsageList from './components/LeaveUsageList.vue'

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))
const isHrManager = computed(
  () =>
    canGlobal(PERM.HQ_HR_WORK_READ) ||
    canGlobal(PERM.HQ_HR_WORK_CREATE) ||
    canGlobal(PERM.HQ_HR_WORK_UPDATE),
)
const navMenu = computed(() => (!isHrManager.value ? navMenu1 : navMenu2))

const dataFilter = ref<StaffLeaveUsageFilter>({
  page: 1,
  com: 1,
  staff: '',
  leave_type: '',
  start_date: '',
  end_date: '',
  is_cancelled: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(() => {
  const url = `/excel/staff-leave-usages/?company=${company.value}`
  const filter = dataFilter.value
  let query = ''
  if (filter.staff) query += `&staff=${filter.staff}`
  if (filter.leave_type) query += `&leave_type=${filter.leave_type}`
  if (filter.start_date) query += `&start_date=${filter.start_date}`
  if (filter.end_date) query += `&end_date=${filter.end_date}`
  if (filter.is_cancelled !== '') query += `&is_cancelled=${filter.is_cancelled}`
  if (filter.q) query += `&search=${filter.q}`
  return `${url}${query}`
})

const listFiltering = (payload: StaffLeaveUsageFilter) => {
  dataFilter.value = payload
  if (company.value)
    fetchStaffLeaveUsageList({
      page: payload.page,
      com: payload.com,
      staff: payload.staff,
      leave_type: payload.leave_type,
      start_date: payload.start_date,
      end_date: payload.end_date,
      is_cancelled: payload.is_cancelled,
      q: payload.q,
    })
}

const fetchStaffLeaveUsageList = (payload: StaffLeaveUsageFilter) =>
  comStore.fetchStaffLeaveUsageList(payload)
const fetchAllStaffList = (com?: number) => comStore.fetchAllStaffList(com)

const createStaffLeaveUsage = (payload: StaffLeaveUsage, p?: number, c?: number) =>
  comStore.createStaffLeaveUsage(payload, p, c)
const updateStaffLeaveUsage = (payload: StaffLeaveUsage, p?: number, c?: number) =>
  comStore.updateStaffLeaveUsage(payload, p, c)
const deleteStaffLeaveUsage = (pk: number, com: number) => comStore.deleteStaffLeaveUsage(pk, com)

const multiSubmit = (payload: StaffLeaveUsage) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (payload.pk) updateStaffLeaveUsage(payload, page, company.value)
    else createStaffLeaveUsage(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deleteStaffLeaveUsage(pk, company.value)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    fetchStaffLeaveUsageList(dataFilter.value)
  }
}

const dataSetup = (pk: number) => {
  fetchStaffLeaveUsageList({ com: pk })
  fetchAllStaffList(pk)
}
const dataReset = () => {
  comStore.staffLeaveUsageList = []
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
        <ListController @list-filtering="listFiltering" />
        <AddLeaveUsage v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="휴가 사용 내역"
          excel
          :url="excelUrl"
          filename="휴가_사용_내역.xlsx"
          :disabled="!company"
        />
        <LeaveUsageList
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
