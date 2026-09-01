<script lang="ts" setup>
import { computed } from 'vue'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { type Staff, type StaffLeaveQuota } from '@/store/types/company.ts'

const props = defineProps<{
  staffList: Staff[]
  quotaList: StaffLeaveQuota[]
  year: number
}>()

const quotaMap = computed(() => {
  const map = new Map<number, StaffLeaveQuota>()
  props.quotaList.forEach(q => {
    map.set(q.staff, q)
  })
  return map
})

const getStatusBadge = (status: string) => {
  switch (status) {
    case '1':
      return { color: 'success', label: '근무 중' }
    case '2':
      return { color: 'warning', label: '휴직 중' }
    case '3':
      return { color: 'info', label: '퇴직신청' }
    case '4':
      return { color: 'secondary', label: '퇴사' }
    default:
      return { color: 'light', label: '-' }
  }
}
</script>

<template>
  <CTable hover responsive bordered align="middle" class="text-center">
    <colgroup>
      <col style="width: 5%" />
      <col style="width: 12%" />
      <col style="width: 11%" />
      <col style="width: 11%" />
      <col style="width: 11%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 12%" />
      <col style="width: 8%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow align="middle">
        <CTableHeaderCell scope="col">No</CTableHeaderCell>
        <CTableHeaderCell scope="col">부서</CTableHeaderCell>
        <CTableHeaderCell scope="col">직급/직위</CTableHeaderCell>
        <CTableHeaderCell scope="col">성명</CTableHeaderCell>
        <CTableHeaderCell scope="col">입사일자</CTableHeaderCell>
        <CTableHeaderCell scope="col">총 부여일수</CTableHeaderCell>
        <CTableHeaderCell scope="col">사용일수</CTableHeaderCell>
        <CTableHeaderCell scope="col">잔여일수</CTableHeaderCell>
        <CTableHeaderCell scope="col">연차 사용률</CTableHeaderCell>
        <CTableHeaderCell scope="col">상태</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="(staff, index) in staffList" :key="staff.pk">
        <CTableDataCell>{{ index + 1 }}</CTableDataCell>
        <CTableDataCell>{{ staff.department || '-' }}</CTableDataCell>
        <CTableDataCell>{{ staff.position || staff.grade || '-' }}</CTableDataCell>
        <CTableDataCell class="fw-bold">{{ staff.name }}</CTableDataCell>
        <CTableDataCell class="small text-muted">{{ staff.date_join || '-' }}</CTableDataCell>
        <CTableDataCell class="text-right">
          {{ Number(quotaMap.get(staff.pk as number)?.total_granted_days || 0).toFixed(2) }}
        </CTableDataCell>
        <CTableDataCell class="text-right text-danger">
          {{ Number(quotaMap.get(staff.pk as number)?.used_days || 0).toFixed(2) }}
        </CTableDataCell>
        <CTableDataCell class="text-right fw-bold text-success">
          {{ Number(quotaMap.get(staff.pk as number)?.remaining_days || 0).toFixed(2) }}
        </CTableDataCell>
        <CTableDataCell class="text-right">
          <div class="d-flex align-items-center justify-content-end">
            <span class="small me-2">
              {{
                Number(quotaMap.get(staff.pk as number)?.total_granted_days || 0) > 0
                  ? (
                      (Number(quotaMap.get(staff.pk as number)?.used_days || 0) /
                        Number(quotaMap.get(staff.pk as number)?.total_granted_days || 0)) *
                      100
                    ).toFixed(1)
                  : '0.0'
              }}%
            </span>
            <CProgress
              thin
              :color="
                Number(quotaMap.get(staff.pk as number)?.total_granted_days || 0) > 0 &&
                (Number(quotaMap.get(staff.pk as number)?.used_days || 0) /
                  Number(quotaMap.get(staff.pk as number)?.total_granted_days || 0)) *
                  100 >=
                  80
                  ? 'danger'
                  : 'info'
              "
              :value="
                Number(quotaMap.get(staff.pk as number)?.total_granted_days || 0) > 0
                  ? (Number(quotaMap.get(staff.pk as number)?.used_days || 0) /
                      Number(quotaMap.get(staff.pk as number)?.total_granted_days || 0)) *
                    100
                  : 0
              "
              style="width: 50px"
            />
          </div>
        </CTableDataCell>
        <CTableDataCell>
          <CBadge :color="getStatusBadge(staff.status).color" shape="rounded-pill">
            {{ getStatusBadge(staff.status).label }}
          </CBadge>
        </CTableDataCell>
      </CTableRow>

      <CTableRow v-if="staffList.length === 0">
        <CTableDataCell colspan="10" class="text-center text-muted py-4">
          조회된 직원 근태/연차 현황 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
