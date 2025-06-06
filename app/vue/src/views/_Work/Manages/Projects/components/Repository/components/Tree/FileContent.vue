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
import { bgLight, btnSecondary, darkSecondary } from '@/utils/cssMixins.ts'
import type { FileInfo } from '@/store/types/work_github.ts'
import { cutString, humanizeFileSize, timeFormat } from '@/utils/baseMixins.ts'
import hljs from 'highlight.js'

const props = defineProps({
  repoName: { type: String, required: true },
  currPath: { type: String, default: '' },
  currBranch: { type: String, required: true },
  fileData: {
    type: Object as PropType<FileInfo>,
    required: true,
  },
})

const emit = defineEmits(['into-root', 'into-path', 'file-view-close'])

const isDark = inject<ComputedRef<Boolean>>(
  'isDark',
  computed(() => false),
)

const currentPath = computed<string[]>(() => (props.currPath ? props.currPath.split('/') : []))

const intoPath = (path: string) => {
  const index = currentPath.value.indexOf(path)
  const nowPath = index === -1 ? null : currentPath.value.slice(0, index + 1).join('/')
  emit('into-path', { sha: '', path: nowPath })
}

const codeBlock = ref<HTMLElement | null>(null)

// 언어 추론
const language = computed(() => {
  const ext = (props.fileData?.path ?? '').split('.').pop()?.toLowerCase()
  const langMap: { [key: string]: string } = {
    gitignore: 'gitignore',
    py: 'python',
    php: 'php',
    js: 'javascript',
    ts: 'typescript',
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

// 코드 블록 하이라이팅
const highlightCode = async () => {
  await nextTick()
  if (codeBlock.value) {
    hljs.highlightElement(codeBlock.value)
  }
}

// 초기 적용
onMounted(highlightCode)
watch(isDark, highlightCode)
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <router-link to="" @click="emit('into-root')">{{ repoName }}</router-link>
        <span v-for="path in currentPath" :key="path">
          /
          <router-link to="" @click="intoPath(path)">{{ path }}</router-link>
        </span>
        /
        {{ fileData.name }}
        @ {{ currBranch }}
      </h5>
    </CCol>
  </CRow>

  <CRow class="mt-4 pl-2">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="emit('file-view-close')">
        돌아가기
      </v-btn>
    </CCol>
  </CRow>

  <CRow>
    <CCol class="file-content" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
      <div class="file-viewer">
        <CTable
          responsive
          :class="bgLight"
          class="mb-0"
          style="width: 100%; border-collapse: collapse"
        >
          <CTableRow>
            <CTableDataCell class="py-2 px-5 strong truncate">{{ fileData.path }}</CTableDataCell>
            <CTableDataCell class="px-5 text-right" style="width: 160px">
              <b :class="bgLight">SHA</b> : {{ cutString(fileData.sha, 7) }}
            </CTableDataCell>
            <CTableDataCell class="px-5 text-right" style="width: 160px">
              <b :class="bgLight">Size</b> : {{ humanizeFileSize(fileData.size) }}
            </CTableDataCell>
            <CTableDataCell class="px-5 text-right" style="width: 250px">
              <b :class="bgLight">modified</b> : {{ timeFormat(fileData.modified) }}
            </CTableDataCell>
          </CTableRow>
        </CTable>
        <v-card v-if="fileData.binary" class="py-5 px-3" :color="darkSecondary">
          <code>{{ fileData.message }}</code>
        </v-card>
        <pre
          v-else-if="fileData.content"
          class="code-block"
        ><code ref="codeBlock" :class="`language-${language}`"
        >{{ fileData.content }}</code></pre>
        <p v-else>Loading file...</p>
      </div>
    </CCol>
  </CRow>

  <CRow class="mb-5 pl-2">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="emit('file-view-close')">
        돌아가기
      </v-btn>
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
