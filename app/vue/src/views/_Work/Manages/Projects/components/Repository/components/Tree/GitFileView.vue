<script lang="ts" setup>
import { inject, onMounted, type PropType, ref, watch } from 'vue'
import { bgLight, btnSecondary } from '@/utils/cssMixins.ts'
import type { FileInfo } from '@/store/types/work_github.ts'
import { humanizeFileSize } from '@/utils/baseMixins.ts'
import hljs from 'highlight.js'

const props = defineProps({
  fileData: {
    type: Object as PropType<FileInfo>,
    required: true,
  },
})

const emit = defineEmits(['file-view-close'])

const isDark = inject('isDark')

const codeBlock = ref<HTMLElement | null>(null)

const themes = {
  light: 'highlight.js/styles/atom-one-light.css',
  dark: 'highlight.js/styles/atom-one-dark-reasonable.css',
}

// highlight.js 테마 CSS 동적 적용
const loadHighlightTheme = (darkMode: boolean) => {
  const id = 'hljs-theme'
  let link = document.getElementById(id) as HTMLLinkElement | null

  if (!link) {
    link = document.createElement('link')
    link.id = id
    link.rel = 'stylesheet'
    document.head.appendChild(link)
  }

  link.href = darkMode ? themes.dark : themes.light
}

// 코드 블록 하이라이팅
const highlightCode = () => {
  if (codeBlock.value) {
    hljs.highlightElement(codeBlock.value)
  }
}

// 초기 적용
onMounted(() => {
  loadHighlightTheme(isDark.value)
  highlightCode()
})

// 테마 변경 감지 (반응형으로 추적)
watch(
  () => isDark,
  val => {
    loadHighlightTheme(val.value)
    highlightCode()
  },
)
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>
        <router-link to="">Git 저장소</router-link>
        / {{ fileData?.name }}
      </h5>
    </CCol>
  </CRow>

  <CRow class="my-4">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="emit('file-view-close')">
        돌아가기
      </v-btn>
    </CCol>
  </CRow>

  <CRow>
    <CCol class="file-content">
      <div class="file-viewer">
        <table :class="bgLight" style="width: 100%">
          <tr>
            <td class="py-2 px-5 strong" style="width: 500px">{{ fileData.path }}</td>
            <td class="px-5" style="width: 150px">SHA: {{ fileData.sha }}</td>
            <td class="px-5">Size: {{ humanizeFileSize(fileData.size) }}</td>
          </tr>
        </table>
        <pre v-if="fileData.content" class="code-block">
          <code ref="codeBlock" class="language-python">{{ fileData.content }}</code>
        </pre>
        <p v-else>Loading file...</p>
      </div>
    </CCol>
  </CRow>

  <CRow class="mt-4 mb-5">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="emit('file-view-close')">
        돌아가기
      </v-btn>
    </CCol>
  </CRow>
</template>

<style lang="scss" scoped>
.code-block {
  background: #fafafa;
  padding: 1em;
  white-space: pre-wrap;
  font-family: monospace;
  border: 1px solid #ddd;
  border-radius: 1px;
}

.dark-theme {
  .code-block {
    background: #282c34;
    border-color: #444;
  }
}
</style>
