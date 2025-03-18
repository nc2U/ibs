<script lang="ts" setup>
import { type PropType } from 'vue'
import type { Docs } from '@/store/types/docs'

defineProps({ docs: { type: Object as PropType<Docs>, required: true } })
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>{{ docs.title }}</h5>
    </CCol>

    <CCol class="text-right">
      <span class="mr-2 form-text">
        <v-icon icon="mdi-pencil" color="warning" size="sm" />
        <router-link :to="{ name: '(문서) - 편집' }" class="ml-1">편집</router-link>
      </span>

      <span class="mr-2 form-text">
        <v-icon icon="mdi-trash-can-outline" color="secondary" size="sm" />
        <router-link :to="{ name: '(문서) - 삭제' }" class="ml-1">삭제</router-link>
      </span>
    </CCol>
  </CRow>

  <CRow>
    <CCol> {{ docs }}</CCol>
  </CRow>

  <CRow class="mt-5">
    <CCol class="text-right">
      <CButton color="light" @click="$router.replace({ name: '(문서)' })" size="sm">
        목록으로
      </CButton>
    </CCol>
  </CRow>
</template>
