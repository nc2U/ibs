<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import TodoListApp from '@/components/TodoListApp/index.vue'

defineProps({ size: { type: String as PropType<'sm' | 'lg' | 'xl'>, default: undefined } })

const visible = ref(false)

const callModal = () => (visible.value = true)
const close = () => (visible.value = false)
defineExpose({ callModal, close })
</script>

<template>
  <CModal
    :size="size || undefined"
    :visible="visible"
    scrollable
    @close="close"
    @keydown.esc="close"
  >
    <CModalHeader>
      <CModalTitle class="text-body">
        <CIcon name="cilCalendarCheck" class="me-2" />
        할 일 목록
      </CModalTitle>
    </CModalHeader>
    <CModalBody>
      <TodoListApp />
    </CModalBody>
  </CModal>
</template>
