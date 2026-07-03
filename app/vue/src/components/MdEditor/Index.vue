<script lang="ts" setup>
import { useStore } from '@/store'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  codeTheme: { type: String, default: 'atom' },
  height: { type: Number, default: 250 },
  placeholder: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const store = useStore()
const theme = computed(() => (store.theme === 'dark' ? 'dark' : 'light'))
</script>

<template>
  <MdEditor
    :modelValue="modelValue"
    @update:modelValue="val => emit('update:modelValue', val)"
    language="en-US"
    :codeTheme="codeTheme"
    :toolbarsExclude="['github']"
    :style="`height: ${height}px`"
    :theme="theme"
    :placeholder="placeholder"
    :noMermaid="false"
  />
</template>

<style lang="scss" scoped>
.dark-theme .md-editor {
  background: #2f303b !important;
}

.md-editor-dark {
  --md-bk-color: #474850;
}
</style>
