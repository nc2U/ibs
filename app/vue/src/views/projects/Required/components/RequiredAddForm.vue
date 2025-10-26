<script lang="ts" setup>
import { reactive, ref, computed } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { isValidate } from '@/utils/helper'
import { useProject } from '@/store/pinia/project.ts'
import { useContract } from '@/store/pinia/contract.ts'
import type { Project } from '@/store/types/project.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ disabled: Boolean })

const projStore = useProject()
const contStore = useContract()
const project = computed(() => (projStore.project as Project)?.pk)

const refAlertModal = ref()
const refConfirmModal = ref()

const form = reactive({
  sort: 'proof' as 'proof' | 'pledge',
  document_type: null as null | number,
  quantity: null as null | number,
  require_type: 'required' as 'required' | 'optional' | 'conditional',
  description: '',
  display_order: null as null | number,
})

const validated = ref(false)

const onSubmit = (event: Event) => {
  if (write_project.value) {
    isValidate(event) ? (validated.value = true) : refConfirmModal.value.callModal()
  } else {
    refAlertModal.value.callModal()
    resetForm()
  }
}

const modalAction = async () => {
  if (!project.value) return

  try {
    await contStore.createRequiredDoc({
      ...form,
      project: project.value,
    } as any)
    validated.value = false
    refConfirmModal.value.close()
    resetForm()
  } catch (error) {
    console.error('Failed to create required document:', error)
  }
}

const resetForm = () => {
  form.sort = 'proof'
  form.document_type = null
  form.quantity = null
  form.require_type = 'required'
  form.description = ''
  form.display_order = null
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow class="p-2">
      <CCol lg="10" xl="11">
        <CRow>
          <CCol md="6" lg="4" xl="2" class="mb-2">
            <CFormSelect v-model="form.sort" :disabled="disabled" required>
              <option value="proof">증빙서류</option>
              <option value="pledge">동의서류</option>
            </CFormSelect>
          </CCol>

          <CCol md="6" lg="4" xl="2" class="mb-2">
            <CFormSelect v-model="form.document_type" :disabled="disabled" required>
              <option value="">서류 유형</option>
            </CFormSelect>
          </CCol>

          <CCol md="6" lg="4" xl="2" class="mb-2">
            <CFormInput
              v-model.number="form.quantity"
              placeholder="필요 수량"
              type="number"
              min="0"
              :disabled="disabled"
            />
          </CCol>

          <CCol md="6" lg="4" xl="2" class="mb-2">
            <CFormSelect v-model="form.require_type" :disabled="disabled" required>
              <option value="required">필수</option>
              <option value="optional">선택</option>
              <option value="conditional">조건부 필수</option>
            </CFormSelect>
          </CCol>

          <CCol md="6" lg="4" xl="2" class="mb-2">
            <CFormInput
              v-model="form.description"
              maxlength="255"
              placeholder="비고"
              :disabled="disabled"
            />
          </CCol>

          <CCol md="6" lg="4" xl="2" class="mb-2">
            <CFormInput
              v-model.number="form.display_order"
              placeholder="표시 순서"
              type="number"
              min="0"
              :disabled="disabled"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="2" xl="1">
        <CRow>
          <CCol md="12" class="d-grid gap-2 d-lg-block mb-3">
            <v-btn color="primary" type="submit" :disabled="disabled">필요서류 추가</v-btn>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 계약시 구비서류</template>
    <template #default> 프로젝트의 계약 시 구비서류 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
