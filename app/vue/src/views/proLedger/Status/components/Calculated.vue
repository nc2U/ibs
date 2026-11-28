<script lang="ts" setup>
import { ref, computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

interface Props {
  project?: number | null
  calcDate?: string | null
  isCalculated?: boolean
  hasTransactions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  project: undefined,
  calcDate: null,
  isCalculated: false,
  hasTransactions: false,
})
const emit = defineEmits<{
  (e: 'to-calculate'): void
}>()

const { can, canGlobal, PERM } = usePerms()
const canLedgerManage = computed(
  () =>
    (props.project ? can(PERM.LEDGER_MANAGE, props.project) : can(PERM.LEDGER_MANAGE)) ||
    canGlobal(PERM.LEDGER_MANAGE),
)

const refConfirmModal = ref()

const toCalculated = () => refConfirmModal.value?.callModal()

const modalAction = () => {
  emit('to-calculate')
  refConfirmModal.value?.close()
}
</script>

<template>
  <CAlert v-if="canLedgerManage" :color="isCalculated ? 'success' : 'warning'" class="text-end">
    <span v-if="calcDate" class="me-3">[정산일 : {{ calcDate }}]</span>
    <v-btn v-if="isCalculated" color="success" size="x-large" disabled> 잔고정산 확인완료</v-btn>
    <v-btn
      v-else
      color="warning"
      size="x-large"
      :disabled="!hasTransactions"
      @click="toCalculated"
    >
      당일잔고 정산확인
    </v-btn>
  </CAlert>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 알림</template>
    <template #default>
      계좌별 잔고 데이터가 실제 계좌 잔고와 일치하는지 확인 후 진행해 주세요. 정산 확인 후 정산
      마감일 이전 거래 건은 관리자(원장 관리 권한 보유자) 외 수정 및 삭제할 수 없습니다.
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="modalAction">확인</v-btn>
    </template>
  </ConfirmModal>
</template>
