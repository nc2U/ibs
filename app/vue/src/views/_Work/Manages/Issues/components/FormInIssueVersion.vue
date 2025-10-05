<script lang="ts" setup>
import { ref } from 'vue'
import { isValidate } from '@/utils/helper'
import { btnLight } from '@/utils/cssMixins.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const emit = defineEmits(['create-version', 'close'])

const validated = ref(false)

const nVersion = ref({
  name: '',
  description: '',
  status: '1' as '1' | '2' | '3',
  wiki_page_title: '',
  effective_date: null as string | null,
  sharing: '0' as '0' | '1' | '2' | '3' | '4',
  is_default: false,
})

const createVersion = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    emit('create-version', { ...nVersion.value })
    validated.value = false
    emit('close')
  }
}

const closeModal = () => emit('close')
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="createVersion">
    <CModalBody class="text-body">
      <CRow class="mb-3">
        <CFormLabel for="name" class="col-sm-3 col-form-label text-right required">
          이름
        </CFormLabel>

        <CCol class="col-7">
          <CFormInput v-model="nVersion.name" placeholder="새 버전 이름" required />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="description" class="col-sm-3 col-form-label text-right"> 설명</CFormLabel>

        <CCol class="col-7">
          <CFormInput v-model="nVersion.description" placeholder="새 버전에 대한 설명" />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="name" class="col-sm-3 col-form-label text-right"> 상태</CFormLabel>

        <CCol class="col-7">
          <CFormSelect v-model="nVersion.status">
            <option value="1">진행</option>
            <option value="2">잠김</option>
            <option value="3">닫힘</option>
          </CFormSelect>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="name" class="col-sm-3 col-form-label text-right"> 위키 페이지</CFormLabel>

        <CCol class="col-7">
          <CFormInput v-model="nVersion.wiki_page_title" placeholder="위키 페이지 제목" />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="name" class="col-sm-3 col-form-label text-right"> 날짜</CFormLabel>

        <CCol class="col-7">
          <DatePicker v-model="nVersion.effective_date" placeholder="버전 출시 기한" />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="name" class="col-sm-3 col-form-label text-right"> 공유</CFormLabel>

        <CCol class="col-7">
          <CFormSelect v-model="nVersion.sharing">
            <option value="0">공유 없음</option>
            <option value="1">하위 프로젝트</option>
            <option value="2">상위 및 하위 프로젝트</option>
            <option value="3">최상위 및 모든 하위 프로젝트</option>
            <option value="4">모든 프로젝트</option>
          </CFormSelect>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CFormLabel for="name" class="col-sm-3 col-form-label text-right"> 기본 버전</CFormLabel>

        <CCol class="col-7 pt-2">
          <CFormCheck v-model="nVersion.is_default" />
        </CCol>
      </CRow>
    </CModalBody>

    <CModalFooter>
      <v-btn :color="btnLight" @click="closeModal">닫기</v-btn>
      <v-btn type="submit" color="primary">저장</v-btn>
    </CModalFooter>
  </CForm>
</template>
