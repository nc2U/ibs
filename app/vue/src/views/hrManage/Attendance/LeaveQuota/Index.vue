<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin3'
import { useCompany } from '@/store/pinia/company.ts'
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

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const listControl = ref<InstanceType<typeof ListController> | null>(null)

const dataFilter = ref<StaffLeaveQuotaFilter>({
  page: 1,
  com: undefined,
  staff: '',
  year: currentYear,
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk ?? undefined)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(() => {
  const sp = new URLSearchParams({ company: String(company.value ?? '') })
  const f = dataFilter.value
  if (f.year) sp.set('year', String(f.year))
  if (f.staff) sp.set('staff', String(f.staff))
  if (f.q) sp.set('search', f.q)
  return `/excel/staff-leave-quotas/?${sp.toString()}`
})

const listFiltering = (payload: StaffLeaveQuotaFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) comStore.fetchStaffLeaveQuotaList(dataFilter.value)
}

const multiSubmit = async (payload: StaffLeaveQuota, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updateStaffLeaveQuota(payload, page, company.value, dataFilter.value)
      : await comStore.createStaffLeaveQuota(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}

const onDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deleteStaffLeaveQuota(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    comStore.fetchStaffLeaveQuotaList(dataFilter.value)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    comStore.fetchStaffLeaveQuotaList({ com: pk, year: dataFilter.value.year }),
    comStore.fetchAllStaffList(pk),
  ])
}

const dataReset = () => {
  comStore.staffLeaveQuotaList = []
  comStore.staffLeaveQuotasCount = 0
  comStore.allStaffLeaveQuotaList = []
  comStore.staffLeaveQuota = null
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
      year: currentYear,
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
        <AddLeaveQuota v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="연차 부여 및 잔여 현황"
          excel
          :url="excelUrl"
          filename="연차_부여_잔여_현황.xlsx"
          :disabled="!company"
        />
        <LeaveQuotaList
          :active-page="dataFilter.page || 1"
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
