<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin3'
import { useCompany } from '@/store/pinia/company.ts'
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

const listControl = ref<InstanceType<typeof ListController> | null>(null)

const dataFilter = ref<StaffLeaveUsageFilter>({
  page: 1,
  com: undefined,
  staff: '',
  leave_type: '',
  start_date: '',
  end_date: '',
  is_cancelled: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk ?? undefined)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(() => {
  const sp = new URLSearchParams({ company: String(company.value ?? '') })
  const f = dataFilter.value
  if (f.staff) sp.set('staff', String(f.staff))
  if (f.leave_type) sp.set('leave_type', String(f.leave_type))
  if (f.start_date) sp.set('start_date', f.start_date)
  if (f.end_date) sp.set('end_date', f.end_date)
  if (f.is_cancelled !== '' && f.is_cancelled !== undefined)
    sp.set('is_cancelled', String(f.is_cancelled))
  if (f.q) sp.set('search', f.q)
  return `/excel/staff-leave-usages/?${sp.toString()}`
})

const listFiltering = (payload: StaffLeaveUsageFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) comStore.fetchStaffLeaveUsageList(dataFilter.value)
}

const multiSubmit = async (payload: StaffLeaveUsage, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updateStaffLeaveUsage(payload, page, company.value, dataFilter.value)
      : await comStore.createStaffLeaveUsage(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}

const onDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deleteStaffLeaveUsage(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    comStore.fetchStaffLeaveUsageList(dataFilter.value)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([comStore.fetchStaffLeaveUsageList({ com: pk }), comStore.fetchAllStaffList(pk)])
}

const dataReset = () => {
  comStore.staffLeaveUsageList = []
  comStore.staffLeaveUsagesCount = 0
  comStore.allStaffLeaveUsageList = []
  comStore.staffLeaveUsage = null
  comStore.allStaffList = []
}

const loading = ref(true)
watch(
  company,
  async newVal => {
    dataReset()
    listControl.value?.clearFilter()
    dataFilter.value = {
      page: 1,
      com: newVal,
      staff: '',
      leave_type: '',
      start_date: '',
      end_date: '',
      is_cancelled: '',
      q: '',
    }
    if (newVal) {
      loading.value = true
      await dataSetup(newVal)
    }
    loading.value = false
  },
  { immediate: true },
)
</script>

<template>
  <ComHrAuthGuard require-hr-read>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="CompanySelect" />
    <ContentBody>
      <CCardBody>
        <ListController ref="listControl" @list-filtering="listFiltering" />
        <AddLeaveUsage v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="휴가 사용 내역"
          excel
          :url="excelUrl"
          filename="휴가_사용_내역.xlsx"
          :disabled="!company"
        />
        <LeaveUsageList
          :active-page="dataFilter.page || 1"
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
