<script lang="ts" setup>
import { ref } from 'vue'

const props = defineProps({
  itemName: { type: String, default: '아이템' },
  size: { type: String, default: '' },
})

const emit = defineEmits(['confirm-func'])

const visible = ref(false)
const headerMessage = ref(`${props.itemName} 삭제 확인`)
const bodyMessage = ref('')
const headIcon = ref('mdi-alert-octagram')
const headerColor = ref()

const callModal = (head?: string, body?: string, icon?: string, color = 'red-lighten-2') => {
  if (head) headerMessage.value = head
  if (body) bodyMessage.value = body
  if (icon) headIcon.value = icon
  if (color) headerColor.value = color
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
          <v-icon :icon="headIcon" size="22" :color="headerColor" class="mr-2" />
        </slot>
        <slot name="header">{{ headerMessage }}</slot>
      </CModalTitle>
    </CModalHeader>
    <CModalBody class="text-body" style="line-height: 26px">
      <slot>
        {{ bodyMessage || `이 ${itemName}을(를) 삭제 하시겠습니까?` }}
      </slot>
    </CModalBody>
    <CModalFooter>
      <slot name="footer">
        <v-btn size="small" color="red-darken-3" @click="emit('confirm-func')">삭제</v-btn>
      </slot>
      <v-btn color="light" size="small" @click="() => (visible = false)" flat> 닫기</v-btn>
    </CModalFooter>
  </CModal>
</template>
