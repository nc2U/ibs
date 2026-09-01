<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue'
import { navMenu1, navMenu2, pageTitle } from '@/views/hrManage/_menu/headermixin2.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Company } from '@/store/types/settings.ts'
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

const dataFilter = ref<ExecutiveFilter>({
  page: 1,
  com: 1,
  rank: '',
  director_type: '',
  is_registered: '',
  is_standing: '',
  represent_type: '',
  q: '',
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(() => {
  const url = `/excel/executives/?company=${company.value}`
  const filter = dataFilter.value
  let query = ''
  query = filter.rank ? `${query}&rank=${filter.rank}` : query
  query = filter.director_type ? `${query}&director_type=${filter.director_type}` : query
  query = filter.is_registered !== '' ? `${query}&is_registered=${filter.is_registered}` : query
  query = filter.is_standing !== '' ? `${query}&is_standing=${filter.is_standing}` : query
  query = filter.represent_type ? `${query}&represent_type=${filter.represent_type}` : query
  query = filter.q ? `${query}&search=${filter.q}` : query
  return `${url}${query}`
})

const listFiltering = (payload: ExecutiveFilter) => {
  dataFilter.value = payload
  if (company.value)
    fetchExecutiveList({
      page: payload.page,
      com: payload.com,
      rank: payload.rank,
      director_type: payload.director_type,
      is_registered: payload.is_registered,
      is_standing: payload.is_standing,
      represent_type: payload.represent_type,
      q: payload.q,
    })
}

const fetchExecutiveList = (payload: ExecutiveFilter) => comStore.fetchExecutiveList(payload)
const fetchAllExecutiveRankList = (com?: number) => comStore.fetchAllExecutiveRankList(com)
const fetchAllStaffList = (com?: number) => comStore.fetchAllStaffList(com)

const createExecutive = (payload: Executive, p?: number, c?: number) =>
  comStore.createExecutive(payload, p, c)
const updateExecutive = (payload: Executive, p?: number, c?: number) =>
  comStore.updateExecutive(payload, p, c)
const deleteExecutive = (pk: number, com: number) => comStore.deleteExecutive(pk, com)

const multiSubmit = (payload: Executive) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (payload.pk) updateExecutive(payload, page, company.value)
    else createExecutive(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deleteExecutive(pk, company.value)
}

const pageSelect = (num: number) => {
  if (company.value) {
    dataFilter.value.page = num
    dataFilter.value.com = company.value
    fetchExecutiveList(dataFilter.value)
  }
}

const dataSetup = (pk: number) => {
  fetchExecutiveList({ com: pk })
  fetchAllExecutiveRankList(pk)
  fetchAllStaffList(pk)
}
const dataReset = () => {
  comStore.executiveList = []
  comStore.allExecutiveRankList = []
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
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
