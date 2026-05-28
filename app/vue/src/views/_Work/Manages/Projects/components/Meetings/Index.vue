<script lang="ts" setup>
import { ref } from 'vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })
</script>

<template>
  <ContentBody ref="cBody" :aside="false">
    <template v-slot:default> 회의 내용 준비 중... </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
