<script setup lang="ts">
import { computed, type PropType } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'

const content = defineModel<string>('content', { default: '' })

// 툴바 프리셋 정의
const TOOLBAR_PRESETS = {
  // 메일/게시글에 최적화된 표준 툴바
  standard: [
    [{ header: [1, 2, 3, false] }, { size: ['small', false, 'large', 'huge'] }],
    ['bold', 'italic', 'underline', 'strike'],
    [{ color: [] }, { background: [] }],
    [{ align: [] }],
    [{ list: 'ordered' }, { list: 'bullet' }, { indent: '-1' }, { indent: '+1' }],
    ['blockquote', 'code-block', 'link', 'image'],
    ['clean'],
  ],
  // 간단한 입력용 최소 툴바
  minimal: [
    ['bold', 'italic', 'underline'],
    [{ color: [] }, { background: [] }],
    [{ list: 'ordered' }, { list: 'bullet' }],
    ['link'],
    ['clean'],
  ],
  // full 옵션 (Quill 기본 풀 패키지)
  full: 'full',
}

const props = defineProps({
  theme: { type: String as PropType<'snow' | 'bubble'>, default: 'snow' },
  height: { type: Number, default: 300 },
  color: { type: String, default: 'white' },
  placeholder: { type: String, default: '내용을 입력하세요' },
  // 'standard' | 'minimal' | 'full' 또는 커스텀 툴바 배열
  toolbar: {
    type: [String, Array] as PropType<'standard' | 'minimal' | 'full' | any[]>,
    default: 'standard',
  },
})

// 실제 QuillEditor로 전달할 툴바 설정
const resolvedToolbar = computed(() => {
  if (typeof props.toolbar === 'string' && props.toolbar in TOOLBAR_PRESETS) {
    return TOOLBAR_PRESETS[props.toolbar as keyof typeof TOOLBAR_PRESETS]
  }
  return props.toolbar
})
</script>

<template>
  <div class="quill-editor-wrapper">
    <QuillEditor
      v-model:content="content"
      content-type="html"
      :theme="theme"
      :toolbar="resolvedToolbar"
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
:deep(.ql-toolbar.ql-snow) {
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  background-color: #f8fafc;
}
</style>
