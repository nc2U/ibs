<script lang="ts" setup>
import { ref, reactive, inject, watch } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { isValidate } from '@/utils/helper'
import { type OrderGroup } from '@/store/types/contract'
import { type UnitType } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const orders = inject<OrderGroup[]>('orders')
const types = inject<UnitType[]>('types')

const props = defineProps({ disabled: Boolean })
const emit = defineEmits(['on-submit'])

const refAlertModal = ref()
const refConfirmModal = ref()

const form = reactive({
  order_group: '',
  unit_type: '',
  payment_amount: null,
})

const validated = ref(false)

watch(props, () => {
  form.order_group = ''
  form.unit_type = ''
})

const onSubmit = (event: Event) => {
  if (write_project.value) {
    isValidate(event) ? (validated.value = true) : refConfirmModal.value.callModal()
  } else {
    refAlertModal.value.callModal()
    resetForm()
  }
}
const modalAction = () => {
  emit('on-submit', form)
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
            {{ order.order_group_name }}
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
          text="공급가 대비 비율이 아닌 차수 및 타입별 고정 납부 계약금으로 관리할 경우 등록(납부 회수는 납부 회차 모델에서 별도 등록/설정)"
        />
      </CCol>

      <CCol md="2">
        <CRow>
          <CCol md="12" class="d-grid gap-2 d-lg-block mb-3">
            <v-btn color="primary" type="submit" :disabled="disabled"> 계약금액 추가</v-btn>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 타입별 계약금</template>
    <template #default> 프로젝트의 타입별 계약금 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
