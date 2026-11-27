<script lang="ts" setup>
import { computed, reactive, ref } from 'vue'
import { isValidate } from '@/utils/helper'
import { usePerms } from '@/composables/usePerms'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import type { Project } from '@/store/types/project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps({ disabled: Boolean })

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const refAlertModal = ref()
const refConfirmModal = ref()

const parseNum = (val: number | '' | null | undefined): number | null =>
  val !== undefined && val !== null && val !== '' ? Number(val) : null

const form = reactive({
  sort: 'proof' as 'proof' | 'pledge',
  document_type: null as null | number,
  quantity: undefined as undefined | number | '',
  require_type: 'required' as 'required' | 'optional' | 'conditional',
  description: '',
  display_order: undefined as undefined | number | '',
})

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const contStore = useContract()
const documentTypeList = computed(() => contStore.documentTypeList)
const existingTypeIds = computed(() => contStore.requiredDocsList.map(doc => doc.document_type))

const validated = ref(false)

const isFormValid = computed(() => {
  const qty = parseNum(form.quantity)
  const order = parseNum(form.display_order)
  return Boolean(form.document_type) && (qty === null || qty >= 0) && (order === null || order >= 0)
})

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

const modalAction = async () => {
  if (!project.value || !form.document_type) return
  const qty = parseNum(form.quantity)
  const order = parseNum(form.display_order)

  try {
    await contStore.createRequiredDoc({
      sort: form.sort,
      document_type: Number(form.document_type),
      require_type: form.require_type,
      description: form.description,
      project: project.value,
      quantity: qty !== null ? qty : 1,
      display_order: order !== null ? order : 0,
    })
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
  form.quantity = undefined
  form.require_type = 'required'
  form.description = ''
  form.display_order = undefined
  validated.value = false
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
              <option
                v-for="tp in documentTypeList"
                :key="tp.pk"
                :value="tp.pk"
                :disabled="existingTypeIds.includes(tp.pk)"
              >
                {{ tp.name }}{{ existingTypeIds.includes(tp.pk) ? ' (이미 등록됨)' : '' }}
              </option>
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
            <v-btn color="primary" type="submit" :disabled="disabled || !isFormValid">
              필요서류 추가
            </v-btn>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header>계약 시 구비 서류 등록</template>
    <template #default>프로젝트의 계약 시 구비 서류 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
