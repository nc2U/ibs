<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin2'
import { useCompany } from '@/store/pinia/company'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Company } from '@/store/types/settings.ts'
import { type Position, type ComFilter } from '@/store/types/company'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddPosition from './components/AddPosition.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import PositionList from './components/PositionList.vue'

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HR_WORK_CREATE))

const dataFilter = ref<ComFilter>({
  page: 1,
  com: 1,
  q: '',
})

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comName = computed(() => (comStore.company as Company)?.name || undefined)

const excelUrl = computed(
  () => `/excel/positions/?company=${company.value}&search=${dataFilter.value.q}`,
)

const listFiltering = (payload: ComFilter) => {
  dataFilter.value = payload
  if (company.value)
    fetchPositionList({
      page: payload.page,
      com: payload.com,
      q: payload.q,
    })
}

const fetchAllGradeList = (com?: number) => comStore.fetchAllGradeList(com)
const fetchPositionList = (payload: ComFilter) => comStore.fetchPositionList(payload)

const createPosition = (payload: Position, p?: number, c?: number) =>
  comStore.createPosition(payload, p, c)
const updatePosition = (payload: Position, p?: number, c?: number) =>
  comStore.updatePosition(payload, p, c)
const deletePosition = (pk: number, com: number) => comStore.deletePosition(pk, com)

const multiSubmit = (payload: Position) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (!!payload.pk) updatePosition(payload, page, company.value)
    else createPosition(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deletePosition(pk, company.value)
}

const pageSelect = (num: number) => {
  dataFilter.value.page = num
  if (company.value) {
    dataFilter.value.com = company.value
    fetchPositionList(dataFilter.value)
  }
}

const dataSetup = (pk: number) => {
  fetchAllGradeList(pk)
  fetchPositionList({ com: pk })
}

const dataReset = () => {
  comStore.allGradeList = []
  comStore.positionList = []
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
        <AddPosition v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="직위 목록"
          excel
          :url="excelUrl"
          filename="직위_목록.xlsx"
          :disabled="!company"
        />
        <PositionList @multi-submit="multiSubmit" @on-delete="onDelete" @page-select="pageSelect" />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
