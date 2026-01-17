<script lang="ts" setup>
import { inject, reactive, ref, watch } from 'vue'
import { write_project } from '@/utils/pageAuth'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ disabled: Boolean })
const emit = defineEmits(['on-submit'])

const accountList = inject<any>('accountList')

const refAlertModal = ref()
const refConfirmModal = ref()

const validated = ref(false)
const form = reactive({
  account: null,
  basis_calc: '',
  budget: null,
  revised_budget: null,
})

watch(props, newVal => {
  if (!!newVal.disabled) resetForm()
})

const onSubmit = (event: Event) => {
  if (write_project.value) {
    const e = event.currentTarget as HTMLFormElement
    if (!e.checkValidity()) {
      event.preventDefault()
      event.stopPropagation()

      validated.value = true
    } else refConfirmModal.value.callModal()
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
  form.account = null
  form.basis_calc = ''
  form.budget = null
  form.revised_budget = null
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow class="p-2" color="success">
      <CCol md="10" xl="11">
        <CRow>
          <CCol md="3" class="mb-2">
            <CFormSelect v-model="form.account" required :disabled="disabled">
              <option value="">계정 과목</option>
              <option v-for="acc in accountList" :key="acc.value" :value="acc.value">
                {{ acc.label }}
              </option>
            </CFormSelect>
          </CCol>
          <CCol md="3" class="mb-2">
            <CFormInput
              v-model="form.basis_calc"
              placeholder="산출근거"
              maxlength="18"
              :disabled="disabled"
            />
          </CCol>

          <CCol md="3" class="mb-2">
            <CFormInput
              v-model.number="form.budget"
              min="0"
              placeholder="기초(인준) 지출 예산"
              type="number"
              maxlength="18"
              required
              :disabled="disabled"
            />
          </CCol>

          <CCol md="3" class="mb-2">
            <CFormInput
              v-model.number="form.revised_budget"
              min="0"
              placeholder="현황(변경) 지출 예산"
              type="number"
              maxlength="18"
              :disabled="disabled"
            />
          </CCol>
        </CRow>
      </CCol>
      <CCol md="2" xl="1">
        <CRow>
          <CCol md="12" class="d-grid gap-2 d-lg-block text-right mb-3">
            <v-btn color="primary" type="submit" :disabled="disabled"> 지출 예산 추가</v-btn>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 수입 예산 등록</template>
    <template #default> 프로젝트의 수입 예산 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
