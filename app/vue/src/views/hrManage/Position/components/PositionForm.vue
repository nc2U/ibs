<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { useCompany } from '@/store/pinia/company'
import { isValidate } from '@/utils/helper'
import { write_human_resource } from '@/utils/pageAuth'
import { type Position } from '@/store/types/company'
import Multiselect from '@vueform/multiselect'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  position: { type: Object, default: null },
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

const form = ref<Position>({
  pk: undefined,
  company: undefined,
  name: '',
  grades: [],
  desc: '',
})

const formsCheck = computed(() => {
  if (props.position) {
    const a = form.value.name === props.position.name
    const b = form.value.grades === props.position.grades
    const c = form.value.desc === props.position.desc

    return a && b && c
  } else return false
})

const comCompany = useCompany()
const getPkGrades = computed(() => comCompany.getPkGrades)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (write_human_resource.value) multiSubmit({ ...form.value })
    else refAlertModal.value.callModal()
  }
}

const multiSubmit = (payload: Position) => {
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
  if (props.position) {
    form.value.pk = props.position.pk
    form.value.company = props.position.company
    form.value.name = props.position.name
    form.value.grades = props.position.grades
    form.value.desc = props.position.desc
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
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required">직위명</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.name" required placeholder="직위명" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">직급</CFormLabel>
              <CCol sm="10">
                <Multiselect
                  v-model="form.grades"
                  :options="getPkGrades"
                  mode="tags"
                  autocomplete="label"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                  placeholder="직급"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">설명</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.desc" placeholder="설명" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </div>
    </CModalBody>

    <CModalFooter>
      <CButton type="button" color="light" @click="$emit('close')"> 닫기</CButton>
      <slot name="footer">
        <CButton type="submit" :color="position ? 'success' : 'primary'" :disabled="formsCheck">
          저장
        </CButton>
        <CButton v-if="position" type="button" color="danger" @click="deleteConfirm">
          삭제
        </CButton>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>직급 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <CButton color="danger" @click="deleteObject(position.pk)">삭제</CButton>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
