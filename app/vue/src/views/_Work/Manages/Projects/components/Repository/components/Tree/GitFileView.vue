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
import { bgLight, btnSecondary } from '@/utils/cssMixins.ts'
import type { FileInfo } from '@/store/types/work_github.ts'
import { cutString, humanizeFileSize } from '@/utils/baseMixins.ts'
import hljs from 'highlight.js'

const props = defineProps({
  fileData: {
    type: Object as PropType<FileInfo>,
    required: true,
  },
})

const emit = defineEmits(['file-view-close'])

const isDark = inject<ComputedRef<Boolean>>(
  'isDark',
  computed(() => false),
)

const codeBlock = ref<HTMLElement | null>(null)

// 언어 추론
const language = computed(() => {
  const ext = (props.fileData?.path ?? '').split('.').pop()?.toLowerCase()
  const langMap: { [key: string]: string } = {
    gitignore: 'gitignore',
    py: 'python',
    js: 'javascript',
    ts: 'typescript',
    html: 'html',
    css: 'css',
    json: 'json',
    yaml: 'yaml',
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
        <router-link to="" @click="emit('file-view-close')">Git 저장소</router-link>
        / {{ fileData?.name }}
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
        <table :class="bgLight" style="width: 100%; border-collapse: collapse">
          <tr>
            <td class="py-2 px-5 strong">{{ fileData.path }}</td>
            <td class="px-5 text-right" style="width: 200px">
              SHA: {{ cutString(fileData.sha, 7) }}
            </td>
            <td class="px-5 text-right" style="width: 200px">
              Size: {{ humanizeFileSize(fileData.size) }}
            </td>
          </tr>
        </table>
        <pre
          v-if="fileData.content"
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
