<script lang="ts" setup>
import { ref, reactive, inject, watch } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { type ProjectAccountD2, type ProjectAccountD3 } from '@/store/types/proCash'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const d2List = inject<ProjectAccountD2[]>('d2List')
const d3List = inject<ProjectAccountD3[]>('d3List')

const props = defineProps({ disabled: Boolean })
const emit = defineEmits(['on-submit'])

const refAlertModal = ref()
const refConfirmModal = ref()

const validated = ref(false)
const form = reactive({
  account_d2: null,
  account_opt: '',
  account_d3: null,
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
  form.account_d2 = null
  form.account_opt = ''
  form.account_d3 = null
  form.basis_calc = ''
  form.budget = null
  form.revised_budget = null
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow class="p-2" color="success">
      <CCol md="12" lg="5">
        <CRow>
          <CCol md="4" class="mb-2">
            <CFormSelect v-model="form.account_d2" required :disabled="disabled">
              <option value="">대분류</option>
              <option v-for="d1 in d2List" :key="d1.pk" :value="d1.pk">
                {{ d1.name }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="4" class="mb-2">
            <CFormInput
              v-model="form.account_opt"
              placeholder="중분류(필요시 기재)"
              maxlength="20"
              :disabled="disabled"
            />
          </CCol>

          <CCol md="4" class="mb-2">
            <CFormSelect v-model="form.account_d3" :disabled="disabled">
              <option value="">소분류</option>
              <option v-for="d2 in d3List" :key="d2.pk" :value="d2.pk">
                {{ d2.name }}
              </option>
            </CFormSelect>
          </CCol>
        </CRow>
      </CCol>

      <CCol md="12" lg="7">
        <CRow>
          <CCol md="4" class="mb-2">
            <CFormInput
              v-model="form.basis_calc"
              placeholder="산출근거"
              maxlength="18"
              :disabled="disabled"
            />
          </CCol>

          <CCol md="4" lg="3" class="mb-2">
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

          <CCol md="4" lg="3" class="mb-2">
            <CFormInput
              v-model.number="form.revised_budget"
              min="0"
              placeholder="현황(변경) 지출 예산"
              type="number"
              maxlength="18"
              :disabled="disabled"
            />
          </CCol>

          <CCol md="4" lg="2" class="d-grid gap-2 d-lg-block mb-3">
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
