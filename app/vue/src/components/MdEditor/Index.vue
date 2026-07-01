<script lang="ts" setup>
import { useStore } from '@/store'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { computed } from 'vue'

defineProps({
  codeTheme: { type: String, default: 'atom' },
  height: { type: Number, default: 250 },
})

const store = useStore()
const theme = computed(() => (store.theme === 'dark' ? 'dark' : 'light'))
</script>

<template>
  <MdEditor
    language="en-US"
    :codeTheme="codeTheme"
    :toolbarsExclude="['github']"
    :style="`height: ${250}px`"
    :theme="theme"
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
