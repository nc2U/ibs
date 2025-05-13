<script lang="ts" setup>
import { inject, reactive, ref } from 'vue'
import { write_project } from '@/utils/pageAuth'
import AlertModal from '@/components/Modals/AlertModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({ disabled: Boolean })
const emit = defineEmits(['on-submit'])

export type SortType = {
  value: '1' | '2' | '3' | '4' | '5' | '6'
  label: string
}

const typeSort = inject<SortType[]>('typeSort')

const refAlertModal = ref()
const refConfirmModal = ref()

const validated = ref(false)
const form = reactive({
  sort: '',
  name: '',
  color: '',
  actual_area: null,
  supply_area: null,
  contract_area: null,
  average_price: null,
  price_setting: '',
  num_unit: null,
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
  form.sort = ''
  form.name = ''
  form.color = ''
  form.actual_area = null
  form.supply_area = null
  form.contract_area = null
  form.average_price = null
  form.price_setting = ''
  form.num_unit = null
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow class="p-2">
      <CCol lg="3">
        <CRow>
          <CCol lg="5" class="mb-2">
            <CFormSelect v-model="form.sort" required :disabled="disabled">
              <option value="">타입종류</option>
              <option v-for="tp in typeSort" :key="tp.value" :value="tp.value">
                {{ tp.label }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol lg="5" class="mb-2">
            <CFormInput
              v-model="form.name"
              maxlength="10"
              placeholder="타입명칭"
              required
              :disabled="disabled"
            />
          </CCol>

          <CCol lg="2" class="mb-2">
            <CFormInput
              v-model="form.color"
              title="타입색상"
              type="color"
              required
              :disabled="disabled"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="8">
        <CRow>
          <CCol lg="2" class="mb-2">
            <CFormInput
              v-model.number="form.actual_area"
              placeholder="전용면적"
              type="number"
              min="0"
              step="0.0001"
              :disabled="disabled"
            />
            <CFormFeedback invalid> 전용면적을 소소점4자리 이하로 입력하세요.</CFormFeedback>
          </CCol>
          <CCol lg="2" class="mb-2">
            <CFormInput
              v-model.number="form.supply_area"
              placeholder="공급면적"
              type="number"
              min="0"
              step="0.0001"
              :disabled="disabled"
            />
            <CFormFeedback invalid> 공급면적을 소소점4자리 이하로 입력하세요.</CFormFeedback>
          </CCol>
          <CCol lg="2" class="mb-2">
            <CFormInput
              v-model.number="form.contract_area"
              placeholder="계약면적"
              type="number"
              min="0"
              step="0.0001"
              :disabled="disabled"
            />
            <CFormFeedback invalid> 계약면적을 소소점4자리 이하로 입력하세요.</CFormFeedback>
          </CCol>

          <CCol lg="2" class="mb-2">
            <CFormInput
              v-model.number="form.average_price"
              placeholder="평균가격"
              type="number"
              min="0"
              :disabled="disabled"
            />
          </CCol>

          <CCol lg="2" class="mb-2">
            <CFormSelect v-model="form.price_setting" required :disabled="disabled">
              <option value="">공급가 설정 옵션</option>
              <option value="1">타입별 설정</option>
              <option value="2">층타입별 설정</option>
              <option value="3">호별 설정</option>
            </CFormSelect>
          </CCol>

          <CCol lg="2" class="mb-2">
            <CFormInput
              v-model.number="form.num_unit"
              placeholder="세대수"
              type="number"
              required
              :disabled="disabled"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="1">
        <CRow>
          <CCol lg="12" class="d-grid gap-2 d-lg-block mb-3">
            <v-btn color="primary" type="submit" :disabled="disabled"> 타입추가</v-btn>
          </CCol>
        </CRow>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 타입 정보 등록</template>
    <template #default> 프로젝트의 타입 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
