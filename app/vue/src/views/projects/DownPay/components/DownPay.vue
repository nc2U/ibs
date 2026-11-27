<script lang="ts" setup>
import { ref, reactive, computed, inject, watch, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePayment } from '@/store/pinia/payment'
import { usePerms } from '@/composables/usePerms.ts'
import { type OrderGroup } from '@/store/types/contract'
import { type UnitType } from '@/store/types/project'
import { type DownPay } from '@/store/types/payment'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  downPay: { type: Object as PropType<DownPay>, required: true },
})

const emit = defineEmits<{
  (e: 'on-update', payload: DownPay): void
  (e: 'on-delete', pk: number): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const isSuperAuth = computed(() => useAccount().superAuth)

const orders = inject<OrderGroup[]>('orders')
const types = inject<UnitType[]>('types')

const paymentStore = usePayment()

const refAlertModal = ref()
const refConfirmModal = ref()

const form = reactive<{
  order_group: number | ''
  unit_type: number | ''
  payment_amount: number | '' | null
}>({
  order_group: '',
  unit_type: '',
  payment_amount: null,
})

// 다른 항목과 차수+타입 중복 검사
const isDuplicate = computed(() => {
  if (!form.order_group || !form.unit_type) return false
  return paymentStore.downPayList.some(
    dp =>
      dp.pk !== props.downPay.pk &&
      dp.order_group === Number(form.order_group) &&
      dp.unit_type === Number(form.unit_type),
  )
})

// 기존 데이터에서 변경된 내용이 없는지 검사
const isUnchanged = computed(
  () =>
    Number(form.order_group) === props.downPay.order_group &&
    Number(form.unit_type) === props.downPay.unit_type &&
    (form.payment_amount !== null && form.payment_amount !== ''
      ? Number(form.payment_amount)
      : null) === props.downPay.payment_amount,
)

// 수정 버튼 비활성화 여부
const formsCheck = computed(
  () =>
    !form.order_group ||
    !form.unit_type ||
    form.payment_amount === null ||
    form.payment_amount === '' ||
    Number(form.payment_amount) < 0 ||
    isDuplicate.value ||
    isUnchanged.value,
)

const onUpdateDownPay = () => {
  if (formsCheck.value) return

  if (canProjectUpdate.value) {
    emit('on-update', {
      pk: props.downPay.pk,
      project: props.downPay.project,
      order_group: Number(form.order_group),
      unit_type: Number(form.unit_type),
      payment_amount: Number(form.payment_amount),
    })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const onDeleteDownPay = () => {
  if (isSuperAuth.value) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const modalAction = () => {
  if (props.downPay.pk) {
    emit('on-delete', props.downPay.pk)
  }
  refConfirmModal.value.close()
}

const dataSetup = () => {
  form.order_group = props.downPay.order_group
  form.unit_type = props.downPay.unit_type
  form.payment_amount = props.downPay.payment_amount
}

watch(
  () => props.downPay,
  () => dataSetup(),
  { deep: true, immediate: true },
)
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model="form.order_group" :disabled="!canProjectUpdate" required>
        <option value="">차수선택</option>
        <option v-for="order in orders" :key="order.pk as number" :value="order.pk as number">
          {{ order.name }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.unit_type" :disabled="!canProjectUpdate" required>
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
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdateDownPay"
      />
    </CTableDataCell>

    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateDownPay">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" class="ms-1" @click="onDeleteDownPay">삭제</v-btn>
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
