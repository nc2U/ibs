<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/hrManage/_menu/headermixin4.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type PromotionCandidate, type PromotionCandidateFilter } from '@/store/types/company.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddCandidate from './components/AddCandidate.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import CandidateList from './components/CandidateList.vue'

const currentYear = new Date().getFullYear()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const listControl = ref<InstanceType<typeof ListController> | null>(null)

const dataFilter = ref<PromotionCandidateFilter>({
  page: 1,
  com: undefined,
  eval_year: currentYear,
  status: '',
  policy: '',
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
  if (f.status) sp.set('status', f.status)
  if (f.policy) sp.set('policy', String(f.policy))
  if (f.staff) sp.set('staff', String(f.staff))
  if (f.q) sp.set('search', f.q)
  return `/excel/staff-promotion-candidates/?${sp.toString()}`
})

const listFiltering = (payload: PromotionCandidateFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) comStore.fetchPromotionCandidateList(dataFilter.value)
}

const multiSubmit = async (payload: PromotionCandidate, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updatePromotionCandidate(payload, page, company.value, dataFilter.value)
      : await comStore.createPromotionCandidate(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}

const onDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deletePromotionCandidate(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    comStore.fetchPromotionCandidateList(dataFilter.value)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    comStore.fetchPromotionCandidateList({ com: pk, eval_year: dataFilter.value.eval_year }),
    comStore.fetchAllStaffList(pk),
    comStore.fetchAllPromotionPolicyList(pk),
  ])
}

const dataReset = () => {
  comStore.promotionCandidateList = []
  comStore.promotionCandidatesCount = 0
  comStore.allPromotionCandidateList = []
  comStore.promotionCandidate = null
  comStore.allStaffList = []
  comStore.allPromotionPolicyList = []
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
      status: '',
      policy: '',
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
        <AddCandidate v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="승급 심사 대상 및 발령 목록"
          excel
          :url="excelUrl"
          filename="승급_심사_발령_목록.xlsx"
          :disabled="!company"
        />
        <CandidateList
          :active-page="dataFilter.page || 1"
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
