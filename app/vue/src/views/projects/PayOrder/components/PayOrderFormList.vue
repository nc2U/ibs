<script lang="ts" setup>
import { computed } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { usePayment } from '@/store/pinia/payment'
import { type PayOrder as po } from '@/store/types/payment'
import { TableSecondary } from '@/utils/cssMixins'
import PayOrder from '@/views/projects/PayOrder/components/PayOrder.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const paymentStore = usePayment()
const payOrderList = computed(() => paymentStore.payOrderList)

const onUpdatePayOrder = (payload: po) => emit('on-update', payload)
const onDeletePayOrder = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col style="width: 6%" />
      <col v-if="write_project" style="width: 6%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>종류</CTableHeaderCell>
        <CTableHeaderCell>납입회차 코드</CTableHeaderCell>
        <CTableHeaderCell>납부순서</CTableHeaderCell>
        <CTableHeaderCell>납부회차명</CTableHeaderCell>
        <CTableHeaderCell>회차 별칭</CTableHeaderCell>
        <CTableHeaderCell>PM용역비 여부</CTableHeaderCell>
        <CTableHeaderCell>약정금액</CTableHeaderCell>
        <CTableHeaderCell>납부비율(%)</CTableHeaderCell>
        <CTableHeaderCell>납부약정일</CTableHeaderCell>
        <CTableHeaderCell>전회기준 경과일수</CTableHeaderCell>
        <CTableHeaderCell>선납할인 적용</CTableHeaderCell>
        <CTableHeaderCell>선납할인율</CTableHeaderCell>
        <CTableHeaderCell>선납기준일</CTableHeaderCell>
        <CTableHeaderCell>연체가산 적용</CTableHeaderCell>
        <CTableHeaderCell>연체가산율</CTableHeaderCell>
        <CTableHeaderCell>연체기준일</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="payOrderList.length > 0">
      <PayOrder
        v-for="payOrder in payOrderList"
        :key="payOrder.pk as number"
        :pay-order="payOrder"
        @on-update="onUpdatePayOrder"
        @on-delete="onDeletePayOrder"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="write_project ? 17 : 16" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
