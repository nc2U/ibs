<script lang="ts" setup>
import { computed } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Department as Depart } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import Department from './Department.vue'

const emit = defineEmits(['page-select', 'multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_UPDATE))
const canHrWorkManager = computed(() => canHrWorkCreate.value || canHrWorkUpdate.value)

const companyStore = useCompany()
const getPkDeparts = computed(() => companyStore.getPkDeparts)
const departmentList = computed(() => companyStore.departmentList)
const departmentsCount = computed(() => companyStore.departmentsCount)

const departmentPages = (page: number) => companyStore.departmentPages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: Depart) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 46%" />
      <col v-if="canHrWorkManager" style="width: 8%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">No</CTableHeaderCell>
        <CTableHeaderCell scope="col">상위부서</CTableHeaderCell>
        <CTableHeaderCell scope="col">부서명</CTableHeaderCell>
        <CTableHeaderCell scope="col">책임자</CTableHeaderCell>
        <CTableHeaderCell scope="col">주요업무</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManager" scope="col">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Department
        v-for="depart in departmentList"
        :key="depart.pk"
        :department="depart"
        :get-departs="getPkDeparts"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
    </CTableBody>
  </CTable>

  <Pagination
    v-if="departmentsCount > 10"
    :active-page="1"
    :limit="8"
    :pages="departmentPages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
