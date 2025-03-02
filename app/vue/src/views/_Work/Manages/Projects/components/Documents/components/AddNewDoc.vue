<script lang="ts" setup>
defineProps({ projStatus: { type: String, default: '' } })
</script>

<template>
  <CCol class="text-right">
    <span v-if="projStatus !== '9'" class="mr-2 form-text">
      <v-icon icon="mdi-plus-circle" color="success" size="sm" />
      <router-link :to="{ name: '(문서) - 추가' }" class="ml-1">새 문서</router-link>
    </span>
  </CCol>
</template>
