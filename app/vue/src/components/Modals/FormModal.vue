<script lang="ts" setup>
import { ref } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'

defineProps({ size: { type: String, default: '' } })

const visible = ref(false)

const callModal = () => (visible.value = true)
const close = () => (visible.value = false)
defineExpose({ callModal, close })
</script>

<template>
  <CModal
    :size="size"
    alignment="center"
    :visible="visible"
    @close="() => (visible = false)"
    @keydown.esc="() => (visible = false)"
  >
    <CModalHeader class="text-body">
      <CModalTitle>
        <slot name="icon">
          <v-icon icon="mdi-application-cog" size="small" color="blue-grey-darken-1" class="mr-2" />
        </slot>
        <slot name="header">Title</slot>
      </CModalTitle>
    </CModalHeader>
    <slot>
      <CModalBody class="text-body"> Form here...</CModalBody>
      <CModalFooter>
        <v-btn :color="btnLight" size="small" @click="() => (visible = false)"> 닫기</v-btn>
        <v-btn color="primary" size="small">확인</v-btn>
      </CModalFooter>
    </slot>
  </CModal>
</template>
