<script lang="ts" setup>
import { computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { type Staff as StaffType } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import Staff from './Staff.vue'

const emit = defineEmits(['page-select', 'multi-submit', 'on-delete'])

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const companyStore = useCompany()
const staffList = computed(() => companyStore.staffList)
const staffsCount = computed(() => companyStore.staffsCount)

const staffPages = (page: number) => companyStore.staffPages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: StaffType) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 11%" />
      <col style="width: 10%" />
      <col style="width: 11%" />
      <col style="width: 11%" />
      <col style="width: 18%" />
      <col style="width: 13%" />
      <col style="width: 10%" />
      <col v-if="canHrWorkManage" style="width: 8%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">구분</CTableHeaderCell>
        <CTableHeaderCell scope="col">부서</CTableHeaderCell>
        <CTableHeaderCell scope="col">직위</CTableHeaderCell>
        <CTableHeaderCell scope="col">직책</CTableHeaderCell>
        <CTableHeaderCell scope="col">성명</CTableHeaderCell>
        <CTableHeaderCell scope="col">이메일</CTableHeaderCell>
        <CTableHeaderCell scope="col">입사일</CTableHeaderCell>
        <CTableHeaderCell scope="col">상태</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Staff
        v-for="staff in staffList"
        :key="staff.pk"
        :staff="staff"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
    </CTableBody>
  </CTable>

  <Pagination
    v-if="staffsCount > 10"
    :active-page="1"
    :limit="8"
    :pages="staffPages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
