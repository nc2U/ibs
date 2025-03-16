<script lang="ts" setup>
import NoData from '@/views/_Work/components/NoData.vue'
import Docs from './Docs.vue'

defineProps({
  docsList: { type: Array, default: () => [] },
})
</script>

<template>
  <NoData v-if="!docsList.length" />

  <CRow v-else>
    <Docs v-for="docs in docsList" :key="docs.pk" :docs="docs" />
  </CRow>
</template>
