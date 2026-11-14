<script lang="ts" setup>
import { colorLight } from '@/utils/cssMixins'
</script>

<template>
  <CRow class="py-2">
    <CCol class="text-end"></CCol>
  </CRow>

  <CRow>
    <CCol>
      <h6>
        <v-icon icon="mdi-check" color="success" size="sm" />
        업무 유형
      </h6>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <CCard class="mb-3" :color="colorLight">
        <CCardBody>
          <CRow>
            <CCol>
              <CFormCheck inline id="bug" label="버그" />
              <CFormCheck inline id="feature" label="기능" />
              <CFormCheck inline id="support" label="지원" />
            </CCol>
            <CCol class="text-end">
              <span>
                <v-icon icon="mdi-cog" color="secondary" size="15" />
                업무 유형 관리
              </span>
            </CCol>
          </CRow>
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <CCard class="mb-3" :color="colorLight">
        <CCardBody>
          <CRow class="mb-2">
            <CFormLabel for="default-version" class="col-sm-2 col-form-label text-end">
              기본 단계
            </CFormLabel>
            <CCol sm="4">
              <CFormSelect id="default-version">
                <option value="">없음</option>
              </CFormSelect>
            </CCol>
          </CRow>
          <CRow class="mb-2">
            <CFormLabel for="default-assignee" class="col-sm-2 col-form-label text-end">
              기본 담당자
            </CFormLabel>
            <CCol sm="4">
              <CFormSelect id="default-assignee">
                <option value="">없음</option>
              </CFormSelect>
            </CCol>
          </CRow>
          <CRow>
            <CFormLabel for="default-query" class="col-sm-2 col-form-label text-end">
              기본 업무 요청
            </CFormLabel>
            <CCol sm="4">
              <CFormSelect id="default-query">
                <option value="">없음</option>
                <option value="1">나에게 할당된 업무</option>
                <option value="2">보고된 업무</option>
                <option value="3">업데이트된 업무</option>
                <option value="4">지켜보는 업무</option>
              </CFormSelect>
              <span class="form-text">공개(모든 사용자에게) 요청만 선택 가능</span>
            </CCol>
          </CRow>
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <v-btn color="primary" size="small" variant="outlined">저장</v-btn>
    </CCol>
  </CRow>
</template>
