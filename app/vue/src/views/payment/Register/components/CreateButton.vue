<script lang="ts" setup>
import { ref, computed } from 'vue'
import type { Contract } from '@/store/types/contract.ts'
import type { ContractPaymentPayload } from '@/store/types/payment.ts'
import { AlertLight } from '@/utils/cssMixins.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import PaymentForm from './PaymentForm.vue'

const props = withDefaults(defineProps<{ contract?: Contract | null }>(), { contract: null })
const emit = defineEmits<{
  (e: 'on-create', payload: ContractPaymentPayload, done?: (ok: boolean) => void): void
}>()

const createFormModal = ref()

const btnActive = computed(() => !props.contract)

const showDetail = () => createFormModal.value.callModal()

const createObject = (payload: ContractPaymentPayload, done?: (ok: boolean) => void) => {
  emit('on-create', payload, (ok: boolean) => {
    done?.(ok)
    if (ok) createFormModal.value?.close()
  })
}
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-end">
    <v-btn type="button" color="primary" variant="flat" :disabled="btnActive" @click="showDetail">
      신규납부 등록
    </v-btn>
  </CAlert>

  <FormModal ref="createFormModal" size="lg">
    <template #header>건별 납부 관리 [신규 납부등록]</template>
    <template #default>
      <PaymentForm
        :contract="contract"
        @on-submit="createObject"
        @close="createFormModal.close()"
      />
    </template>
  </FormModal>
</template>
