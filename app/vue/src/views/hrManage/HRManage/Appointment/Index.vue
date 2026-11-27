<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { navMenu1, navMenu2, pageTitle } from '@/views/hrManage/_menu/headermixin2.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
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

const refListControl = ref<InstanceType<typeof ListController> | null>(null)

const dataFilter = ref<PersonnelOrderFilter>({
  page: 1,
  com: undefined,
  staff: '',
  order_type: '',
  department: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk ?? undefined)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(() => {
  const sp = new URLSearchParams({ company: String(company.value ?? '') })
  const f = dataFilter.value
  if (f.staff) sp.set('staff', String(f.staff))
  if (f.order_type) sp.set('order_type', String(f.order_type))
  if (f.department) sp.set('department', String(f.department))
  if (f.q) sp.set('search', f.q)
  return `/excel/appointments/?${sp.toString()}`
})

const listFiltering = (payload: PersonnelOrderFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) comStore.fetchPersonnelOrderList(dataFilter.value)
}

const multiSubmit = async (payload: PersonnelOrder, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updatePersonnelOrder(payload, page, company.value, dataFilter.value)
      : await comStore.createPersonnelOrder(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}

const onDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deletePersonnelOrder(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    comStore.fetchPersonnelOrderList(dataFilter.value)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    comStore.fetchPersonnelOrderList({ com: pk }),
    comStore.fetchAllDepartList(pk),
    comStore.fetchAllGradeList(pk),
    comStore.fetchAllPositionList(pk),
    comStore.fetchAllDutyList(pk),
    comStore.fetchAllStaffList(pk, ''),
  ])
}

const dataReset = () => {
  comStore.personnelOrderList = []
  comStore.personnelOrdersCount = 0
  comStore.allPersonnelOrderList = []
  comStore.personnelOrder = null
  comStore.allDepartList = []
  comStore.allGradeList = []
  comStore.allPositionList = []
  comStore.allDutyList = []
  comStore.allStaffList = []
}

const loading = ref(true)
watch(
  company,
  async newVal => {
    dataReset()
    refListControl.value?.clearFilter()
    dataFilter.value = {
      page: 1,
      com: newVal,
      staff: '',
      order_type: '',
      department: '',
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
          :active-page="dataFilter.page || 1"
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
