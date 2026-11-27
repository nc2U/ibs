<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { pageTitle, navMenu1, navMenu2 } from '@/views/hrManage/_menu/headermixin2.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Staff, type StaffFilter } from '@/store/types/company.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddStaff from './components/AddStaff.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import StaffList from './components/StaffList.vue'

const accStore = useAccount()
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

const dataFilter = ref<StaffFilter>({
  page: 1,
  com: undefined,
  sort: '',
  dep: '',
  gra: '',
  pos: '',
  dut: '',
  sts: '1',
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk ?? undefined)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(() => {
  const sp = new URLSearchParams({ company: String(company.value ?? '') })
  const f = dataFilter.value
  if (f.sort) sp.set('sort', String(f.sort))
  if (f.dep) sp.set('department', String(f.dep))
  if (f.gra) sp.set('grade', String(f.gra))
  if (f.pos) sp.set('position', String(f.pos))
  if (f.dut) sp.set('duty', String(f.dut))
  if (f.sts) sp.set('status', String(f.sts))
  if (f.q) sp.set('search', f.q)
  return `/excel/staffs/?${sp.toString()}`
})

const listFiltering = (payload: StaffFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) comStore.fetchStaffList(dataFilter.value)
}

const multiSubmit = async (payload: Staff, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updateStaff(payload, page, company.value, dataFilter.value)
      : await comStore.createStaff(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}

const onDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deleteStaff(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    comStore.fetchStaffList(dataFilter.value)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    accStore.usersList.length ? Promise.resolve() : accStore.fetchUsersList(),
    comStore.fetchStaffList({ com: pk, sts: '1' }),
    comStore.fetchAllGradeList(pk),
    comStore.fetchAllDepartList(pk),
    comStore.fetchAllPositionList(pk),
    comStore.fetchAllDutyList(pk),
  ])
}

const dataReset = () => {
  comStore.staffList = []
  comStore.staffsCount = 0
  comStore.allStaffList = []
  comStore.staff = null
  comStore.allGradeList = []
  comStore.allDepartList = []
  comStore.allPositionList = []
  comStore.allDutyList = []
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
      sort: '',
      dep: '',
      gra: '',
      pos: '',
      dut: '',
      sts: '1',
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
  <ComHrAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="CompanySelect" />
    <ContentBody>
      <CCardBody>
        <ListController ref="refListControl" @list-filtering="listFiltering" />
        <AddStaff v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="직원 목록"
          excel
          :url="excelUrl"
          filename="직원_목록.xlsx"
          :disabled="!company"
        />
        <StaffList
          :active-page="dataFilter.page || 1"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
          @page-select="pageSelect"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
