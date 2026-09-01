<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin4'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company.ts'
import type { Company } from '@/store/types/settings.ts'
import { type StaffEvaluation, type StaffEvaluationFilter } from '@/store/types/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddEvaluation from './components/AddEvaluation.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import EvaluationList from './components/EvaluationList.vue'

const currentYear = new Date().getFullYear()

const accStore = useAccount()
const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const dataFilter = ref<StaffEvaluationFilter>({
  page: 1,
  com: 1,
  eval_year: currentYear,
  eval_period: '',
  grade: '',
  staff: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(() => {
  const url = `/excel/staff-evaluations/?company=${company.value}`
  const filter = dataFilter.value
  let query = ''
  if (filter.eval_year) query += `&eval_year=${filter.eval_year}`
  if (filter.eval_period) query += `&eval_period=${filter.eval_period}`
  if (filter.grade) query += `&grade=${filter.grade}`
  if (filter.staff) query += `&staff=${filter.staff}`
  if (filter.q) query += `&search=${filter.q}`
  return `${url}${query}`
})

const listFiltering = (payload: StaffEvaluationFilter) => {
  dataFilter.value = payload
  if (company.value)
    fetchStaffEvaluationList({
      page: payload.page,
      com: payload.com,
      eval_year: payload.eval_year,
      eval_period: payload.eval_period,
      grade: payload.grade,
      staff: payload.staff,
      q: payload.q,
    })
}

const fetchStaffEvaluationList = (payload: StaffEvaluationFilter) =>
  comStore.fetchStaffEvaluationList(payload)
const fetchAllStaffList = (com?: number) => comStore.fetchAllStaffList(com)

const createStaffEvaluation = (payload: StaffEvaluation, p?: number, c?: number) =>
  comStore.createStaffEvaluation(payload, p, c)
const updateStaffEvaluation = (payload: StaffEvaluation, p?: number, c?: number) =>
  comStore.updateStaffEvaluation(payload, p, c)
const deleteStaffEvaluation = (pk: number, com: number) =>
  comStore.deleteStaffEvaluation(pk, com)

const multiSubmit = (payload: StaffEvaluation) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (payload.pk) updateStaffEvaluation(payload, page, company.value)
    else createStaffEvaluation(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deleteStaffEvaluation(pk, company.value)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    fetchStaffEvaluationList(dataFilter.value)
  }
}

const dataSetup = (pk: number) => {
  fetchStaffEvaluationList({ com: pk, eval_year: dataFilter.value.eval_year })
  fetchAllStaffList(pk)
}
const dataReset = () => {
  comStore.staffEvaluationList = []
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
        <AddEvaluation
          v-if="canHrWorkCreate"
          :company="comName"
          @multi-submit="multiSubmit"
        />
        <TableTitleRow
          title="인사/업적 평가 목록"
          excel
          :url="excelUrl"
          filename="인사_업적_평가_목록.xlsx"
          :disabled="!company"
        />
        <EvaluationList
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
