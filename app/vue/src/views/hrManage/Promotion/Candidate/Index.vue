<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin4'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company.ts'
import type { Company } from '@/store/types/settings.ts'
import { type PromotionCandidate, type PromotionCandidateFilter } from '@/store/types/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddCandidate from './components/AddCandidate.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import CandidateList from './components/CandidateList.vue'

const currentYear = new Date().getFullYear()

const accStore = useAccount()
const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const dataFilter = ref<PromotionCandidateFilter>({
  page: 1,
  com: 1,
  eval_year: currentYear,
  status: '',
  policy: '',
  staff: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(() => {
  const url = `/excel/staff-promotion-candidates/?company=${company.value}`
  const filter = dataFilter.value
  let query = ''
  if (filter.eval_year) query += `&eval_year=${filter.eval_year}`
  if (filter.status) query += `&status=${filter.status}`
  if (filter.policy) query += `&policy=${filter.policy}`
  if (filter.staff) query += `&staff=${filter.staff}`
  if (filter.q) query += `&search=${filter.q}`
  return `${url}${query}`
})

const listFiltering = (payload: PromotionCandidateFilter) => {
  dataFilter.value = payload
  if (company.value)
    fetchPromotionCandidateList({
      page: payload.page,
      com: payload.com,
      eval_year: payload.eval_year,
      status: payload.status,
      policy: payload.policy,
      staff: payload.staff,
      q: payload.q,
    })
}

const fetchPromotionCandidateList = (payload: PromotionCandidateFilter) =>
  comStore.fetchPromotionCandidateList(payload)
const fetchAllStaffList = (com?: number) => comStore.fetchAllStaffList(com)
const fetchAllPromotionPolicyList = (com?: number) => comStore.fetchAllPromotionPolicyList(com)

const createPromotionCandidate = (payload: PromotionCandidate, p?: number, c?: number) =>
  comStore.createPromotionCandidate(payload, p, c)
const updatePromotionCandidate = (payload: PromotionCandidate, p?: number, c?: number) =>
  comStore.updatePromotionCandidate(payload, p, c)
const deletePromotionCandidate = (pk: number, com: number) =>
  comStore.deletePromotionCandidate(pk, com)

const multiSubmit = (payload: PromotionCandidate) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (payload.pk) updatePromotionCandidate(payload, page, company.value)
    else createPromotionCandidate(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deletePromotionCandidate(pk, company.value)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    fetchPromotionCandidateList(dataFilter.value)
  }
}

const dataSetup = (pk: number) => {
  fetchPromotionCandidateList({ com: pk, eval_year: dataFilter.value.eval_year })
  fetchAllStaffList(pk)
  fetchAllPromotionPolicyList(pk)
}
const dataReset = () => {
  comStore.promotionCandidateList = []
  comStore.allStaffList = []
  comStore.allPromotionPolicyList = []
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
        <AddCandidate
          v-if="canHrWorkCreate"
          :company="comName"
          @multi-submit="multiSubmit"
        />
        <TableTitleRow
          title="승급 심사 대상 및 발령 목록"
          excel
          :url="excelUrl"
          filename="승급_심사_발령_목록.xlsx"
          :disabled="!company"
        />
        <CandidateList
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
