<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/hrManage/_menu/headermixin4'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Company } from '@/store/types/settings.ts'
import type { PromotionPolicy, PromotionPolicyFilter } from '@/store/types/company.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddPolicy from './components/AddPolicy.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import PolicyList from './components/PolicyList.vue'

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const dataFilter = ref<PromotionPolicyFilter>({
  page: 1,
  com: 1,
  current_grade: '',
  target_grade: '',
  is_active: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(() => {
  const url = `/excel/staff-promotion-policies/?company=${company.value}`
  const filter = dataFilter.value
  let query = ''
  if (filter.current_grade) query += `&current_grade=${filter.current_grade}`
  if (filter.target_grade) query += `&target_grade=${filter.target_grade}`
  if (filter.is_active !== '' && filter.is_active !== undefined)
    query += `&is_active=${filter.is_active}`
  if (filter.q) query += `&search=${filter.q}`
  return `${url}${query}`
})

const listFiltering = (payload: PromotionPolicyFilter) => {
  dataFilter.value = payload
  if (company.value)
    fetchPromotionPolicyList({
      page: payload.page,
      com: payload.com,
      current_grade: payload.current_grade,
      target_grade: payload.target_grade,
      is_active: payload.is_active,
      q: payload.q,
    })
}

const fetchPromotionPolicyList = (payload: PromotionPolicyFilter) =>
  comStore.fetchPromotionPolicyList(payload)
const fetchAllGradeList = (com?: number) => comStore.fetchAllGradeList(com)

const createPromotionPolicy = (payload: PromotionPolicy, p?: number, c?: number) =>
  comStore.createPromotionPolicy(payload, p, c)
const updatePromotionPolicy = (payload: PromotionPolicy, p?: number, c?: number) =>
  comStore.updatePromotionPolicy(payload, p, c)
const deletePromotionPolicy = (pk: number, com: number) => comStore.deletePromotionPolicy(pk, com)

const multiSubmit = (payload: PromotionPolicy) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (payload.pk) updatePromotionPolicy(payload, page, company.value)
    else createPromotionPolicy(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deletePromotionPolicy(pk, company.value)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    fetchPromotionPolicyList(dataFilter.value)
  }
}

const dataSetup = (pk: number) => {
  fetchPromotionPolicyList({ com: pk })
  fetchAllGradeList(pk)
}
const dataReset = () => {
  comStore.promotionPolicyList = []
  comStore.allGradeList = []
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
        <AddPolicy v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="직급별 승급 기준 및 정책 목록"
          excel
          :url="excelUrl"
          filename="직급별_승급_정책_목록.xlsx"
          :disabled="!company"
        />
        <PolicyList @page-select="pageSelect" @multi-submit="multiSubmit" @on-delete="onDelete" />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
