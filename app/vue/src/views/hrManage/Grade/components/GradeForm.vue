<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, type PropType } from 'vue'
import { useCompany } from '@/store/pinia/company'
import { isValidate } from '@/utils/helper'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_human_resource } from '@/utils/pageAuth'
import { type Grade } from '@/store/types/company'
import Multiselect from '@vueform/multiselect'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  grade: { type: Object as PropType<Grade>, default: null },
})

watch(
  () => props.company,
  newVal => {
    if (!!newVal) form.value.company = newVal
    else form.value.company = undefined
  },
)

const emit = defineEmits(['multi-submit', 'on-delete', 'close'])

const refDelModal = ref()
const refAlertModal = ref()

const validated = ref(false)

const form = ref<Grade>({
  pk: undefined,
  company: undefined,
  name: '',
  promotion_period: null,
  positions: [],
  criteria_new: '',
})

const formsCheck = computed(() => {
  if (props.grade) {
    const a = form.value.name === props.grade.name
    const b = form.value.promotion_period === props.grade.promotion_period
    const c = JSON.stringify(form.value.positions) === JSON.stringify(props.grade.positions)
    const d = form.value.criteria_new === props.grade.criteria_new

    return a && b && c && d
  } else return false
})

const comStore = useCompany()
const getPkPositions = computed(() => comStore.getPkPositions)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (write_human_resource.value) multiSubmit({ ...form.value })
    else refAlertModal.value.callModal()
  }
}

const multiSubmit = (payload: Grade) => {
  emit('multi-submit', payload)
  emit('close')
}

const deleteObject = (pk: number) => {
  emit('on-delete', pk)
  refDelModal.value.close()
  emit('close')
}

const deleteConfirm = () => {
  if (write_human_resource.value) refDelModal.value.callModal()
  else refAlertModal.value.callModal()
}

const formDataSetup = () => {
  if (props.grade) {
    form.value.pk = props.grade.pk
    form.value.company = props.grade.company
    form.value.name = props.grade.name
    form.value.promotion_period = props.grade.promotion_period
    form.value.positions = props.grade.positions
    form.value.criteria_new = props.grade.criteria_new
  } else form.value.company = props.company
}

onBeforeMount(() => formDataSetup())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <div>
        <CRow class="mb-3"></CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">직급명</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.name" required placeholder="직급명" />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label"> 승급표준년수</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.promotion_period"
                  type="number"
                  placeholder="승급표준년수"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label"> 허용직위</CFormLabel>
              <CCol sm="10">
                <Multiselect
                  v-model="form.positions"
                  :options="getPkPositions"
                  mode="tags"
                  autocomplete="label"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                  placeholder="허용직위"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label"> 신입부여기준</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.criteria_new" placeholder="신입부여기준" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </div>
    </CModalBody>

    <CModalFooter>
      <v-btn type="button" size="small" :color="btnLight" @click="$emit('close')"> 닫기</v-btn>
      <slot name="footer">
        <v-btn
          type="submit"
          size="small"
          :color="grade ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="grade" type="button" size="small" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>직급 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject(grade.pk as number)">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
