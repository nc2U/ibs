<script lang="ts" setup>
import DOMPurify from 'dompurify'

defineProps({ description: { type: String, required: true } })
</script>

<template>
  <CRow class="p-3 mb-5">
    <CCol>
      <div v-html="DOMPurify().sanitize(description)" />
    </CCol>
  </CRow>
</template>
