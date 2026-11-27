<script lang="ts" setup>
import { ref, reactive, inject, computed } from 'vue'
import { isValidate } from '@/utils/helper'
import { usePerms } from '@/composables/usePerms.ts'
import { usePayment } from '@/store/pinia/payment'
import { type OrderGroup } from '@/store/types/contract'
import { type UnitType } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const orders = inject<OrderGroup[]>('orders')
const types = inject<UnitType[]>('types')

defineProps({ disabled: Boolean })
const emit = defineEmits<{
  (
    e: 'on-submit',
    payload: { order_group: number; unit_type: number; payment_amount: number },
  ): void
}>()

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

const validated = ref(false)

// 이미 등록된 차수 + 타입 조합인지 확인
const isDuplicate = computed(() => {
  if (!form.order_group || !form.unit_type) return false
  return paymentStore.downPayList.some(
    dp => dp.order_group === Number(form.order_group) && dp.unit_type === Number(form.unit_type),
  )
})

const isFormValid = computed(
  () =>
    Boolean(form.order_group) &&
    Boolean(form.unit_type) &&
    form.payment_amount !== null &&
    form.payment_amount !== '' &&
    Number(form.payment_amount) >= 0 &&
    !isDuplicate.value,
)

const onSubmit = (event: Event) => {
  if (canProjectUpdate.value) {
    if (isDuplicate.value) {
      refAlertModal.value.callModal('중복 등록 오류', '이미 등록된 차수와 타입의 조합입니다.')
      return
    }
    if (isValidate(event)) {
      validated.value = true
    } else {
      refConfirmModal.value.callModal()
    }
  } else {
    refAlertModal.value.callModal()
    resetForm()
  }
}

const modalAction = () => {
  if (isDuplicate.value) {
    refConfirmModal.value.close()
    refAlertModal.value.callModal('중복 등록 오류', '이미 등록된 차수와 타입의 조합입니다.')
    return
  }
  emit('on-submit', {
    order_group: Number(form.order_group),
    unit_type: Number(form.unit_type),
    payment_amount: Number(form.payment_amount),
  })
  validated.value = false
  refConfirmModal.value.close()
  resetForm()
}

const resetForm = () => {
  form.order_group = ''
  form.unit_type = ''
  form.payment_amount = null
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow class="p-2">
      <CCol md="3" class="mb-2">
        <CFormSelect v-model="form.order_group" :disabled="disabled" required>
          <option value="">차수선택</option>
          <option v-for="order in orders" :key="order.pk as number" :value="order.pk as number">
            {{ order.name }}
          </option>
        </CFormSelect>
      </CCol>

      <CCol md="3" class="mb-2">
        <CFormSelect v-model="form.unit_type" :disabled="disabled" required>
          <option value="">타입선택</option>
          <option v-for="type in types" :key="type.pk" :value="type.pk">
            {{ type.name }}
          </option>
        </CFormSelect>
      </CCol>

      <CCol md="4" class="mb-2">
        <CFormInput
          v-model.number="form.payment_amount"
          placeholder="회차별 납부 계약금액"
          type="number"
          min="0"
          required
          :disabled="disabled"
          :feedback-invalid="isDuplicate ? '이미 등록된 차수/타입 조합입니다.' : undefined"
          :invalid="isDuplicate"
          text="동호 미지정 계약 등 차수 및 타입별 각 계약금 회차 고정 납부 계약금. 미지정 시 공급가격 * 회차별 납부비율 적용"
        />
        <div v-if="isDuplicate" class="text-danger small mt-1">
          ※ 이미 등록된 차수와 타입의 조합입니다.
        </div>
      </CCol>

      <CCol md="2">
        <CRow>
          <CCol md="12" class="d-grid gap-2 d-lg-block mb-3">
            <v-btn color="primary" type="submit" :disabled="disabled || !isFormValid">
              계약금액 추가
            </v-btn>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 타입별 계약금</template>
    <template #default> 프로젝트의 타입별 계약금 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
