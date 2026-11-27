<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/hrManage/_menu/headermixin4.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type StaffEvaluation, type StaffEvaluationFilter } from '@/store/types/company.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddEvaluation from './components/AddEvaluation.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import EvaluationList from './components/EvaluationList.vue'

const currentYear = new Date().getFullYear()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const listControl = ref<InstanceType<typeof ListController> | null>(null)

const dataFilter = ref<StaffEvaluationFilter>({
  page: 1,
  com: undefined,
  eval_year: currentYear,
  eval_period: '',
  grade: '',
  staff: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk ?? undefined)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(() => {
  const sp = new URLSearchParams({ company: String(company.value ?? '') })
  const f = dataFilter.value
  if (f.eval_year) sp.set('eval_year', String(f.eval_year))
  if (f.eval_period) sp.set('eval_period', f.eval_period)
  if (f.grade) sp.set('grade', f.grade)
  if (f.staff) sp.set('staff', String(f.staff))
  if (f.q) sp.set('search', f.q)
  return `/excel/staff-evaluations/?${sp.toString()}`
})

const listFiltering = (payload: StaffEvaluationFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) comStore.fetchStaffEvaluationList(dataFilter.value)
}

const multiSubmit = async (payload: StaffEvaluation, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updateStaffEvaluation(payload, page, company.value, dataFilter.value)
      : await comStore.createStaffEvaluation(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}

const onDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deleteStaffEvaluation(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    comStore.fetchStaffEvaluationList(dataFilter.value)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    comStore.fetchStaffEvaluationList({ com: pk, eval_year: dataFilter.value.eval_year }),
    comStore.fetchAllStaffList(pk),
  ])
}

const dataReset = () => {
  comStore.staffEvaluationList = []
  comStore.staffEvaluationsCount = 0
  comStore.allStaffEvaluationList = []
  comStore.staffEvaluation = null
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
      eval_year: currentYear,
      eval_period: '',
      grade: '',
      staff: '',
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
        <AddEvaluation v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="인사/업적 평가 목록"
          excel
          :url="excelUrl"
          filename="인사_업적_평가_목록.xlsx"
          :disabled="!company"
        />
        <EvaluationList
          :active-page="dataFilter.page || 1"
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
