<script lang="ts" setup>
import DOMPurify from 'dompurify'

defineProps({ content: { type: String, required: true } })
</script>

<template>
  <CRow class="p-4 mb-5">
    <CCol style="font-size: 1.03em; line-height: 1.6">
      <div v-html="DOMPurify().sanitize(content)" />
    </CCol>
  </CRow>
</template>
