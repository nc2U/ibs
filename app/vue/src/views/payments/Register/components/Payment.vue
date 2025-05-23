<script lang="ts" setup>
import { ref, onMounted, type PropType } from 'vue'
import { type ProjectCashBook } from '@/store/types/proCash'
import { useRouter } from 'vue-router'
import { numFormat } from '@/utils/baseMixins'
import { write_payment } from '@/utils/pageAuth'
import { TableSecondary } from '@/utils/cssMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import PaymentForm from '@/views/payments/Register/components/PaymentForm.vue'
import { type AllPayment } from '@/store/types/payment'

const props = defineProps({
  payment: { type: Object as PropType<AllPayment>, default: null },
  paymentId: { type: String, default: '' },
  contract: { type: Object, default: null },
})
const emit = defineEmits(['on-update', 'on-delete'])

const updateFormModal = ref()

onMounted(() => {
  if (props.paymentId === props.payment.pk.toString()) {
    showDetail()
  }
})

const router = useRouter()
const showDetail = () => {
  router.replace({
    name: '건별 수납 관리',
    query: { contract: props.contract.pk },
  })
  updateFormModal.value.callModal()
}

const updateObject = (payload: ProjectCashBook) => {
  emit('on-update', { ...{ pk: props.payment.pk }, ...payload })
  updateFormModal.value.close()
}

const deleteObject = () => emit('on-delete', props.payment.pk)
</script>

<template>
  <CTableRow class="text-center" :color="payment.pk.toString() === paymentId ? TableSecondary : ''">
    <CTableDataCell>{{ payment.deal_date }}</CTableDataCell>
    <CTableDataCell>
      {{ payment.installment_order ? payment.installment_order.__str__ : '-' }}
    </CTableDataCell>
    <CTableDataCell class="text-right">
      <router-link to="" @click="showDetail">
        {{ numFormat(payment.income) }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell>{{ payment.bank_account.alias_name }}</CTableDataCell>
    <CTableDataCell>{{ payment.trader }}</CTableDataCell>
    <CTableDataCell v-if="write_payment">
      <v-btn type="button" color="info" size="x-small" @click="showDetail"> 보기</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>건별 수납 관리</template>
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
