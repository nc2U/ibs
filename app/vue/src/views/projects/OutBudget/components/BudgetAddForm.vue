<script lang="ts" setup>
import { computed, inject, reactive, ref, watch } from 'vue'
import { isValidate } from '@/utils/helper'
import { usePerms } from '@/composables/usePerms'
import type { ProOutBudget } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

export interface AccItem {
  value: number
  label: string
}

const props = defineProps({ disabled: Boolean })
const emit = defineEmits<{
  (e: 'on-submit', payload: Omit<ProOutBudget, 'pk' | 'project'>): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const accountList = inject<AccItem[]>('accountList')

const refAlertModal = ref()
const refConfirmModal = ref()

const validated = ref(false)
const form = reactive<{
  account: number | ''
  basis_calc: string
  budget: number | '' | null
  revised_budget: number | '' | null
}>({
  account: '',
  basis_calc: '',
  budget: null,
  revised_budget: null,
})

watch(
  () => props.disabled,
  newVal => {
    if (newVal) resetForm()
  },
)

const isFormValid = computed(
  () =>
    Boolean(form.account) && form.budget !== null && form.budget !== '' && Number(form.budget) >= 0,
)

const onSubmit = (event: Event) => {
  if (canProjectUpdate.value) {
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
  emit('on-submit', {
    account: Number(form.account),
    basis_calc: form.basis_calc.trim(),
    budget: Number(form.budget),
    revised_budget:
      form.revised_budget !== null && form.revised_budget !== ''
        ? Number(form.revised_budget)
        : null,
  })
  validated.value = false
  refConfirmModal.value.close()
  resetForm()
}

const resetForm = () => {
  form.account = ''
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
            <CFormSelect v-model.number="form.account" required :disabled="disabled">
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
              maxlength="255"
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
          <CCol md="12" class="d-grid gap-2 d-lg-block text-end mb-3">
            <v-btn color="primary" type="submit" :disabled="disabled || !isFormValid">
              지출 예산 추가
            </v-btn>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 지출 예산 등록</template>
    <template #default> 프로젝트의 지출 예산 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
