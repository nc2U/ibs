<script lang="ts" setup>
import { useStore } from '@/store'
import { MdEditor, NormalToolbar } from 'md-editor-v3'
import type { ToolbarNames, ExposeParam } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  codeTheme: { type: String, default: 'atom' },
  height: { type: Number, default: 250 },
  placeholder: { type: String, default: '' },
  preview: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue'])

const store = useStore()
const theme = computed(() => (store.theme === 'dark' ? 'dark' : 'light'))

// 0번 인덱스에 커스텀 툴바(가운데 정렬) 배치
const toolbars: ToolbarNames[] = [
  'bold',
  'underline',
  'italic',
  'strikeThrough',
  '-',
  0,
  '-',
  'title',
  'sub',
  'sup',
  'quote',
  'unorderedList',
  'orderedList',
  'task',
  '-',
  'codeRow',
  'code',
  'link',
  'image',
  'table',
  'mermaid',
  'katex',
  '-',
  'revoke',
  'next',
  'save',
  '=',
  'prettier',
  'pageFullscreen',
  'fullscreen',
  'preview',
  'previewOnly',
  'htmlPreview',
  'catalog',
]

const editorRef = ref<ExposeParam>()

const insertCenter = () => {
  if (editorRef.value) {
    editorRef.value.insert((selectedText: string) => {
      const text = selectedText || '- 아 래 -'
      return {
        targetValue: `<center>${text}</center>`,
        select: !selectedText,
        deviationStart: selectedText ? 0 : 8,
        deviationEnd: selectedText ? 0 : 8 + text.length,
      }
    })
  }
}
</script>

<template>
  <MdEditor
    ref="editorRef"
    :modelValue="modelValue"
    @update:modelValue="val => emit('update:modelValue', val)"
    language="en-US"
    :codeTheme="codeTheme"
    :toolbars="toolbars"
    :style="`height: ${height}px`"
    :theme="theme"
    :placeholder="placeholder"
    :preview="preview"
    :noMermaid="false"
  >
    <template #defToolbars>
      <NormalToolbar
        title="가운데 정렬 (<center>)"
        @onClick="insertCenter"
      >
        <template #default>
          <svg
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="currentColor"
            style="vertical-align: -2px; cursor: pointer"
          >
            <path
              d="M3 3h18v2H3V3zm4 4h10v2H7V7zm-4 4h18v2H3v-2zm4 4h10v2H7v-2zm-4 4h18v2H3v-2z"
            />
          </svg>
        </template>
      </NormalToolbar>
    </template>
  </MdEditor>
</template>

<style lang="scss" scoped>
.dark-theme .md-editor {
  background: #2f303b !important;
}

.md-editor-dark {
  --md-bk-color: #474850;
}
</style>
