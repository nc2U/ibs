<script lang="ts" setup>
import { ref, reactive, watch } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { SalesAgency } from '@/store/types/sales'
import { isValidate } from '@/utils/helper'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps({
  project: { type: Number, required: true },
})

const emit = defineEmits(['saved'])

const salesStore = useSales()
const modalRef = ref()
const isEdit = ref(false)
const targetId = ref<number | null>(null)
const validated = ref(false)

const form = reactive({
  name: '',
  is_direct_managed: true,
  business_number: '',
  ceo_name: '',
  phone: '',
  order: 1,
  is_active: true,
})

// 자체 직영 대행인 경우 외주 대행사 관련 정보(대표자명, 사업자등록번호, 대표 전화번호) 초기화
watch(
  () => form.is_direct_managed,
  newVal => {
    if (newVal) {
      form.business_number = ''
      form.ceo_name = ''
      form.phone = ''
    }
  },
)

const resetForm = () => {
  validated.value = false
  form.name = ''
  form.is_direct_managed = true
  form.business_number = ''
  form.ceo_name = ''
  form.phone = ''
  form.order = 1
  form.is_active = true
  targetId.value = null
  isEdit.value = false
}

const open = (agency?: SalesAgency) => {
  resetForm()
  if (agency) {
    isEdit.value = true
    targetId.value = agency.id
    form.name = agency.name
    form.is_direct_managed = agency.is_direct_managed
    form.business_number = agency.business_number
    form.ceo_name = agency.ceo_name
    form.phone = agency.phone
    form.order = agency.order
    form.is_active = agency.is_active
  }
  modalRef.value.callModal()
}

const isSubmitting = ref(false)

const submit = async (event: Event) => {
  if (isSubmitting.value) return

  if (isValidate(event)) {
    validated.value = true
    return
  }

  if (!form.name.trim()) {
    validated.value = true
    return
  }

  isSubmitting.value = true
  try {
    const payload = {
      ...form,
      project: props.project,
      business_number: form.is_direct_managed ? '' : form.business_number,
      ceo_name: form.is_direct_managed ? '' : form.ceo_name,
      phone: form.is_direct_managed ? '' : form.phone,
    }

    if (isEdit.value && targetId.value) {
      await salesStore.updateAgency(targetId.value, payload)
    } else {
      await salesStore.createAgency(payload)
    }
    modalRef.value.close()
    emit('saved')
  } finally {
    isSubmitting.value = false
  }
}

defineExpose({ open })
</script>

<template>
  <FormModal ref="modalRef" size="lg">
    <template #header>{{ isEdit ? '분양 대행사 수정' : '신규 분양 대행사 등록' }}</template>
    <template #default>
      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="submit">
        <CModalBody>
          <CRow class="g-3">
            <CCol md="8">
              <CFormLabel class="small required">대행사명</CFormLabel>
              <CFormInput
                v-model="form.name"
                placeholder="예: [직영] 자체분양관리 또는 (주)미래분양대행"
                required
              />
              <CFormFeedback invalid>대행사명을 입력해주세요.</CFormFeedback>
            </CCol>
            <CCol md="4" class="d-flex align-items-center pt-4">
              <CFormCheck
                id="is_direct_managed"
                v-model="form.is_direct_managed"
                label="자체 직영 대행 여부"
              />
            </CCol>
            <template v-if="!form.is_direct_managed">
              <CCol md="4">
                <CFormLabel class="small">대표자명</CFormLabel>
                <CFormInput
                  v-model="form.ceo_name"
                  placeholder="대표자 성명"
                />
              </CCol>
              <CCol md="4">
                <CFormLabel class="small">사업자등록번호</CFormLabel>
                <input
                  v-model="form.business_number"
                  v-maska
                  data-maska="###-##-#####"
                  class="form-control"
                  placeholder="000-00-00000"
                />
              </CCol>
              <CCol md="4">
                <CFormLabel class="small">대표 전화번호</CFormLabel>
                <input
                  v-model="form.phone"
                  v-maska
                  data-maska="['###-###-####', '###-####-####']"
                  class="form-control"
                  placeholder="02-000-0000"
                />
              </CCol>
            </template>
            <CCol md="4">
              <CFormLabel class="small">정렬 순서</CFormLabel>
              <CFormInput
                v-model.number="form.order"
                type="number"
                min="1"
              />
            </CCol>
            <CCol md="4" class="d-flex align-items-center pt-4">
              <CFormCheck id="is_active" v-model="form.is_active" label="사용 여부 (활성화)" />
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn
            type="submit"
            color="primary"
            size="small"
            :loading="isSubmitting"
            :disabled="isSubmitting"
          >
            {{ isEdit ? '수정 저장' : '등록하기' }}
          </v-btn>
          <v-btn color="light" size="small" flat :disabled="isSubmitting" @click="modalRef.close()"
            >취소</v-btn
          >
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>
</template>
