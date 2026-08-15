<script setup lang="ts">
import type { PropType } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'

const content = defineModel<string>('content', { default: '' })

defineProps({
  theme: { type: String as PropType<'snow' | 'bubble'>, default: 'snow' },
  height: { type: Number, default: 300 },
  color: { type: String, default: 'white' },
  placeholder: { type: String, default: '내용을 입력하세요' },
})
</script>

<template>
  <div class="quill-editor-wrapper">
    <QuillEditor
      v-model:content="content"
      content-type="html"
      :theme="theme"
      :style="`height: ${height}px; background-color: ${color}`"
      :placeholder="placeholder"
    />
  </div>
</template>

<style scoped>
.quill-editor-wrapper {
  display: flex;
  flex-direction: column;
}
:deep(.ql-container) {
  font-family: inherit;
  font-size: 14px;
}
:deep(.ql-editor) {
  min-height: 150px;
}
</style>
