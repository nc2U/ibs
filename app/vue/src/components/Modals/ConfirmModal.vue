<script lang="ts" setup>
import { type PropType, ref } from 'vue'

const props = defineProps({
  itemName: { type: String, default: '아이템' },
  size: { type: String as PropType<'sm' | 'lg' | 'xl'>, default: undefined },
  checked: { type: Boolean, default: false },
})

const emit = defineEmits(['confirm-func', 'close'])

const visible = ref(false)
const headerMessage = ref('')
const bodyMessage = ref('')
const headIcon = ref(props.checked ? 'mdi-checkbox-marked-outline' : 'mdi-alert-box')
const headerColor = ref(props.checked ? 'brown-lighten-3' : 'red-lighten-3')
const submitBtnText = ref('확인')
const submitBtnColor = ref('red-lighten-2')

const callModal = (
  head = '',
  body = '',
  icon?: string,
  color?: string,
  btnText = '확인',
  btnColor = 'red-lighten-2',
) => {
  headerMessage.value = head
  bodyMessage.value = body
  headIcon.value = icon || (props.checked ? 'mdi-checkbox-marked-outline' : 'mdi-alert-box')
  headerColor.value = color || (props.checked ? 'brown-lighten-3' : 'red-lighten-3')
  submitBtnText.value = btnText || '확인'
  submitBtnColor.value = btnColor || 'red-lighten-2'
  visible.value = true
}
const close = () => {
  visible.value = false
  emit('close')
}
defineExpose({ callModal, close })
</script>

<template>
  <CModal
    alignment="center"
    :size="size || undefined"
    :visible="visible"
    @close="close"
    @keydown.esc="close"
  >
    <CModalHeader class="text-body">
      <CModalTitle>
        <slot name="icon">
          <v-icon :icon="headIcon" size="22" :color="headerColor" class="me-2" />
        </slot>
        <slot name="header">{{ headerMessage || `${itemName} 저장 확인` }}</slot>
      </CModalTitle>
    </CModalHeader>
    <CModalBody class="text-body" style="line-height: 26px; white-space: pre-line">
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
      <v-btn color="light" size="small" @click="close" flat> 닫기</v-btn>
    </CModalFooter>
  </CModal>
</template>
