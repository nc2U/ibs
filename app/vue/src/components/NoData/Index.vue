<script lang="ts" setup>
defineProps({ align: { type: String, default: 'text-center' } })
</script>

<template>
  <CRow class="my-2">
    <CCol>
      <CAlert color="warning" class="alert" :class="align">표시할 데이터가 없습니다.</CAlert>
    </CCol>
  </CRow>
</template>

<style lang="scss" scoped>
.dark-theme .alert {
  color: lightyellow;
  background: #443d2b !important;
  border-color: #564f3e !important;
}
</style>
