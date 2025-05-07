<script lang="ts" setup>
import { ref, reactive, inject } from 'vue'
import { write_project } from '@/utils/pageAuth'
import Multiselect from '@/components/MultiSelect/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

defineProps({ disabled: Boolean })
const emit = defineEmits(['on-submit'])

const getTypes = inject('getTypes')

const refAlertModal = ref()
const refConfirmModal = ref()

const validated = ref(false)
const form = reactive({
  types: [] as number[],
  opt_code: '',
  opt_name: '',
  opt_desc: '',
  opt_maker: '',
  opt_price: null as null | number,
  opt_deposit: null as null | number,
  opt_balance: null as null | number,
})

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
  form.types = []
  form.opt_code = ''
  form.opt_name = ''
  form.opt_desc = ''
  form.opt_maker = ''
  form.opt_price = null
  form.opt_deposit = null
  form.opt_balance = null
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow class="p-2">
      <CCol lg="6" xl="3">
        <CRow>
          <CCol lg="12" xl="7" class="mb-2">
            <Multiselect
              v-model="form.types"
              :options="getTypes"
              placeholder="타입구분"
              :classes="{ search: 'form-control multiselect-search' }"
              required
              :disabled="disabled"
            />
            <CFormFeedback invalid> 적용 타입을 선택하세요.</CFormFeedback>
          </CCol>

          <CCol lg="12" xl="5" class="mb-2">
            <CFormInput
              v-model="form.opt_code"
              maxlength="20"
              placeholder="품목 코드"
              :disabled="disabled"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="6" xl="3">
        <CRow>
          <CCol lg="12" xl="6" class="mb-2">
            <CFormInput
              v-model="form.opt_name"
              maxlength="100"
              placeholder="품목 이름"
              required
              :disabled="disabled"
            />
            <CFormFeedback invalid> 유상 옵션 품목 이름을 입력하세요.</CFormFeedback>
          </CCol>

          <CCol lg="12" xl="6" class="mb-2">
            <CFormInput
              v-model="form.opt_desc"
              maxlength="200"
              placeholder="세부 옵션"
              :disabled="disabled"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="12" xl="5">
        <CRow>
          <CCol lg="6" xl="3" class="mb-2">
            <CFormInput v-model="form.opt_maker" placeholder="제조사" :disabled="disabled" />
          </CCol>
          <CCol lg="6" xl="3" class="mb-2">
            <CFormInput
              v-model.number="form.opt_price"
              placeholder="옵션 가격"
              type="number"
              min="0"
              required
              :disabled="disabled"
            />
            <CFormFeedback invalid> 유상 옵션 금액을 입력하세요.</CFormFeedback>
          </CCol>

          <CCol lg="6" xl="3" class="mb-2">
            <CFormInput
              v-model.number="form.opt_deposit"
              placeholder="계약금"
              type="number"
              min="0"
              :disabled="disabled"
            />
          </CCol>

          <CCol lg="6" xl="3" class="mb-2">
            <CFormInput
              v-model.number="form.opt_balance"
              placeholder="잔금"
              type="number"
              min="0"
              :disabled="disabled"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="12" xl="1">
        <CCol lg="12" class="d-grid gap-2 d-lg-block mb-3 text-center">
          <v-btn color="primary" type="submit" :disabled="disabled"> 옵션추가</v-btn>
        </CCol>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 옵션 정보 등록</template>
    <template #default> 이 유상 옵션 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
