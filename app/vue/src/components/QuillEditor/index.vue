<script setup lang="ts">
import type { PropType } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'

defineProps({
  theme: { type: String as PropType<'snow' | 'bubble'>, default: 'snow' },
  height: { type: Number, default: 300 },
  color: { type: String, default: 'white' },
  placeholder: { type: String, default: '내용을 입력하세요' },
})
</script>

<template>
  <QuillEditor
    content-type="html"
    :theme="theme"
    :style="`height: ${height}px; background-color: ${color}`"
    :placeholder="placeholder"
  />
</template>
