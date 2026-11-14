<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { numFormat } from '@/utils/baseMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import type { Contract } from '@/store/types/contract.ts'
import type { OriginPayment } from '@/store/types/payment.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import PaymentForm from './PaymentForm.vue'

const props = withDefaults(
  defineProps<{
    payment?: OriginPayment | null
    paymentId?: string
    contract?: Contract | null
  }>(),
  {
    payment: null,
    paymentId: '',
    contract: null,
  },
)
const emit = defineEmits<{
  (e: 'on-update', bankTransactionId: number, payload: any): void
  (e: 'on-delete', bankTransactionId: number): void
}>()

const { can, PERM } = usePerms()
const canPaymentUpdate = computed(() => can(PERM.PAYMENT_UPDATE))

const updateFormModal = ref()

onMounted(() => {
  if (props.paymentId === props.payment?.pk.toString()) {
    showDetail()
  }
})

const router = useRouter()
const showDetail = () => {
  router.replace({
    name: '건별 납부 관리 - 상세',
    params: { contractId: props.contract?.pk },
  })
  updateFormModal.value.callModal()
}

const updateObject = (bankTransactionId: number, payload: any) => {
  emit('on-update', bankTransactionId, payload)
  updateFormModal.value.close()
}

const deleteObject = (bankTransactionId: number) => {
  emit('on-delete', bankTransactionId)
}
</script>

<template>
  <CTableRow
    v-if="payment"
    class="text-center"
    :color="payment.pk.toString() === paymentId ? TableSecondary : ''"
  >
    <CTableDataCell>{{ payment.deal_date }}</CTableDataCell>
    <CTableDataCell>
      {{ payment.installment_order ? payment.installment_order.str_display : '-' }}
    </CTableDataCell>
    <CTableDataCell class="text-end">
      <a
        v-if="canPaymentUpdate"
        href="#"
        class="text-decoration-none"
        @click.prevent="showDetail"
      >
        {{ numFormat(payment.amount || 0) }}
      </a>
      <span v-else>
        {{ numFormat(payment.amount || 0) }}
      </span>
    </CTableDataCell>
    <CTableDataCell>{{ payment.bank_account.alias_name }}</CTableDataCell>
    <CTableDataCell>{{ payment.trader }}</CTableDataCell>
    <CTableDataCell v-if="canPaymentUpdate">
      <v-btn type="button" color="info" variant="flat" size="x-small" @click="showDetail">
        보기
      </v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>건별 납부 관리</template>
    <template #default>
      <PaymentForm
        :contract="contract"
        :payment="payment"
        @on-submit="updateObject"
        @on-delete="deleteObject"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
