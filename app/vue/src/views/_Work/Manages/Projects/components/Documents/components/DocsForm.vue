<script lang="ts" setup>
import { ref } from 'vue'
import AddNewDoc from './AddNewDoc.vue'

defineProps({
  projStatus: { type: Array, default: () => [] },
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>새 문서</h5>
    </CCol>

    <AddNewDoc :proj-status="projStatus" />
  </CRow>
</template>
