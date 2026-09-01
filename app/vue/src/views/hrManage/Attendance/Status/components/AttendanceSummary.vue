<script lang="ts" setup>
import { computed } from 'vue'
import { numFormat } from '@/utils/baseMixins.ts'
import { TableSecondary, TableSuccess, TablePrimary, TableInfo } from '@/utils/cssMixins.ts'
import { type Staff, type StaffLeaveQuota } from '@/store/types/company.ts'

const props = defineProps<{
  staffList: Staff[]
  quotaList: StaffLeaveQuota[]
  year: number
}>()

const totalStaffCount = computed(() => props.staffList.length)
const activeStaffCount = computed(() => props.staffList.filter(s => s.status === '1').length)
const onLeaveStaffCount = computed(() => props.staffList.filter(s => s.status === '2').length)

const totalGrantedDays = computed(() =>
  props.quotaList.reduce((acc, cur) => acc + Number(cur.total_granted_days || 0), 0),
)
const totalUsedDays = computed(() =>
  props.quotaList.reduce((acc, cur) => acc + Number(cur.used_days || 0), 0),
)
const totalRemainingDays = computed(() =>
  props.quotaList.reduce((acc, cur) => acc + Number(cur.remaining_days || 0), 0),
)
const overallUsageRate = computed(() => {
  if (totalGrantedDays.value > 0) {
    return ((totalUsedDays.value / totalGrantedDays.value) * 100).toFixed(1)
  }
  return '0.0'
})
</script>

<template>
  <CRow class="mb-4">
    <!-- 인원 현황 카드 -->
    <CCol lg="6" xl="6" class="mb-3">
      <CCard class="h-100 shadow-sm border-top-primary border-top-3">
        <CCardHeader class="bg-more-white py-2">
          <strong>
            <CIcon icon="cil-people" class="me-1 text-primary" />
            인력 현황 요약
          </strong>
        </CCardHeader>
        <CCardBody class="p-0">
          <CTable hover responsive bordered align="middle" class="mb-0 text-center">
            <colgroup>
              <col style="width: 25%" />
              <col style="width: 25%" />
              <col style="width: 25%" />
              <col style="width: 25%" />
            </colgroup>
            <CTableHead :color="TableSecondary">
              <CTableRow>
                <CTableHeaderCell>총 인원</CTableHeaderCell>
                <CTableHeaderCell>재직(근무)</CTableHeaderCell>
                <CTableHeaderCell>휴직</CTableHeaderCell>
                <CTableHeaderCell>기타/퇴사</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              <CTableRow class="fs-5 fw-bold">
                <CTableDataCell>{{ numFormat(totalStaffCount) }} 명</CTableDataCell>
                <CTableDataCell class="text-primary"
                  >{{ numFormat(activeStaffCount) }} 명</CTableDataCell
                >
                <CTableDataCell class="text-warning">
                  {{ numFormat(onLeaveStaffCount) }} 명
                </CTableDataCell>
                <CTableDataCell class="text-muted">
                  {{ numFormat(totalStaffCount - activeStaffCount - onLeaveStaffCount) }} 명
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </CCardBody>
      </CCard>
    </CCol>

    <!-- 연차 집계 요약 카드 -->
    <CCol lg="6" xl="6" class="mb-3">
      <CCard class="h-100 shadow-sm border-top-info border-top-3">
        <CCardHeader class="bg-more-white py-2 d-flex justify-content-between align-items-center">
          <strong>
            <CIcon icon="cil-chart-pie" class="me-1 text-info" />
            {{ year }}년도 연차 사용 현황 요약
          </strong>
          <CBadge color="info" shape="rounded-pill"> 전체 소진율: {{ overallUsageRate }}% </CBadge>
        </CCardHeader>
        <CCardBody class="p-0">
          <CTable hover responsive bordered align="middle" class="mb-0 text-center">
            <colgroup>
              <col style="width: 25%" />
              <col style="width: 25%" />
              <col style="width: 25%" />
              <col style="width: 25%" />
            </colgroup>
            <CTableHead :color="TableSecondary">
              <CTableRow>
                <CTableHeaderCell>총 부여일수</CTableHeaderCell>
                <CTableHeaderCell>총 사용일수</CTableHeaderCell>
                <CTableHeaderCell>총 잔여일수</CTableHeaderCell>
                <CTableHeaderCell>평균 소진율</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              <CTableRow class="fs-5 fw-bold">
                <CTableDataCell class="text-primary">
                  {{ totalGrantedDays.toFixed(2) }} 일
                </CTableDataCell>
                <CTableDataCell class="text-danger">
                  {{ totalUsedDays.toFixed(2) }} 일
                </CTableDataCell>
                <CTableDataCell class="text-success">
                  {{ totalRemainingDays.toFixed(2) }} 일
                </CTableDataCell>
                <CTableDataCell class="text-info">{{ overallUsageRate }} %</CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>
</template>
