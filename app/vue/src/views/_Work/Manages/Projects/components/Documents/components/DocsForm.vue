<script lang="ts" setup>
import { ref } from 'vue'
import { colorLight } from '@/utils/cssMixins'
import MdEditor from '@/components/MdEditor/Index.vue'
import AddNewDoc from './AddNewDoc.vue'

defineProps({
  projStatus: { type: Array, default: () => [] },
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>새 문서</h5>
    </CCol>

    <AddNewDoc :proj-status="projStatus" />
  </CRow>

  <CRow>
    <CCard :color="colorLight" class="mb-3">
      <CCardBody>
        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">범주</CFormLabel>
          <CCol class="col-sm-10 col-md-6 col-lg-4 col-xl-3">
            <CFormSelect></CFormSelect>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2 required">제목</CFormLabel>
          <CCol class="col-sm-10">
            <CFormInput />
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel class="col-form-label text-right col-2">설명</CFormLabel>
          <CCol class="col-sm-10">
            <MdEditor></MdEditor>
          </CCol>
        </CRow>

        <CRow class="">
          <CFormLabel class="col-form-label text-right col-2">파일</CFormLabel>
          <CCol class="col-sm-10">
            <CFormInput />
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>
  </CRow>

  <CRow class="mb-5">
    <CCol>
      <CButton type="submit" color="primary" variant="outline"> 저장</CButton>
      <CButton color="light" type="submit">취소</CButton>
    </CCol>
  </CRow>
</template>
