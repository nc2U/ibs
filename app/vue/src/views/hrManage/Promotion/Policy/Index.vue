<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/hrManage/_menu/headermixin4.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
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

const listControl = ref<InstanceType<typeof ListController> | null>(null)

const dataFilter = ref<PromotionPolicyFilter>({
  page: 1,
  com: undefined,
  current_grade: '',
  target_grade: '',
  is_active: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk ?? undefined)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(() => {
  const sp = new URLSearchParams({ company: String(company.value ?? '') })
  const f = dataFilter.value
  if (f.current_grade) sp.set('current_grade', String(f.current_grade))
  if (f.target_grade) sp.set('target_grade', String(f.target_grade))
  if (f.is_active !== '' && f.is_active !== undefined)
    sp.set('is_active', String(f.is_active))
  if (f.q) sp.set('search', f.q)
  return `/excel/staff-promotion-policies/?${sp.toString()}`
})

const listFiltering = (payload: PromotionPolicyFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) comStore.fetchPromotionPolicyList(dataFilter.value)
}

const multiSubmit = async (payload: PromotionPolicy, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updatePromotionPolicy(payload, page, company.value, dataFilter.value)
      : await comStore.createPromotionPolicy(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}

const onDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deletePromotionPolicy(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    comStore.fetchPromotionPolicyList(dataFilter.value)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([comStore.fetchPromotionPolicyList({ com: pk }), comStore.fetchAllGradeList(pk)])
}

const dataReset = () => {
  comStore.promotionPolicyList = []
  comStore.promotionPoliciesCount = 0
  comStore.allPromotionPolicyList = []
  comStore.promotionPolicy = null
  comStore.allGradeList = []
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
      current_grade: '',
      target_grade: '',
      is_active: '',
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
        <AddPolicy v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="직급별 승급 기준 및 정책 목록"
          excel
          :url="excelUrl"
          filename="직급별_승급_정책_목록.xlsx"
          :disabled="!company"
        />
        <PolicyList
          :active-page="dataFilter.page || 1"
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
