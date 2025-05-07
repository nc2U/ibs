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
  order_group_name: '',
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
  form.order_group_name = ''
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow class="p-2" color="success">
      <CCol md="3" class="mb-2">
        <CFormInput
          v-model.number="form.order_number"
          placeholder="등록차수"
          type="number"
          min="1"
          required
          :disabled="disabled"
        />
      </CCol>

      <CCol md="3" class="mb-2">
        <CFormSelect v-model="form.sort" :disabled="disabled" required>
          <option value="">구분선택</option>
          <option value="1">조합모집</option>
          <option value="2">일반분양</option>
        </CFormSelect>
      </CCol>

      <CCol md="3" class="mb-2">
        <CFormInput
          v-model="form.order_group_name"
          placeholder="차수그룹명"
          maxlength="20"
          required
          :disabled="disabled"
        />
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
      <v-btn color="primary" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
