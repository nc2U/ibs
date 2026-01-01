<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useRouter } from 'vue-router'
import { numFormat } from '@/utils/baseMixins'
import { write_payment } from '@/utils/pageAuth'
import type { PaymentList } from '@/store/types/payment.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import ContChoicer from './ContChoicer.vue'

const props = defineProps({
  project: { type: Number, required: true },
  payment: { type: Object as PropType<PaymentList>, required: true },
})

const emit = defineEmits(['pay-match'])

const router = useRouter()
const contMatchingModal = ref()

const rowClass = computed(() => {
  let cls = ''
  cls = props.payment?.contract && props.payment.installment_order === '-' ? 'danger' : cls
  cls = !props.payment?.contract ? 'warning' : cls
  return cls
})

const toManage = () => (props.payment?.contract ? toRegister() : contMatching())

const toRegister = () => {
  router.push({
    name: '건별 납부 관리 - 상세',
    params: { contractId: props.payment?.contract.pk },
    query: { payment: props.payment?.pk },
  })
}
const contMatching = () => {
  if (!props.payment?.contract) contMatchingModal.value.callModal()
  return
}

const payMatch = (payload: any) => emit('pay-match', payload)
</script>

<template>
  <CTableRow v-if="payment" class="text-center" :color="rowClass">
    <CTableDataCell>{{ payment.deal_date }}</CTableDataCell>
    <CTableDataCell>{{ payment.order_group }}</CTableDataCell>
    <CTableDataCell class="text-left">
      <CIcon
        v-if="payment.contract"
        name="cib-node-js"
        :style="{ color: payment.type_color }"
        size="sm"
        class="mr-1"
      />
      {{ payment.type_name }}
    </CTableDataCell>
    <CTableDataCell>{{ payment.serial_number }}</CTableDataCell>
    <CTableDataCell>
      <router-link to="" @click="toManage">
        {{ payment.contract ? payment.contractor : '계약정보 확인' }}
      </router-link>
      <v-tooltip activator="parent" location="top">
        {{ payment.trader }} / {{ payment.note }}
      </v-tooltip>
    </CTableDataCell>
    <CTableDataCell class="text-right">
      <router-link to="" @click="toManage">
        {{ numFormat(payment.amount) }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell :class="payment.installment_order === '-' ? 'text-danger' : ''">
      {{ payment.installment_order === '-' ? '납입회차 확인' : payment.installment_order }}
    </CTableDataCell>
    <CTableDataCell>{{ payment.bank_account }}</CTableDataCell>
    <CTableDataCell>{{ payment.trader }}</CTableDataCell>
    <CTableDataCell v-if="write_payment">
      <v-btn type="button" color="info" size="x-small" @click="toManage"> 확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="contMatchingModal" size="lg">
    <template #header> 납부 건별 계약 건 매칭</template>
    <template #default>
      <ContChoicer
        :project="project"
        :payment="payment"
        class="p-5"
        @pay-match="payMatch"
        @close="contMatchingModal.close()"
      />
    </template>
  </FormModal>
</template>
