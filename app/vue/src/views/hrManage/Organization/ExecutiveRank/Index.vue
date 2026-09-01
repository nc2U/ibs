<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin1.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type ExecutiveRank, type ComFilter } from '@/store/types/company.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddExecutiveRank from './components/AddExecutiveRank.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ExecutiveRankList from './components/ExecutiveRankList.vue'

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_CREATE))

const dataFilter = ref<ComFilter>({
  page: 1,
  com: 1,
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(
  () => `/excel/executive-ranks/?company=${company.value}&search=${dataFilter.value.q}`,
)

const listFiltering = (payload: ComFilter) => {
  dataFilter.value = payload
  fetchExecutiveRankList({
    page: payload.page,
    com: payload.com,
    q: payload.q,
  })
}

const fetchExecutiveRankList = (payload: ComFilter) => comStore.fetchExecutiveRankList(payload)

const createExecutiveRank = (payload: ExecutiveRank, p?: number, c?: number) =>
  comStore.createExecutiveRank(payload, p, c)
const updateExecutiveRank = (payload: ExecutiveRank, p?: number, c?: number) =>
  comStore.updateExecutiveRank(payload, p, c)
const deleteExecutiveRank = (pk: number, com: number) => comStore.deleteExecutiveRank(pk, com)

const multiSubmit = (payload: ExecutiveRank) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (!!payload.pk) updateExecutiveRank(payload, page, company.value)
    else createExecutiveRank(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deleteExecutiveRank(pk, company.value)
}

const pageSelect = (num: number) => {
  dataFilter.value.page = num
  if (company.value) {
    dataFilter.value.com = company.value
    fetchExecutiveRankList(dataFilter.value)
  }
}

const comSelect = (target: number | null) => {
  comStore.executiveRankList = []
  if (!!target) fetchExecutiveRankList({ com: target })
}

const loading = ref(true)
onMounted(async () => {
  await fetchExecutiveRankList({ com: company.value || comStore.initComId })
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
        <ListController ref="listControl" @list-filtering="listFiltering" />
        <AddExecutiveRank
          v-if="canHrWorkCreate"
          :company="comName"
          @multi-submit="multiSubmit"
        />
        <TableTitleRow
          title="임원 직위 목록"
          excel
          :url="excelUrl"
          filename="임원_직위_목록.xlsx"
          :disabled="!company"
        />
        <ExecutiveRankList
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
