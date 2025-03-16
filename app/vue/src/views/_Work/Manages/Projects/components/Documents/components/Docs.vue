<script lang="ts" setup="">
import { type PropType } from 'vue'
import type { Docs } from '@/store/types/docs'

defineProps({ docs: { type: Object as PropType<Docs>, required: true } })
</script>

<template>
  <CRow>
    <CCol>{{ docs.title }}</CCol>
  </CRow>
</template>
