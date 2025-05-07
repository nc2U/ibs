<script lang="ts" setup>
import { computed } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { usePayment } from '@/store/pinia/payment'
import { type DownPay as dp } from '@/store/types/payment'
import { TableSecondary } from '@/utils/cssMixins'
import DownPay from '@/views/projects/DownPay/components/DownPay.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const paymentStore = usePayment()
const downPayList = computed(() => paymentStore.downPayList)

const onUpdateDownPay = (payload: dp) => emit('on-update', payload)
const onDeleteDownPay = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 25%" />
      <col style="width: 25%" />
      <col style="width: 35%" />
      <col v-if="write_project" style="width: 15%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>차수</CTableHeaderCell>
        <CTableHeaderCell>타입</CTableHeaderCell>
        <CTableHeaderCell>회별 납부금액</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="downPayList.length > 0">
      <DownPay
        v-for="downPay in downPayList"
        :key="downPay.pk"
        :down-pay="downPay"
        @on-update="onUpdateDownPay"
        @on-delete="onDeleteDownPay"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="write_project ? 4 : 3" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
