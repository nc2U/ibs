<script lang="ts" setup>
import { ref, watch } from 'vue'
import { downloadFile } from '@/utils/helper.ts'
import { AlertSecondary } from '@/utils/cssMixins'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  printData: { type: Object, default: null },
  contracts: { type: Array, default: () => [] },
})

const refAlertModal = ref()

const noPrice = ref(localStorage.getItem('noPrice') === 'true')

watch(noPrice, newVal => {
  localStorage.setItem('noPrice', String(newVal))
})

const noLate = ref(localStorage.getItem('noLate') === 'true')

watch(noLate, newVal => {
  localStorage.setItem('noLate', String(newVal))
})

const printBill = () => {
  const { is_bill_issue } = props.printData
  if (!is_bill_issue) {
    refAlertModal.value.callModal('', '고지서 관련 기본 설정 데이터를 입력하여 주십시요.')
  } else {
    if (props.contracts?.length === 0) {
      refAlertModal.value.callModal('', '다운로드(출력)할 계약 건을 선택하여 주십시요.')
    } else {
      const { project, pub_date } = props.printData
      const seq = props.contracts?.join('-')
      const url = '/pdf/bill/'
      const np = noPrice.value ? '1' : ''
      const nl = noLate.value ? '1' : ''
      const lastUrl = `${url}?project=${project}&date=${pub_date}&seq=${seq}&np=${np}&nl=${nl}`
      downloadFile(lastUrl, `대금납부_고지서(${props.contracts.length}건).pdf`)
    }
  }
}
</script>

<template>
  <CAlert :color="AlertSecondary" class="pb-2">
    <CRow class="p-0 m-0">
      <CCol sm="6">
        <v-btn color="primary" :disabled="!contracts.length" @click="printBill">
          선택 건별 고지서 내려받기
        </v-btn>
      </CCol>
      <CCol sm="6" class="text-right">
        <v-checkbox-btn v-model="noPrice" color="success" label="가격정보 미표시" inline />
        <v-checkbox-btn v-model="noLate" color="success" label="연체정보 미표시" inline />
      </CCol>
    </CRow>
  </CAlert>

  <AlertModal ref="refAlertModal" />
</template>
