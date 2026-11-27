<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin3'
import { useCompany } from '@/store/pinia/company.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ListController from './components/ListController.vue'
import AttendanceSummary from './components/AttendanceSummary.vue'
import AttendanceStatusBoard from './components/AttendanceStatusBoard.vue'

const currentYear = new Date().getFullYear()
const listControl = ref<InstanceType<typeof ListController> | null>(null)

const filter = ref({
  year: currentYear,
  department: '',
  status: '1',
  search: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk)
const allStaffList = computed(() => comStore.allStaffList)
const allStaffLeaveQuotaList = computed(() => comStore.allStaffLeaveQuotaList)

// 필터링된 직원 목록 계산
const filteredStaffList = computed(() => {
  let list = allStaffList.value
  if (filter.value.status) {
    list = list.filter(s => s.status === filter.value.status)
  }
  if (filter.value.department) {
    const deptPk = Number(filter.value.department)
    const deptObj = comStore.allDepartList.find(d => d.pk === deptPk)
    const deptName = deptObj?.name || String(filter.value.department)
    list = list.filter(
      s =>
        s.department === deptName ||
        s.assignments?.some(a => a.department === deptPk || a.department_name === deptName),
    )
  }
  if (filter.value.search) {
    const q = filter.value.search.toLowerCase()
    list = list.filter(s => s.name?.toLowerCase().includes(q) || s.personal_phone?.includes(q))
  }
  return list
})

const excelUrl = computed(() => {
  const sp = new URLSearchParams({
    company: String(company.value ?? ''),
    year: String(filter.value.year),
  })
  if (filter.value.department) sp.set('department', String(filter.value.department))
  if (filter.value.status) sp.set('status', filter.value.status)
  if (filter.value.search) sp.set('search', filter.value.search)
  return `/excel/staff-attendance-status/?${sp.toString()}`
})

const listFiltering = (payload: {
  year: number
  department: string
  status: string
  search: string
}) => {
  const prevYear = filter.value.year
  filter.value = payload
  if (company.value && prevYear !== payload.year) {
    // 연도가 바뀌었으면 해당 연도 Quota 재조회
    comStore.fetchAllStaffLeaveQuotaList(company.value, payload.year)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    comStore.fetchAllStaffList(pk, ''),
    comStore.fetchAllDepartList(pk),
    comStore.fetchAllStaffLeaveQuotaList(pk, filter.value.year),
  ])
}

const dataReset = () => {
  comStore.allStaffList = []
  comStore.allStaffLeaveQuotaList = []
  comStore.allDepartList = []
}

const loading = ref(true)
watch(
  company,
  async newVal => {
    dataReset()
    listControl.value?.clearFilter()
    filter.value = { year: currentYear, department: '', status: '1', search: '' }
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
      <CCardBody class="pb-5">
        <ListController ref="listControl" @list-filtering="listFiltering" />

        <!-- 상단 요약 카드 (인원 현황 및 연차 소진율) -->
        <AttendanceSummary
          :staff-list="allStaffList"
          :quota-list="allStaffLeaveQuotaList"
          :year="filter.year"
        />

        <TableTitleRow
          :title="`${filter.year}년도 연차 및 근태 종합 현황`"
          excel
          :url="excelUrl"
          :filename="`${filter.year}년도_연차_근태_종합현황.xlsx`"
          :disabled="!company"
        />

        <!-- 상세 목록 테이블 -->
        <AttendanceStatusBoard
          :staff-list="filteredStaffList"
          :quota-list="allStaffLeaveQuotaList"
          :year="filter.year"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
