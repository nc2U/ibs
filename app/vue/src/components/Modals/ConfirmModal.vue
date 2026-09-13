<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'

const props = defineProps({
  itemName: { type: String, default: '아이템' },
  size: { type: String, default: '' },
  checked: { type: Boolean, default: false },
})

const emit = defineEmits(['confirm-func'])

const visible = ref(false)
const headerMessage = ref(`${props.itemName} 저장 확인`)
const bodyMessage = ref('')
const headIcon = ref('mdi-alert-box')
const headerColor = ref('red-lighten-3')
const submitBtnText = ref('확인')
const submitBtnColor = ref('red-lighten-2')

const callModal = (
  head?: string,
  body?: string,
  icon?: string,
  color?: string,
  btnText?: string,
  btnColor?: string,
) => {
  if (head) headerMessage.value = head
  if (body) bodyMessage.value = body
  if (icon) headIcon.value = icon
  if (color) headerColor.value = color
  if (btnText) submitBtnText.value = btnText
  if (btnColor) submitBtnColor.value = btnColor
  visible.value = true
}
const close = () => (visible.value = false)
defineExpose({ callModal, close })

onBeforeMount(() => {
  if (props.checked) {
    headIcon.value = 'mdi-checkbox-marked-outline'
    headerColor.value = 'brown-lighten-3'
  }
})
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
        {{ bodyMessage || `이 ${itemName}을(를) 저장 하시겠습니까?` }}
      </slot>
    </CModalBody>
    <CModalFooter>
      <slot name="footer">
        <v-btn size="small" :color="submitBtnColor" @click="emit('confirm-func')">
          {{ submitBtnText }}
        </v-btn>
      </slot>
      <v-btn color="light" size="small" @click="() => (visible = false)" flat> 닫기</v-btn>
    </CModalFooter>
  </CModal>
</template>
