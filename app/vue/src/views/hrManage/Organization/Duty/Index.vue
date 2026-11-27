<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/hrManage/_menu/headermixin1.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Duty, type ComFilter } from '@/store/types/company.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComHrAuthGuard from '@/components/AuthGuard/ComHrAuthGuard.vue'
import ListController from './components/ListController.vue'
import AddDuty from './components/AddDuty.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import DutyList from './components/DutyList.vue'

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
  return `/excel/duties/?${sp.toString()}`
})

const listFiltering = (payload: ComFilter) => {
  dataFilter.value = { ...payload, com: company.value }
  if (company.value) comStore.fetchDutyList(dataFilter.value)
}

const multiSubmit = async (payload: Duty, done?: (ok: boolean) => void) => {
  const { page } = dataFilter.value
  const ok = company.value
    ? payload.pk
      ? await comStore.updateDuty(payload, page, company.value, dataFilter.value)
      : await comStore.createDuty(payload, page, company.value, dataFilter.value)
    : false
  done?.(ok)
}

const onDelete = async (pk: number, done?: (ok: boolean) => void) => {
  const ok = company.value
    ? await comStore.deleteDuty(pk, company.value, dataFilter.value)
    : false
  if (ok) dataFilter.value.page = 1
  done?.(ok)
}

const pageSelect = (num: number) => {
  dataFilter.value.page = num
  if (company.value) {
    dataFilter.value.com = company.value
    comStore.fetchDutyList(dataFilter.value)
  }
}

const dataReset = () => {
  comStore.dutyList = []
  comStore.dutysCount = 0
  comStore.allDutyList = []
  comStore.duty = null
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
      await comStore.fetchDutyList({ com: newVal })
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
        <AddDuty v-if="canHrWorkCreate" :company="comName" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="직책 목록"
          excel
          :url="excelUrl"
          filename="직책_목록.xlsx"
          :disabled="!company"
        />
        <DutyList
          :active-page="dataFilter.page || 1"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
          @page-select="pageSelect"
        />
      </CCardBody>
    </ContentBody>
  </ComHrAuthGuard>
</template>
