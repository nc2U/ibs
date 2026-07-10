<script lang="ts" setup>
import { ref } from 'vue'

const msg = ref('')
</script>

<template>
  <CCol>
    <!-- Project Tab (Placeholder or configuration) -->
    <CRow>
      <CCol lg="12">
        <CCard>
          <CCardHeader class="font-weight-bold">
            <v-icon icon="mdi-shield-account" class="mr-1" color="orange" />
            프로젝트 권한 설정
          </CCardHeader>
          <CCardBody class="text-center py-5">
            <span class="text-grey-darken-1">
              프로젝트 권한 관리 및 소속 제어는 상단 관리자 설정 메뉴를 통해 관리할 수 있습니다.
            </span>
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  </CCol>
</template>
