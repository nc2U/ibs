<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>
<template>
  <CCard class="text-body my-4 mx-2 mx-md-3 mx-xl-5">
    <slot name="header">
      <CCardHeader>
        <v-icon icon="mdi-subtitles-outline" size="small" />
        <strong class="ps-1"> {{ route?.meta.title ?? route?.name }}</strong>
      </CCardHeader>
    </slot>

    <slot>
      <CCardBody class="pb-5" style="height: 473px"> This page is under construction.</CCardBody>
    </slot>

    <slot name="footer">
      <CCardFooter>&nbsp;</CCardFooter>
    </slot>
  </CCard>
</template>
