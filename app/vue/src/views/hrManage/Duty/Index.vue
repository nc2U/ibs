<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin2'
import { useCompany } from '@/store/pinia/company'
import { write_human_resource } from '@/utils/pageAuth'
import { type Duty, type ComFilter } from '@/store/types/company'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import HrAuthGuard from '@/components/AuthGuard/HrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddDuty from './components/AddDuty.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import DutyList from './components/DutyList.vue'

// 직책 = Duty
const listControl = ref()

const dataFilter = ref<ComFilter>({
  page: 1,
  com: 1,
  q: '',
})

const comStore = useCompany()
const company = computed(() => comStore.company?.pk)
const comName = computed(() => comStore.company?.name || undefined)

const excelUrl = computed(
  () => `/excel/duties/?company=${company.value}&search=${dataFilter.value.q}`,
)

const listFiltering = (payload: ComFilter) => {
  dataFilter.value = payload
  fetchDutyList({
    page: payload.page,
    com: payload.com,
    q: payload.q,
  })
}

const fetchDutyList = (payload: ComFilter) => comStore.fetchDutyList(payload)

const createDuty = (payload: Duty, p?: number, c?: number) => comStore.createDuty(payload, p, c)
const updateDuty = (payload: Duty, p?: number, c?: number) => comStore.updateDuty(payload, p, c)
const deleteDuty = (pk: number, com: number) => comStore.deleteDuty(pk, com)

const multiSubmit = (payload: Duty) => {
  const { page } = dataFilter.value
  if (company.value) {
    if (!!payload.pk) updateDuty(payload, page, company.value)
    else createDuty(payload, page, company.value)
  }
}
const onDelete = (pk: number) => {
  if (company.value) deleteDuty(pk, company.value)
}

const pageSelect = (num: number) => {
  dataFilter.value.page = num
  if (company.value) {
    dataFilter.value.com = company.value
    fetchDutyList(dataFilter.value)
  }
}

const comSelect = (target: number | null) => {
  comStore.dutyList = []
  if (!!target) fetchDutyList({ com: target })
}

const loading = ref(true)
onMounted(async () => {
  await fetchDutyList({ com: company.value || comStore.initComId })
  loading.value = false
})
</script>

<template>
  <HrAuthGuard>
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
        <AddDuty v-if="write_human_resource" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow title="직책 목록" excel :url="excelUrl" filename="직책_목록" :disabled="!company" />
        <DutyList @multi-submit="multiSubmit" @on-delete="onDelete" @page-select="pageSelect" />
      </CCardBody>
    </ContentBody>
  </HrAuthGuard>
</template>
