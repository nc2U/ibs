<script lang="ts" setup>
import { type PropType, ref } from 'vue'

defineProps({ size: { type: String as PropType<'sm' | 'lg' | 'xl'>, default: undefined } })

const headMessage = ref('')
const bodyMessage = ref('')
const headIcon = ref('mdi-alert-circle')
const headColor = ref('warning')
const visible = ref(false)
const callModal = (head = '', body = '', icon = 'mdi-alert-circle', color = 'warning') => {
  headMessage.value = head
  bodyMessage.value = body
  headIcon.value = icon || 'mdi-alert-circle'
  headColor.value = color || 'warning'
  visible.value = true
}
const close = () => (visible.value = false)
defineExpose({ callModal, close })
</script>

<template>
  <CModal
    alignment="center"
    :size="size || undefined"
    :visible="visible"
    @close="() => (visible = false)"
    @keydown.esc="() => (visible = false)"
  >
    <CModalHeader class="text-body">
      <CModalTitle>
        <slot name="icon">
          <v-icon :icon="headIcon" :color="headColor" class="me-2" />
        </slot>
        <slot name="header"> {{ headMessage || ' 알림' }}</slot>
      </CModalTitle>
    </CModalHeader>
    <CModalBody class="text-body" style="line-height: 26px; white-space: pre-line">
      <slot>
        {{
          bodyMessage ||
          '이 페이지에 대한 등록 및 수정 또는 삭제 권한이 없습니다. \n관리자에게 문의하여 주십시오.'
        }}
      </slot>
    </CModalBody>
    <CModalFooter>
      <slot name="footer">
        <v-btn color="light" size="small" @click="() => (visible = false)" flat> 닫기</v-btn>
      </slot>
    </CModalFooter>
  </CModal>
</template>
