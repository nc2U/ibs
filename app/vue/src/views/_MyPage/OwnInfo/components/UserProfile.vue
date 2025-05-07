<script lang="ts" setup>
import { type ComputedRef, inject } from 'vue'
import { useRouter } from 'vue-router'
import type { User } from '@/store/types/accounts'

const userInfo = inject<ComputedRef<User>>('userInfo')

const router = useRouter()
</script>

<template>
  <CCardBody class="p-5">
    <CRow class="flex-md-row flex-column-reverse">
      <CCol md="4">
        <CRow class="mb-3">
          <h6>사용자 계정</h6>
          <CFormLabel for="companyCeo" class="col-sm-4 col-form-label"> 이름</CFormLabel>

          <CCol sm="8" class="pt-1">{{ userInfo?.username || '' }}</CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="companyName" class="col-sm-4 col-form-label"> 이메일 주소</CFormLabel>

          <CCol sm="8" class="pt-1">{{ userInfo?.email || '' }}</CCol>
        </CRow>

        <v-divider class="my-4" />

        <CRow class="mb-3">
          <h6>사용자 프로필</h6>
          <CFormLabel for="companyName" class="col-sm-4 col-form-label"> 닉네임</CFormLabel>

          <CCol sm="8" class="pt-1">{{ userInfo?.profile?.name || '' }}</CCol>
        </CRow>
        <CRow class="mb-3">
          <CFormLabel for="companyCeo" class="col-sm-4 col-form-label"> 생년월일</CFormLabel>

          <CCol sm="8" class="pt-1">{{ userInfo?.profile?.birth_date || '' }}</CCol>
        </CRow>

        <CRow class="mb-3">
          <CFormLabel for="companyCeo" class="col-sm-4 col-form-label"> 휴대전화</CFormLabel>

          <CCol sm="8" class="pt-1">{{ userInfo?.profile?.cell_phone || '' }}</CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol class="text-right">
            <v-btn color="info" @click="router.push({ name: '정보 수정' })"> 회원정보 변경 </v-btn>
          </CCol>
        </CRow>
      </CCol>
      <CCol md="8"></CCol>
    </CRow>
  </CCardBody>
</template>
