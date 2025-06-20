<script lang="ts" setup>
import { computed, type ComputedRef, inject, nextTick, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import { cutString, humanizeFileSize, timeFormat } from '@/utils/baseMixins.ts'
import { bgLight, btnSecondary, darkSecondary } from '@/utils/cssMixins.ts'
import hljs from 'highlight.js'

const props = defineProps({
  repoName: { type: String, required: true },
  currBranch: { type: String, required: true },
})

const emit = defineEmits(['into-root', 'into-path', 'goto-trees'])

const fileData = ref()

const isDark = inject<ComputedRef<Boolean>>(
  'isDark',
  computed(() => false),
)

const route = useRoute()
const repoId = computed(() => Number(route.params.repoId))
const sha = computed(() => route.params.sha as string)
const path = computed(() => route.params.path)

const gitStore = useGitRepo()
const fetchFileView = (repo: number, path: string, sha: string) =>
  gitStore.fetchFileView(repo, path, sha)

const currentPath = computed<string[]>(() =>
  typeof path.value === 'string' && path.value ? path.value.split('/').slice(0, -1) : [],
)

const intoPath = (path: string) => {
  const index = currentPath.value.indexOf(path)
  const nowPath = index === -1 ? null : currentPath.value.slice(0, index + 1).join('/')
  emit('into-path', { sha: '', path: nowPath })
}

const codeBlock = ref<HTMLElement | null>(null)

// 언어 추론
const language = computed(() => {
  const ext = (fileData.value?.path ?? '').split('.').pop()?.toLowerCase()
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

// 코드 블록 하이라이팅
const highlightCode = async () => {
  await nextTick()
  if (codeBlock.value) {
    hljs.highlightElement(codeBlock.value)
  }
}

// 초기 적용
watch(isDark, highlightCode)

onBeforeMount(async () => {
  fileData.value = await fetchFileView(repoId.value, path.value as string, sha.value)
  await highlightCode()
})
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
        {{ fileData?.name }}
        @ {{ currBranch }}
      </h5>
    </CCol>
  </CRow>

  <CRow class="mb-0 pl-2">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="emit('goto-trees')">
        목록으로
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
          <CTableRow v-if="fileData">
            <CTableDataCell class="py-2 px-3 strong truncate">{{ fileData?.path }}</CTableDataCell>
            <CTableDataCell class="px-3 text-right" style="width: 160px">
              <b :class="bgLight">SHA</b> : {{ cutString(fileData?.sha, 7) }}
            </CTableDataCell>
            <CTableDataCell class="px-3 text-right" style="width: 160px">
              <b :class="bgLight">Size</b> : {{ humanizeFileSize(fileData?.size) }}
            </CTableDataCell>
            <CTableDataCell class="px-3 text-right" style="width: 250px">
              <b :class="bgLight">modified</b> : {{ timeFormat(fileData?.modified) }}
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
        <pre v-else class="code-block"><code></code></pre>
      </div>
    </CCol>
  </CRow>

  <CRow class="mb-5 pl-2">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="emit('goto-trees')">
        목록으로
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
