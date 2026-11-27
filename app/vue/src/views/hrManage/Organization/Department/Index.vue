<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin1.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type Department as Depart, type DepFilter } from '@/store/types/company.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddDepartment from './components/AddDepartment.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import DepartmentList from './components/DepartmentList.vue'

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const listControl = ref<InstanceType<typeof ListController> | null>(null)

const dataFilter = ref<DepFilter>({
  page: 1,
  com: undefined,
  upp: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk ?? undefined)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(() => {
  const sp = new URLSearchParams({ company: String(company.value ?? '') })
  if (dataFilter.value.upp) sp.set('upper_depart', String(dataFilter.value.upp))
  if (dataFilter.value.q) sp.set('search', dataFilter.value.q)
  return `/excel/departs/?${sp.toString()}`
})

const listFiltering = (payload: DepFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) comStore.fetchDepartmentList(dataFilter.value)
}

const multiSubmit = async (payload: Depart, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updateDepartment(payload, page, company.value, dataFilter.value)
      : await comStore.createDepartment(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}

const onDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deleteDepartment(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const pageSelect = (num: number) => {
  dataFilter.value.page = num
  if (company.value) {
    dataFilter.value.com = company.value
    comStore.fetchDepartmentList(dataFilter.value)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    comStore.fetchAllDepartList(pk),
    comStore.fetchDepartmentList({ com: pk }),
    comStore.fetchAllStaffList(pk),
  ])
}

const dataReset = () => {
  comStore.departmentList = []
  comStore.departmentsCount = 0
  comStore.allDepartList = []
  comStore.department = null
  comStore.allStaffList = []
}

const loading = ref(true)
watch(
  company,
  async newVal => {
    dataReset()
    listControl.value?.clearFilter()
    dataFilter.value = { page: 1, com: newVal, upp: '', q: '' }
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
        <ListController ref="listControl" @list-filtering="listFiltering" />
        <AddDepartment v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="부서 목록"
          excel
          :url="excelUrl"
          filename="부서_목록.xlsx"
          :disabled="!company"
        />
        <DepartmentList
          :active-page="dataFilter.page || 1"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
          @page-select="pageSelect"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
