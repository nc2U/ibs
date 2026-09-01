<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin3'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company.ts'
import type { Company } from '@/store/types/settings.ts'
import { type StaffLeaveQuota, type StaffLeaveQuotaFilter } from '@/store/types/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddLeaveQuota from './components/AddLeaveQuota.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import LeaveQuotaList from './components/LeaveQuotaList.vue'

const currentYear = new Date().getFullYear()

const accStore = useAccount()
const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const dataFilter = ref<StaffLeaveQuotaFilter>({
  page: 1,
  com: 1,
  staff: '',
  year: currentYear,
  q: '',
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(() => {
  const url = `/excel/staff-leave-quotas/?company=${company.value}`
  const filter = dataFilter.value
  let query = ''
  if (filter.year) query += `&year=${filter.year}`
  if (filter.staff) query += `&staff=${filter.staff}`
  if (filter.q) query += `&search=${filter.q}`
  return `${url}${query}`
})

const listFiltering = (payload: StaffLeaveQuotaFilter) => {
  dataFilter.value = payload
  if (company.value)
    fetchStaffLeaveQuotaList({
      page: payload.page,
      com: payload.com,
      staff: payload.staff,
      year: payload.year,
      q: payload.q,
    })
}

const fetchStaffLeaveQuotaList = (payload: StaffLeaveQuotaFilter) =>
  comStore.fetchStaffLeaveQuotaList(payload)
const fetchAllStaffList = (com?: number) => comStore.fetchAllStaffList(com)

const createStaffLeaveQuota = (payload: StaffLeaveQuota, p?: number, c?: number) =>
  comStore.createStaffLeaveQuota(payload, p, c)
const updateStaffLeaveQuota = (payload: StaffLeaveQuota, p?: number, c?: number) =>
  comStore.updateStaffLeaveQuota(payload, p, c)
const deleteStaffLeaveQuota = (pk: number, com: number) =>
  comStore.deleteStaffLeaveQuota(pk, com)

const multiSubmit = (payload: StaffLeaveQuota) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (payload.pk) updateStaffLeaveQuota(payload, page, company.value)
    else createStaffLeaveQuota(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deleteStaffLeaveQuota(pk, company.value)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    fetchStaffLeaveQuotaList(dataFilter.value)
  }
}

const dataSetup = (pk: number) => {
  fetchStaffLeaveQuotaList({ com: pk, year: dataFilter.value.year })
  fetchAllStaffList(pk)
}
const dataReset = () => {
  comStore.staffLeaveQuotaList = []
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
        <AddLeaveQuota
          v-if="canHrWorkCreate"
          :company="comName"
          @multi-submit="multiSubmit"
        />
        <TableTitleRow
          title="연차 부여 및 잔여 현황"
          excel
          :url="excelUrl"
          filename="연차_부여_잔여_현황.xlsx"
          :disabled="!company"
        />
        <LeaveQuotaList
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
