<script lang="ts" setup>
import { type PropType, ref } from 'vue'

defineProps({ size: { type: String as PropType<'sm' | 'lg' | 'xl'>, default: undefined } })
const emit = defineEmits(['close'])

const visible = ref(false)

const callModal = () => (visible.value = true)
const close = () => {
  if (visible.value) {
    visible.value = false
    emit('close')
  }
}
defineExpose({ callModal, close })
</script>

<template>
  <CModal
    :size="size || undefined"
    alignment="center"
    :visible="visible"
    @close="close"
    @keydown.esc="close"
  >
    <CModalHeader class="text-body">
      <CModalTitle>
        <slot name="icon">
          <v-icon icon="mdi-application-cog" size="small" color="blue-grey-darken-1" class="me-2" />
        </slot>
        <slot name="header">Title</slot>
      </CModalTitle>
    </CModalHeader>
    <slot>
      <CModalBody class="text-body"> Form here...</CModalBody>
      <CModalFooter>
        <v-btn color="primary" size="small">확인</v-btn>
        <v-btn color="light" size="small" @click="close" flat> 닫기</v-btn>
      </CModalFooter>
    </slot>
  </CModal>
</template>
