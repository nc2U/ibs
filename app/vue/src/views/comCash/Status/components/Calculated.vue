<script lang="ts" setup>
import { ref } from 'vue'
import { write_project_cash } from '@/utils/pageAuth'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({
  calcDate: { type: String, default: null },
  isCalculated: { type: Boolean, default: false },
})
const emit = defineEmits(['to-calculate'])

const refConfirmModal = ref()

const toCalculated = () => refConfirmModal.value.callModal()

const modalAction = () => {
  emit('to-calculate')
  refConfirmModal.value.close()
}
</script>

<template>
  <CAlert
    v-if="write_project_cash"
    :color="isCalculated ? 'success' : 'warning'"
    class="text-right"
  >
    <span v-if="calcDate" class="mr-3">[정산일 : {{ calcDate }}]</span>
    <v-btn v-if="isCalculated" color="success" size="x-large" disabled> 잔고정산 확인완료</v-btn>
    <v-btn v-else color="warning" size="x-large" @click="toCalculated"> 당일잔고 정산확인</v-btn>
  </CAlert>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 알림</template>
    <template #default>
      계좌별 잔고 데이터가 실제 계좌 잔고와 일치 하는지 체크 후 확인을 클릭 하십시요. 확인 후 현재
      등록된 최종 거래 일자로부터 10일이 경과한 거래 건은 수정 및 삭제할 수 없습니다.
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">확인</v-btn>
    </template>
  </ConfirmModal>
</template>
