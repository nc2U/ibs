<script lang="ts" setup>
import { ref } from 'vue'
import { isValidate } from '@/utils/helper'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const emit = defineEmits(['create-version', 'close'])

const validated = ref(false)

const nVersion = ref({
  name: '',
  description: '',
  status: '1' as '1' | '2' | '3',
  effective_date: null as string | null,
  sharing: '0' as '0' | '1' | '2' | '3' | '4',
  is_default: false,
})

const resetForm = () => {
  nVersion.value = {
    name: '',
    description: '',
    status: '1',
    effective_date: null,
    sharing: '0',
    is_default: false,
  }
  validated.value = false
}

const createVersion = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    emit('create-version', { ...nVersion.value })
    resetForm()
    emit('close')
  }
}

const closeModal = () => {
  resetForm()
  emit('close')
}
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="createVersion">
    <CModalBody class="text-body">
      <CRow class="mb-3">
        <CFormLabel for="version-name" class="col-sm-3 col-form-label text-end required">
          이름
        </CFormLabel>

        <CCol class="col-7">
          <CFormInput id="version-name" v-model="nVersion.name" placeholder="새 단계 이름" required />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="version-description" class="col-sm-3 col-form-label text-end"> 설명</CFormLabel>

        <CCol class="col-7">
          <CFormInput id="version-description" v-model="nVersion.description" placeholder="새 단계에 대한 설명" />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="version-status" class="col-sm-3 col-form-label text-end"> 상태</CFormLabel>

        <CCol class="col-7">
          <CFormSelect id="version-status" v-model="nVersion.status">
            <option value="1">진행</option>
            <option value="2">잠김</option>
            <option value="3">닫힘</option>
          </CFormSelect>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="version-date" class="col-sm-3 col-form-label text-end"> 날짜</CFormLabel>

        <CCol class="col-7">
          <DatePicker id="version-date" v-model="nVersion.effective_date" placeholder="단계 완료 기한" />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="version-sharing" class="col-sm-3 col-form-label text-end"> 공유</CFormLabel>

        <CCol class="col-7">
          <CFormSelect id="version-sharing" v-model="nVersion.sharing">
            <option value="0">공유 없음</option>
            <option value="1">하위 프로젝트</option>
            <option value="2">상위 및 하위 프로젝트</option>
            <option value="3">최상위 및 모든 하위 프로젝트</option>
            <option value="4">모든 프로젝트</option>
          </CFormSelect>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="version-default" class="col-sm-3 col-form-label text-end"> 기본 단계</CFormLabel>

        <CCol class="col-7 pt-2">
          <CFormCheck id="version-default" v-model="nVersion.is_default" />
        </CCol>
      </CRow>
    </CModalBody>

    <CModalFooter>
      <v-btn type="submit" size="small" color="primary">저장</v-btn>
      <v-btn color="light" size="small" @click="closeModal" flat>닫기</v-btn>
    </CModalFooter>
  </CForm>
</template>
