<script lang="ts" setup>
import { ref } from 'vue'

defineProps({ news: { type: Object, required: true } })

const msg = ref('')
</script>

<template>
  <CRow>
    <CCol>
      {{ news.title }}
    </CCol>
  </CRow>
</template>
