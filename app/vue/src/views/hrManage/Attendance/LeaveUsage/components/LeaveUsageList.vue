<script lang="ts" setup>
import { computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { type StaffLeaveUsage as StaffLeaveUsageType } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import LeaveUsage from './LeaveUsage.vue'

const emit = defineEmits(['page-select', 'multi-submit', 'on-delete'])

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const companyStore = useCompany()
const staffLeaveUsageList = computed(() => companyStore.staffLeaveUsageList)
const staffLeaveUsagesCount = computed(() => companyStore.staffLeaveUsagesCount)

const staffLeaveUsagePages = (page: number) => companyStore.staffLeaveUsagePages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: StaffLeaveUsageType) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 10%" />
      <col style="width: 12%" />
      <col style="width: 11%" />
      <col style="width: 11%" />
      <col style="width: 10%" />
      <col style="width: 24%" />
      <col style="width: 8%" />
      <col style="width: 9%" />
      <col v-if="canHrWorkManage" style="width: 5%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">성명</CTableHeaderCell>
        <CTableHeaderCell scope="col">휴가 구분</CTableHeaderCell>
        <CTableHeaderCell scope="col">시작일</CTableHeaderCell>
        <CTableHeaderCell scope="col">종료일</CTableHeaderCell>
        <CTableHeaderCell scope="col">차감 일수</CTableHeaderCell>
        <CTableHeaderCell scope="col">휴가 사유</CTableHeaderCell>
        <CTableHeaderCell scope="col">상태</CTableHeaderCell>
        <CTableHeaderCell scope="col">신청/등록일</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <LeaveUsage
        v-for="usage in staffLeaveUsageList"
        :key="usage.pk"
        :usage="usage"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
      <CTableRow v-if="staffLeaveUsageList.length === 0">
        <CTableDataCell :colspan="canHrWorkManage ? 9 : 8" class="text-center text-muted py-4">
          조회된 휴가 사용 내역이 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    v-if="staffLeaveUsagesCount > 10"
    :active-page="1"
    :limit="8"
    :pages="staffLeaveUsagePages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
