<script lang="ts" setup>
import { ref } from 'vue'

defineProps({ size: { type: String, default: '' } })

const headMessage = ref('')
const bodyMessage = ref('')
const headIcon = ref('mdi-alert-circle')
const headColor = ref('indigo-lighten-2')
const visible = ref(false)
const callModal = (head?: string, body?: string, icon?: string, color = 'indigo-lighten-2') => {
  if (head) headMessage.value = head
  if (body) bodyMessage.value = body
  if (icon) headIcon.value = icon
  if (color) headColor.value = color
  visible.value = true
}
const close = () => (visible.value = false)
defineExpose({ callModal, close })
</script>

<template>
  <CModal
    alignment="center"
    :size="size"
    :visible="visible"
    @close="() => (visible = false)"
    @keydown.esc="() => (visible = false)"
  >
    <CModalHeader class="text-body">
      <CModalTitle>
        <slot name="icon">
          <v-icon :icon="headIcon" :color="headColor" class="mr-2" />
        </slot>
        <slot name="header"> {{ headMessage || ' 알림' }}</slot>
      </CModalTitle>
    </CModalHeader>
    <CModalBody class="text-body" style="line-height: 26px">
      <slot>
        {{
          bodyMessage ||
          '이 페이지에 대한 등록 및 수정 또는 삭제 권한이 없습니다. \n관리자에게 문의하여 주십시요.'
        }}
      </slot>
    </CModalBody>
    <CModalFooter>
      <slot name="footer">
        <v-btn color="light" @click="() => (visible = false)"> 닫기</v-btn>
      </slot>
    </CModalFooter>
  </CModal>
</template>
