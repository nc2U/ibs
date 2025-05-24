<script lang="ts" setup>
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default></template>

    <template v-slot:aside></template>
  </ContentBody>
  
  <CRow class="py-2">
    <CCol>
      <h5>{{ route.name }}</h5>
    </CCol>
  </CRow>
</template>
