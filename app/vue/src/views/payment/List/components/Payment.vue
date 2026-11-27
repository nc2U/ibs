<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { numFormat } from '@/utils/baseMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { ContractPaymentPatchPayload, PaymentList } from '@/store/types/payment.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import ContChoicer from './ContChoicer.vue'

type PayMatchPayload = ContractPaymentPatchPayload & { trans_id: number | null }

const props = defineProps<{
  project: number
  payment: PaymentList
}>()

const emit = defineEmits<{
  (e: 'pay-match', payload: PayMatchPayload): void
}>()

const router = useRouter()
const { can, PERM } = usePerms()
const canPaymentMatch = computed(() => can(PERM.PAYMENT_CREATE) || can(PERM.PAYMENT_UPDATE))
const contMatchingModal = ref()

const rowClass = computed(() => {
  let cls = ''
  cls = props.payment?.contract && props.payment.installment_order === '-' ? 'danger' : cls
  cls = !props.payment?.contract ? 'warning' : cls
  return cls
})

const canManageRow = computed(() => Boolean(props.payment?.contract) || canPaymentMatch.value)

const toManage = () => (props.payment?.contract ? toRegister() : contMatching())

const toRegister = () => {
  router.push({
    name: '건별 납부 관리 - 상세',
    params: { contractId: props.payment?.contract?.pk },
    query: { payment: props.payment?.pk },
  })
}
const contMatching = () => {
  if (!props.payment?.contract && canPaymentMatch.value) contMatchingModal.value.callModal()
}

const payMatch = (payload: PayMatchPayload) => emit('pay-match', payload)
</script>

<template>
  <CTableRow v-if="payment" class="text-center" :color="rowClass || undefined">
    <CTableDataCell>{{ payment.deal_date }}</CTableDataCell>
    <CTableDataCell>{{ payment.order_group }}</CTableDataCell>
    <CTableDataCell class="text-start">
      <CIcon
        v-if="payment.contract"
        name="cib-node-js"
        :style="{ color: payment.type_color }"
        size="sm"
        class="me-1"
      />
      {{ payment.type_name }}
    </CTableDataCell>
    <CTableDataCell>{{ payment.serial_number }}</CTableDataCell>
    <CTableDataCell>
      <a v-if="canManageRow" href="#" class="text-decoration-none" @click.prevent="toManage">
        {{ payment.contract ? payment.contractor : '계약정보 확인' }}
      </a>
      <span v-else>{{ payment.contract ? payment.contractor : '계약정보 확인' }}</span>
      <v-tooltip activator="parent" location="top">
        {{ payment.trader }} / {{ payment.note }}
      </v-tooltip>
    </CTableDataCell>
    <CTableDataCell class="text-end">
      <a v-if="canManageRow" href="#" class="text-decoration-none" @click.prevent="toManage">
        {{ numFormat(payment.amount) }}
      </a>
      <span v-else>{{ numFormat(payment.amount) }}</span>
    </CTableDataCell>
    <CTableDataCell :class="payment.installment_order === '-' ? 'text-danger' : ''">
      {{ payment.installment_order === '-' ? '납입회차 확인' : payment.installment_order }}
    </CTableDataCell>
    <CTableDataCell>{{ payment.bank_account }}</CTableDataCell>
    <CTableDataCell>{{ payment.trader }}</CTableDataCell>
    <CTableDataCell>
      <v-btn
        type="button"
        color="info"
        variant="flat"
        size="x-small"
        :disabled="!canManageRow"
        @click="toManage"
      >
        확인
      </v-btn>
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
