<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin1.ts'
import { useCompany } from '@/store/pinia/company.ts'
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

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))

const listControl = ref<InstanceType<typeof ListController> | null>(null)

const dataFilter = ref<ComFilter>({
  page: 1,
  com: undefined,
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk ?? undefined)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(() => {
  const sp = new URLSearchParams({ company: String(company.value ?? '') })
  if (dataFilter.value.q) sp.set('search', dataFilter.value.q)
  return `/excel/executive-ranks/?${sp.toString()}`
})

const listFiltering = (payload: ComFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) comStore.fetchExecutiveRankList(dataFilter.value)
}

const multiSubmit = async (payload: ExecutiveRank, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updateExecutiveRank(payload, page, company.value, dataFilter.value)
      : await comStore.createExecutiveRank(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}

const onDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deleteExecutiveRank(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const pageSelect = (num: number) => {
  dataFilter.value.page = num
  if (company.value) {
    dataFilter.value.com = company.value
    comStore.fetchExecutiveRankList(dataFilter.value)
  }
}

const dataReset = () => {
  comStore.executiveRankList = []
  comStore.executiveRanksCount = 0
  comStore.allExecutiveRankList = []
  comStore.executiveRank = null
}

const loading = ref(true)
watch(
  company,
  async newVal => {
    dataReset()
    listControl.value?.clearFilter()
    dataFilter.value = { page: 1, com: newVal, q: '' }
    if (newVal) {
      loading.value = true
      await comStore.fetchExecutiveRankList({ com: newVal })
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
        <ListController ref="listControl" @list-filtering="listFiltering" />
        <AddExecutiveRank v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="임원 직위 목록"
          excel
          :url="excelUrl"
          filename="임원_직위_목록.xlsx"
          :disabled="!company"
        />
        <ExecutiveRankList
          :active-page="dataFilter.page || 1"
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
