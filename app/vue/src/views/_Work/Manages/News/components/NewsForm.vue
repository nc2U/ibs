<script lang="ts" setup>
import { btnLight } from '@/utils/cssMixins.ts'

const emit = defineEmits(['close-form'])
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>새 {{ ($route?.name as string).replace(/^\((.*)\)$/, '$1') }}</h5>
    </CCol>

    <CCol class="text-right">
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link to="" class="ml-1">새 공지</router-link>
      </span>
    </CCol>
  </CRow>

  <CRow class="mb-3">
    <CForm>
      <CCard class="p-3">Form Call!</CCard>

      <CCol class="mt-3">
        <v-btn color="primary" size="small">저장</v-btn>
        <v-btn :color="btnLight" @click="emit('close-form')" size="small">취소</v-btn>
      </CCol>
    </CForm>
  </CRow>
</template>
