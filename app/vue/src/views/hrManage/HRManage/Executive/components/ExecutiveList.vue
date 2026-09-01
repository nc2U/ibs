<script lang="ts" setup>
import { computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { type Executive as ExecutiveType } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import Executive from './Executive.vue'

const emit = defineEmits(['page-select', 'multi-submit', 'on-delete'])

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const companyStore = useCompany()
const executiveList = computed(() => companyStore.executiveList)
const executivesCount = computed(() => companyStore.executivesCount)

const executivePages = (page: number) => companyStore.executivePages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: ExecutiveType) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 11%" />
      <col style="width: 8%" />
      <col style="width: 8%" />
      <col style="width: 10%" />
      <col style="width: 11%" />
      <col style="width: 11%" />
      <col style="width: 13%" />
      <col v-if="canHrWorkManage" style="width: 8%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">성명</CTableHeaderCell>
        <CTableHeaderCell scope="col">직위</CTableHeaderCell>
        <CTableHeaderCell scope="col">상법상 지위</CTableHeaderCell>
        <CTableHeaderCell scope="col">등기</CTableHeaderCell>
        <CTableHeaderCell scope="col">상근</CTableHeaderCell>
        <CTableHeaderCell scope="col">대표권</CTableHeaderCell>
        <CTableHeaderCell scope="col">취임일</CTableHeaderCell>
        <CTableHeaderCell scope="col">임기만료일</CTableHeaderCell>
        <CTableHeaderCell scope="col">비고</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Executive
        v-for="executive in executiveList"
        :key="executive.pk"
        :executive="executive"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
    </CTableBody>
  </CTable>

  <Pagination
    v-if="executivesCount > 10"
    :active-page="1"
    :limit="8"
    :pages="executivePages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
