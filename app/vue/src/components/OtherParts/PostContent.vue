<script lang="ts" setup>
import sanitizeHtml from 'sanitize-html'

defineProps({ content: { type: String, required: true } })
</script>

<template>
  <CRow class="p-3 mb-5">
    <CCol>
      <div v-html="sanitizeHtml(content)" />
    </CCol>
  </CRow>
</template>
