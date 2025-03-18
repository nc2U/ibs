<script lang="ts" setup>
import { onBeforeMount, type PropType } from 'vue'
import type { Docs as Document } from '@/store/types/docs'

defineProps({ docs: { type: Object as PropType<Document>, required: true } })

onBeforeMount(() => 1)
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>{{ docs.title }}</h5>
    </CCol>

    <CCol class="text-right">
      <span class="mr-2 form-text">
        <v-icon icon="mdi-pencil" color="warning" size="sm" />
        <router-link :to="{ name: '(문서) - 추가' }" class="ml-1">편집</router-link>
      </span>

      <span class="mr-2 form-text">
        <v-icon icon="mdi-trash-can-outline" color="secondary" size="sm" />
        <router-link :to="{ name: '(문서) - 추가' }" class="ml-1">삭제</router-link>
      </span>
    </CCol>
  </CRow>

  <CRow>
    <CCol> {{ docs }}</CCol>
  </CRow>
</template>
