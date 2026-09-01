<script lang="ts" setup>
import { computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { type StaffLeaveQuota as StaffLeaveQuotaType } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import LeaveQuota from './LeaveQuota.vue'

const emit = defineEmits(['page-select', 'multi-submit', 'on-delete'])

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const companyStore = useCompany()
const staffLeaveQuotaList = computed(() => companyStore.staffLeaveQuotaList)
const staffLeaveQuotasCount = computed(() => companyStore.staffLeaveQuotasCount)

const staffLeaveQuotaPages = (page: number) => companyStore.staffLeaveQuotaPages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: StaffLeaveQuotaType) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 10%" />
      <col style="width: 8%" />
      <col style="width: 8%" />
      <col style="width: 8%" />
      <col style="width: 9%" />
      <col style="width: 8%" />
      <col style="width: 9%" />
      <col style="width: 15%" />
      <col style="width: 10%" />
      <col v-if="canHrWorkManage" style="width: 7%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">연도</CTableHeaderCell>
        <CTableHeaderCell scope="col">성명</CTableHeaderCell>
        <CTableHeaderCell scope="col">기본발생</CTableHeaderCell>
        <CTableHeaderCell scope="col">이월/조정</CTableHeaderCell>
        <CTableHeaderCell scope="col">포상/가산</CTableHeaderCell>
        <CTableHeaderCell scope="col">총 부여</CTableHeaderCell>
        <CTableHeaderCell scope="col">사용</CTableHeaderCell>
        <CTableHeaderCell scope="col">잔여</CTableHeaderCell>
        <CTableHeaderCell scope="col">사용 가능 기간</CTableHeaderCell>
        <CTableHeaderCell scope="col">비고</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <LeaveQuota
        v-for="quota in staffLeaveQuotaList"
        :key="quota.pk"
        :quota="quota"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
      <CTableRow v-if="staffLeaveQuotaList.length === 0">
        <CTableDataCell :colspan="canHrWorkManage ? 11 : 10" class="text-center text-muted py-4">
          해당 연도의 연차 부여 정보가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    v-if="staffLeaveQuotasCount > 10"
    :active-page="1"
    :limit="8"
    :pages="staffLeaveQuotaPages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
