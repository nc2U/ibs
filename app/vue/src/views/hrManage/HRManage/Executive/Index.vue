<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { navMenu1, navMenu2, pageTitle } from '@/views/hrManage/_menu/headermixin2.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Executive, type ExecutiveFilter } from '@/store/types/company.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddExecutive from './components/AddExecutive.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ExecutiveList from './components/ExecutiveList.vue'

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

const dataFilter = ref<ExecutiveFilter>({
  page: 1,
  com: undefined,
  rank: '',
  executive_type: '',
  is_registered: '',
  is_standing: '',
  represent_type: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk ?? undefined)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(() => {
  const sp = new URLSearchParams({ company: String(company.value ?? '') })
  const f = dataFilter.value
  if (f.rank) sp.set('rank', String(f.rank))
  if (f.executive_type) sp.set('executive_type', String(f.executive_type))
  if (f.is_registered !== '' && f.is_registered !== undefined)
    sp.set('is_registered', String(f.is_registered))
  if (f.is_standing !== '' && f.is_standing !== undefined)
    sp.set('is_standing', String(f.is_standing))
  if (f.represent_type) sp.set('represent_type', String(f.represent_type))
  if (f.q) sp.set('search', f.q)
  return `/excel/executives/?${sp.toString()}`
})

const listFiltering = (payload: ExecutiveFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) comStore.fetchExecutiveList(dataFilter.value)
}

const multiSubmit = async (payload: Executive, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updateExecutive(payload, page, company.value, dataFilter.value)
      : await comStore.createExecutive(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}

const onDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deleteExecutive(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    comStore.fetchExecutiveList(dataFilter.value)
  }
}

const dataSetup = async (pk: number) => {
  await Promise.all([
    comStore.fetchExecutiveList({ com: pk }),
    comStore.fetchAllExecutiveRankList(pk),
    comStore.fetchAllStaffList(pk),
  ])
}

const dataReset = () => {
  comStore.executiveList = []
  comStore.executivesCount = 0
  comStore.allExecutiveList = []
  comStore.executive = null
  comStore.allExecutiveRankList = []
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
      rank: '',
      executive_type: '',
      is_registered: '',
      is_standing: '',
      represent_type: '',
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
        <AddExecutive v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="임원 재임 목록"
          excel
          :url="excelUrl"
          filename="임원_재임_목록.xlsx"
          :disabled="!company"
        />
        <ExecutiveList
          :active-page="dataFilter.page || 1"
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
