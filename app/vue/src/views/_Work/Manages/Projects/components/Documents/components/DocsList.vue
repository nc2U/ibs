<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import NoData from '@/views/_Work/components/NoData.vue'
import AddNewDoc from './AddNewDoc.vue'

defineProps({
  projStatus: { type: Array, default: () => [] },
  docsList: { type: Array, default: () => [] },
})

const route = useRoute()
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>문서</h5>
    </CCol>

    <AddNewDoc v-if="route.name === '(문서)'" :proj-status="projStatus" />
  </CRow>

  <NoData v-if="!docsList.length" />

  <CRow v-else>
    <CCol></CCol>
  </CRow>
</template>
