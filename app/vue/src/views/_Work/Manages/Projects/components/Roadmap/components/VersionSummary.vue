<script lang="ts" setup></script>

<template>
  <CRow class="mb-4">
    <CCol>
      <div class="p-2 border">
        <CRow class="mb-2">
          <CCol class="col-4 col-lg-6 col-xl-4">
            <CFormSelect readonly disabled>
              <option>유형</option>
              <option>상태</option>
              <option>우선순위</option>
              <option>작성자</option>
              <option>담당자</option>
              <option>범주</option>
            </CFormSelect>
          </CCol>
          <CCol style="padding-top: 6px">별 업무</CCol>
        </CRow>
        <CRow class="my-2">
          <CCol class="col-3 text-right">결함</CCol>
          <CCol class="col-6">
            <CProgress value="10" color="success" />
          </CCol>
          <CCol class="col-3">4/5</CCol>

          <CCol class="col-3 text-right">기능</CCol>
          <CCol class="col-6">
            <CProgress />
          </CCol>
          <CCol class="col-3">1/1</CCol>
        </CRow>
      </div>
    </CCol>
  </CRow>
</template>
