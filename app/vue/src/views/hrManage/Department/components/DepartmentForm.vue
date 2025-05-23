<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, type PropType } from 'vue'
import { isValidate } from '@/utils/helper'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_human_resource } from '@/utils/pageAuth'
import { useCompany } from '@/store/pinia/company'
import { type Department } from '@/store/types/company'
import Multiselect from '@vueform/multiselect'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  department: { type: Object as PropType<Department>, default: null },
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

const form = ref<Department>({
  pk: undefined,
  company: undefined,
  upper_depart: null,
  level: 1,
  name: '',
  task: '',
})

const formsCheck = computed(() => {
  if (props.department) {
    const a = form.value.upper_depart === props.department.upper_depart
    const b = form.value.name === props.department.name
    const c = form.value.task === props.department.task

    return a && b && c
  } else return false
})

const comStore = useCompany()
const getPkDeparts = computed(() => comStore.getPkDeparts)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (write_human_resource.value) multiSubmit({ ...form.value })
    else refAlertModal.value.callModal()
  }
}

const multiSubmit = (payload: Department) => {
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
  if (props.department) {
    form.value.pk = props.department.pk
    form.value.company = props.department.company
    form.value.upper_depart = props.department.upper_depart
    form.value.level = props.department.level
    form.value.name = props.department.name
    form.value.task = props.department.task
  } else form.value.company = props.company
}

onBeforeMount(() => formDataSetup())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <div>
        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">상위부서</CFormLabel>
              <CCol sm="10">
                <Multiselect
                  v-model.number="form.upper_depart"
                  :options="getPkDeparts"
                  autocomplete="label"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                  placeholder="상위부서"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required">부서명</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model.number="form.name" required placeholder="부서명" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow>
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">주요업무</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.task" placeholder="주요업무" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </div>
    </CModalBody>

    <CModalFooter>
      <v-btn type="button" :color="btnLight" size="small" @click="$emit('close')"> 닫기</v-btn>
      <slot name="footer">
        <v-btn
          type="submit"
          :color="department ? 'success' : 'primary'"
          size="small"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="department" type="button" color="warning" size="small" @click="deleteConfirm">
          삭제
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>부서 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject(department.pk as number)">
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
