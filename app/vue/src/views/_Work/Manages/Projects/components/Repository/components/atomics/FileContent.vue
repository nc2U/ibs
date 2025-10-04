<script lang="ts" setup>
import {
  computed,
  type ComputedRef,
  inject,
  nextTick,
  onMounted,
  type PropType,
  ref,
  watch,
} from 'vue'
import type { FileInfo } from '@/store/types/work_git_repo.ts'
import { cutString, humanizeFileSize, timeFormat } from '@/utils/baseMixins.ts'
import { bgLight, darkSecondary } from '@/utils/cssMixins.ts'
// Import only core and commonly used languages to reduce bundle size
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import css from 'highlight.js/lib/languages/css'
import xml from 'highlight.js/lib/languages/xml' // html
import json from 'highlight.js/lib/languages/json'
import yaml from 'highlight.js/lib/languages/yaml'
import markdown from 'highlight.js/lib/languages/markdown'
import sql from 'highlight.js/lib/languages/sql'
import php from 'highlight.js/lib/languages/php'

// Register only the languages we need
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('css', css)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('json', json)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('php', php)
hljs.registerLanguage('gitignore', bash) // Use bash for gitignore

const props = defineProps({ fileData: { type: Object as PropType<FileInfo>, required: true } })

const isDark = inject<ComputedRef<Boolean>>(
  'isDark',
  computed(() => false),
)

const codeBlock = ref<HTMLElement | null>(null)

// 코드 블록 하이라이팅
const highlightCode = async () => {
  await nextTick()
  if (codeBlock.value) {
    hljs.highlightElement(codeBlock.value)
  }
}

// 초기 적용
watch(isDark, highlightCode)

// 언어 추론
const language = computed(() => {
  const ext = (props.fileData?.path ?? '').split('.').pop()?.toLowerCase()
  const langMap: { [key: string]: string } = {
    gitignore: 'gitignore',
    py: 'python',
    php: 'php',
    js: 'javascript',
    cjs: 'javascript',
    ts: 'typescript',
    mts: 'typescript',
    html: 'html',
    htm: 'html',
    vue: 'html',
    css: 'css',
    scss: 'css',
    sass: 'css',
    json: 'json',
    yaml: 'yaml',
    yml: 'yaml',
    sh: 'bash',
    md: 'markdown',
    sql: 'sql',
  }
  return langMap[ext || ''] || 'plaintext'
})

onMounted(() => {
  if (props.fileData) highlightCode()
})
</script>

<template>
  <CRow>
    <CCol class="file-content" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
      <div class="file-viewer">
        <CTable
          responsive
          :class="bgLight"
          class="mb-0"
          style="width: 100%; border-collapse: collapse"
        >
          <CTableRow v-if="fileData">
            <CTableDataCell class="py-2 px-3 strong truncate">{{ fileData?.path }}</CTableDataCell>
            <CTableDataCell class="px-3 text-right" style="width: 160px">
              <b :class="bgLight">SHA</b> : {{ cutString(fileData?.sha, 7) }}
            </CTableDataCell>
            <CTableDataCell class="px-3 text-right" style="width: 160px">
              <b :class="bgLight">Size</b> : {{ humanizeFileSize(fileData?.size) }}
            </CTableDataCell>
            <CTableDataCell class="px-3 text-right" style="width: 250px">
              <b :class="bgLight">modified</b> : {{ timeFormat(fileData?.modified as string) }}
            </CTableDataCell>
          </CTableRow>
        </CTable>
        <v-card v-if="fileData?.binary" class="py-5 px-3" :color="darkSecondary">
          <code>{{ fileData?.message }}</code>
        </v-card>
        <pre
          v-else-if="fileData?.content"
          class="code-block"
        ><code ref="codeBlock" :class="`language-${language}`"
        >{{ fileData?.content }}</code></pre>
        <pre v-else class="code-block"><code>로딩 중...</code></pre>
      </div>
    </CCol>
  </CRow>
</template>

<style lang="scss" scoped>
.file-content {
  padding: 20px;
}

.file-viewer {
  width: 100%;
}

.code-block {
  background: #fafafa;
  padding: 1em;
  white-space: pre-wrap;
  font-family: monospace;
  border: 1px solid #ddd;
  border-radius: 1px;
}

table {
  border-color: #ddd;
  border-width: 1px 1px 0 1px;
}

.theme-light .code-block {
  background: #fafafa;
  border-color: #ddd;
}

.theme-dark .code-block {
  background: #282c34;
  border-color: #444;

  table {
    border-color: #444;
  }
}
</style>
