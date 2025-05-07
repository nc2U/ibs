<script lang="ts" setup>
import { computed, type ComputedRef, inject } from 'vue'

const isDark = inject<ComputedRef<boolean>>('isDark')

const light = computed(() => (!isDark?.value ? 'light' : ''))
</script>

<template>
  <CRow class="py-2">
    <CCol class="text-right"></CCol>
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
      <CCard class="mb-3" :color="light">
        <CCardBody>
          <CRow>
            <CCol>
              <CFormCheck inline id="bug" label="버그" />
              <CFormCheck inline id="feature" label="기능" />
              <CFormCheck inline id="support" label="지원" />
            </CCol>
            <CCol class="text-right">
              <span>
                <v-icon icon="mdi-cog" color="secondary" size="sm" />
                <router-link :to="{ name: '업무 유형' }" class="ml-1">관리</router-link>
              </span>
            </CCol>
          </CRow>
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <CCard class="mb-3" :color="light">
        <CCardBody>
          <CRow class="mb-2">
            <CFormLabel for="inputEmail3" class="col-sm-2 col-form-label text-right">
              기본 버전
            </CFormLabel>
            <CCol sm="4">
              <CFormSelect>
                <option value="">없음</option>
              </CFormSelect>
            </CCol>
          </CRow>
          <CRow class="mb-2">
            <CFormLabel for="inputEmail3" class="col-sm-2 col-form-label text-right">
              기본 담당자
            </CFormLabel>
            <CCol sm="4">
              <CFormSelect>
                <option value="">없음</option>
              </CFormSelect>
            </CCol>
          </CRow>
          <CRow>
            <CFormLabel for="inputEmail3" class="col-sm-2 col-form-label text-right">
              기본 업무 요청
            </CFormLabel>
            <CCol sm="4">
              <CFormSelect>
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
