<script lang="ts" setup>
import { ref, reactive } from 'vue'
import { write_project } from '@/utils/pageAuth'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps({ disabled: Boolean })
const emit = defineEmits(['on-submit'])

const refAlertModal = ref()
const refConfirmModal = ref()

const form = reactive({
  sort: '',
  start_floor: '',
  end_floor: '',
  extra_cond: '',
  alias_name: '',
})

const validated = ref(false)

const onSubmit = (event: Event) => {
  if (write_project.value) {
    const el = event.currentTarget as HTMLFormElement
    if (!el.checkValidity()) {
      event.preventDefault()
      event.stopPropagation()

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
  emit('on-submit', form)
  validated.value = false
  refConfirmModal.value.close()
  resetForm()
}

const resetForm = () => {
  form.sort = ''
  form.start_floor = ''
  form.end_floor = ''
  form.extra_cond = ''
  form.alias_name = ''
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow class="p-2">
      <CCol md="2" class="mb-2">
        <CFormSelect v-model="form.sort" required :disabled="disabled">
          <option value="">---------</option>
          <option value="1">공동주택</option>
          <option value="2">오피스텔</option>
          <option value="3">숙박시설</option>
          <option value="4">지식산업센터</option>
          <option value="5">근린생활시설</option>
          <option value="6">기타</option>
        </CFormSelect>
      </CCol>

      <CCol md="2" class="mb-2">
        <CFormInput
          v-model.number="form.start_floor"
          placeholder="시작 층"
          type="number"
          min="-10"
          required
          :disabled="disabled"
        />
      </CCol>

      <CCol md="2" class="mb-2">
        <CFormInput
          v-model.number="form.end_floor"
          placeholder="종료 층"
          type="number"
          min="-10"
          required
          :disabled="disabled"
        />
      </CCol>

      <CCol md="2" class="mb-2">
        <CFormInput
          v-model="form.extra_cond"
          maxlength="20"
          placeholder="방향/위치(옵션)"
          :disabled="disabled"
        />
      </CCol>

      <CCol md="2" class="mb-2">
        <CFormInput
          v-model="form.alias_name"
          maxlength="20"
          placeholder="층별 범위 명칭"
          required
          :disabled="disabled"
        />
      </CCol>

      <CCol md="2" class="d-grid gap-2 d-lg-block mb-3">
        <v-btn color="primary" type="submit" :disabled="disabled"> 층별타입추가</v-btn>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 층별 타입 등록</template>
    <template #default> 프로젝트의 층별 범위 타입 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
