<script lang="ts" setup>
import { ref, reactive, computed, inject, onBeforeMount } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { write_project } from '@/utils/pageAuth'
import { type OrderGroup } from '@/store/types/contract'
import { type UnitType } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const orders = inject<OrderGroup[]>('orders')
const types = inject<UnitType[]>('types')

const props = defineProps({ downPay: { type: Object, required: true } })

const emit = defineEmits(['on-update', 'on-delete'])

const form = reactive({
  order_group: null,
  unit_type: null,
  payment_amount: null,
})

const refAlertModal = ref()
const refConfirmModal = ref()

const formsCheck = computed(() => {
  const a = form.order_group === props.downPay.order_group
  const b = form.unit_type === props.downPay.unit_type
  const c = form.payment_amount === props.downPay.payment_amount
  return a && b && c
})

const formCheck = (bool: boolean) => {
  if (bool) onUpdateDownPay()
  return
}
const onUpdateDownPay = () => {
  if (write_project.value) {
    const pk = props.downPay.pk
    emit('on-update', { ...{ pk }, ...form })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}
const onDeleteDownPay = () => {
  if (useAccount().superAuth) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}
const modalAction = () => {
  emit('on-delete', props.downPay.pk)
  refConfirmModal.value.close()
}

const dataSetup = () => {
  form.order_group = props.downPay.order_group
  form.unit_type = props.downPay.unit_type
  form.payment_amount = props.downPay.payment_amount
}

onBeforeMount(() => dataSetup())
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model="form.order_group" required>
        <option value="">차수선택</option>
        <option v-for="order in orders" :key="order.pk" :value="order.pk">
          {{ order.order_group_name }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.unit_type" required>
        <option value="">타입선택</option>
        <option v-for="type in types" :key="type.pk" :value="type.pk">
          {{ type.name }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.payment_amount"
        placeholder="회차별 납부 계약금액"
        type="number"
        min="0"
        required
        @keypress.enter="formCheck(form.payment_amount !== downPay.payment_amount)"
      />
    </CTableDataCell>

    <CTableDataCell v-if="write_project" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateDownPay">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" @click="onDeleteDownPay">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 계약 조건 삭제</template>
    <template #default>
      해당 데이터를 삭제하면 이후 복구할 수 없습니다. 이 계약 조건 정보를 삭제 하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
