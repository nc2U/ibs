<script lang="ts" setup>
import { ref, reactive } from 'vue'
import { write_project } from '@/utils/pageAuth'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps({ disabled: Boolean })
const emit = defineEmits(['on-submit'])

const refAlertModal = ref()
const refConfirmModal = ref()

const validated = ref(false)
const form = reactive({
  order_number: null,
  sort: '',
  name: '',
  is_default_for_uncontracted: false,
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
  form.order_number = null
  form.sort = ''
  form.name = ''
  form.is_default_for_uncontracted = false
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow class="p-2" color="success">
      <CCol md="2" class="mb-2">
        <CFormInput
          v-model.number="form.order_number"
          placeholder="등록차수"
          type="number"
          min="1"
          required
          :disabled="disabled"
        />
      </CCol>

      <CCol md="2" class="mb-2">
        <CFormSelect v-model="form.sort" :disabled="disabled" required>
          <option value="">구분선택</option>
          <option value="1">조합모집</option>
          <option value="2">일반분양</option>
        </CFormSelect>
      </CCol>

      <CCol md="2" class="mb-2">
        <CFormInput
          v-model="form.name"
          placeholder="차수그룹명"
          maxlength="20"
          required
          :disabled="disabled"
        />
      </CCol>

      <CCol md="3" class="mb-2 pt-sm-1">
        <CFormCheck
          v-model="form.is_default_for_uncontracted"
          label="미계약세대 기본설정"
          id="is_default_for_uncontracted"
          :disabled="disabled"
        >
        </CFormCheck>
        <div class="form-text d-none d-lg-block">
          미계약 세대 분양(공급)가격 생성시 용할 기본 차수 여적
        </div>
      </CCol>

      <CCol md="3" class="d-grid gap-2 d-lg-block mb-3">
        <v-btn color="primary" type="submit" :disabled="disabled"> 그룹추가</v-btn>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 차수그룹 등록</template>
    <template #default> 프로젝트의 차수그룹 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
