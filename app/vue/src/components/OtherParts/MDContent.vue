<script lang="ts" setup>
import { markdownRender } from '@/utils/helper.ts'
import DOMPurify from 'dompurify'

defineProps({ content: { type: String, default: '' } })
</script>

<template>
  <CRow class="p-3 mb-5">
    <CCol>
      <div v-html="markdownRender(content)" />
    </CCol>
  </CRow>
</template>
