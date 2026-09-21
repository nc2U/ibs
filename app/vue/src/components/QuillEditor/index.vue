<script setup lang="ts">
import { computed, type PropType } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import { useStore } from '@/store'
import '@vueup/vue-quill/dist/vue-quill.snow.css'

const store = useStore()
const isDark = computed(() => store.isDark)

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
  color: { type: String, default: '' },
  placeholder: { type: String, default: '내용을 입력하세요' },
  // 'standard' | 'minimal' | 'full' 또는 커스텀 툴바 배열
  toolbar: {
    type: [String, Array] as PropType<'standard' | 'minimal' | 'full' | any[]>,
    default: 'standard',
  },
})

// 실제 에디터 배경색 결정 (미지정 시 다크모드 여부에 따라 자동 적용)
const editorBgColor = computed(() => {
  if (props.color) return props.color
  return isDark.value ? '#212631' : '#ffffff'
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
  <div class="quill-editor-wrapper" :class="{ 'dark-mode': isDark }">
    <QuillEditor
      v-model:content="content"
      content-type="html"
      :theme="theme"
      :toolbar="resolvedToolbar"
      :style="`height: ${height}px; background-color: ${editorBgColor}`"
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

/* ═══════════════════════════════════════════════════
   다크모드 스타일
   ═══════════════════════════════════════════════════ */
.dark-mode :deep(.ql-toolbar.ql-snow) {
  background-color: #2a2b38;
  border-color: #434955;
}

.dark-mode :deep(.ql-container.ql-snow) {
  border-color: #434955;
  color: #e2e8f0;
}

/* 다크모드 툴바 아이콘 및 버튼 */
.dark-mode :deep(.ql-snow .ql-stroke) {
  stroke: #cbd5e1;
}
.dark-mode :deep(.ql-snow .ql-fill) {
  fill: #cbd5e1;
}
.dark-mode :deep(.ql-snow .ql-picker) {
  color: #cbd5e1;
}

/* 다크모드 드롭다운(피커) 목록 박스 */
.dark-mode :deep(.ql-snow .ql-picker-options) {
  background-color: #2a2b38;
  border-color: #434955;
}
.dark-mode :deep(.ql-snow .ql-picker-item:hover),
.dark-mode :deep(.ql-snow .ql-picker-item.ql-selected) {
  color: #60a5fa;
}

/* 다크모드 버튼 호버/활성화 */
.dark-mode :deep(.ql-snow.ql-toolbar button:hover .ql-stroke),
.dark-mode :deep(.ql-snow.ql-toolbar button.ql-active .ql-stroke) {
  stroke: #60a5fa;
}
.dark-mode :deep(.ql-snow.ql-toolbar button:hover .ql-fill),
.dark-mode :deep(.ql-snow.ql-toolbar button.ql-active .ql-fill) {
  fill: #60a5fa;
}

/* 다크모드 placeholder 글자 색상 */
.dark-mode :deep(.ql-editor.ql-blank::before) {
  color: #9fa0a4;
  font-style: normal;
}
</style>
