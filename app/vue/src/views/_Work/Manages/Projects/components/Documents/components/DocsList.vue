<script lang="ts" setup="">
import { computed, ref } from 'vue'
import NoData from '@/views/_Work/components/NoData.vue'

defineProps({
  projStatus: { type: Array, default: () => [] },
  docsList: { type: Array, default: () => [] },
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>문서</h5>
    </CCol>

    <CCol class="text-right">
      <span v-if="projStatus !== '9'" class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link :to="{ name: '(문서) - 추가' }" class="ml-1">새 문서</router-link>
      </span>
    </CCol>
  </CRow>

  <NoData v-if="!docsList.length" />

  <CRow v-else>
    <CCol></CCol>
  </CRow>
</template>
