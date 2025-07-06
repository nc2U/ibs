<script lang="ts" setup>
import { computed, onMounted, type PropType, ref, watch } from 'vue'
import type { DiffApi } from '@/store/types/work_git_repo.ts'
import { useRoute } from 'vue-router'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import { cutString } from '@/utils/baseMixins.ts'
import { html } from 'diff2html'
import Loading from '@/components/Loading/Index.vue'
import DOMPurify from 'dompurify'

const props = defineProps({
  gitDiff: { type: Object as PropType<DiffApi>, required: true },
  diffIndex: { type: Number, default: undefined },
})

const route = useRoute()
const repo = computed(() => Number(route.params.repoId))

const gitStore = useGitRepo()
const loading = ref(false)
const getFullDiff = async () => {
  loading.value = true
  const diff_hash = `?base=${props.gitDiff?.base}&head=${props.gitDiff?.head}`
  await gitStore.fetchGitDiff(repo.value as number, diff_hash, true)
  loading.value = false
}

const diffHtml = ref('')
const diffLines = ref(0)
const outputFormat = ref<'line-by-line' | 'side-by-side'>('line-by-line')

const getDiffCode = (diff: string) => {
  const diffText = Number.isInteger(props.diffIndex)
    ? splitDiff(diff)[props.diffIndex as number]
    : diff
  diffLines.value = diffText.split('\n').length
  diffHtml.value = html(diffText, {
    drawFileList: false,
    matching: 'lines',
    outputFormat: outputFormat.value,
  })
}

const splitDiff = (diffText: string | undefined): string[] => {
  if (!diffText) return [] // 엣지 케이스: 빈 입력

  const diffSections: string[] = []
  let currentSection: string[] = []
  const diffStartRegex = /^diff --git\s+a\/.+?\s+b\/.+/ // diff --git a/... b/... 형식 매칭

  const lines = diffText.split(/\r?\n/) // 줄 단위 분리, 마지막 줄의 \n 처리

  for (const line of lines) {
    if (diffStartRegex.test(line)) {
      if (currentSection.length) diffSections.push(currentSection.join('\n')) // 새로운 섹션 시작
      currentSection = [line]
    } else currentSection.push(line)
  }

  if (currentSection.length) diffSections.push(currentSection.join('\n')) // 마지막 섹션 추가

  return diffSections
}

watch(
  () => props.gitDiff,
  newVal => {
    if (newVal) getDiffCode(newVal.diff)
  },
)

watch(
  () => outputFormat.value,
  newVal => getDiffCode(props.gitDiff?.diff as string),
)

const hasContent = computed(() => {
  const text = DOMPurify.sanitize(diffHtml.value, {
    ALLOWED_TAGS: [], // 태그 모두 제거
    ALLOWED_ATTR: [], // 속성 모두 제거
    RETURN_TRUSTED_TYPE: false, // 일반 문자열 반환
  }).trim()
  return text.length > 0
})

onMounted(() => {
  if (props.gitDiff) getDiffCode(props.gitDiff.diff)
})
</script>

<template>
  <Loading v-model:active="loading" />
  <CRow class="mb-3">
    <CCol>
      차이점 보기 :
      <CFormCheck
        type="radio"
        name="viewChoice"
        id="c1"
        label="두줄로"
        value="line-by-line"
        inline
        v-model="outputFormat"
      />
      <CFormCheck
        type="radio"
        name="viewChoice"
        id="c2"
        label="한줄로"
        value="side-by-side"
        inline
        v-model="outputFormat"
      />
    </CCol>
  </CRow>

  <div v-if="diffHtml" v-html="diffHtml" class="diff-container" />
  <div v-else>로딩 중...</div>

  <div v-if="gitDiff?.truncated && diffLines > 800">
    <CAlert color="warning">
      Diff 가져오기 정책에 의해 1000줄 이상에 해당하는 데이터가 표시되지 않았습니다.
      <router-link to="" @click="getFullDiff"> 전체 데이터 를 보려면 클릭</router-link>
      하세요.
    </CAlert>
  </div>

  <div v-if="diffHtml && !hasContent" class="p-0">
    <CRow class="pb-5 text-center">
      <CCol>
        <svg
          aria-hidden="true"
          height="24"
          viewBox="0 0 24 24"
          version="1.1"
          width="24"
          data-view-component="true"
          class="octicon octicon-git-compare blankslate-icon mb-4"
          stroke=""
          fill="#888"
        >
          <path
            d="M16.5 19.25a3.25 3.25 0 1 1 6.5 0 3.25 3.25 0 0 1-6.5 0Zm3.25-1.75a1.75 1.75 0 1 0 .001 3.501 1.75 1.75 0 0 0-.001-3.501Z"
          />
          <path
            d="M13.905 1.72a.75.75 0 0 1 0 1.06L12.685 4h4.065a3.75 3.75 0 0 1 3.75 3.75v8.75a.75.75 0 0 1-1.5 0V7.75a2.25 2.25 0 0 0-2.25-2.25h-4.064l1.22 1.22a.75.75 0 0 1-1.061 1.06l-2.5-2.5a.75.75 0 0 1 0-1.06l2.5-2.5a.75.75 0 0 1 1.06 0ZM7.5 4.75a3.25 3.25 0 1 1-6.5 0 3.25 3.25 0 0 1 6.5 0ZM4.25 6.5a1.75 1.75 0 1 0-.001-3.501A1.75 1.75 0 0 0 4.25 6.5Z"
          />
          <path
            d="M10.095 22.28a.75.75 0 0 1 0-1.06l1.22-1.22H7.25a3.75 3.75 0 0 1-3.75-3.75V7.5a.75.75 0 0 1 1.5 0v8.75a2.25 2.25 0 0 0 2.25 2.25h4.064l-1.22-1.22a.748.748 0 0 1 .332-1.265.75.75 0 0 1 .729.205l2.5 2.5a.75.75 0 0 1 0 1.06l-2.5 2.5a.75.75 0 0 1-1.06 0Z"
          />
        </svg>
        <h5 class="mt-3 mb-4">비교할 것이 없습니다.</h5>

        <span>
          <router-link
            :to="{ name: '(저장소) - 리비전 보기', params: { sha: gitDiff.base } }"
            class="strong"
          >
            {{ cutString(gitDiff?.base ?? '', 10, '..') }}
          </router-link>
          는 최신 버전입니다.
        </span>
        <span>
          <router-link
            :to="{ name: '(저장소) - 리비전 보기', params: { sha: gitDiff.head } }"
            class="strong"
          >
            {{ cutString(gitDiff?.head, 10, '..') }}
          </router-link>
          변경된 파일 또는 변경 사항이 없습니다.
        </span>
      </CCol>
    </CRow>

    <CRow style="padding-top: 60px">
      <CCol class="pt-0">
        <v-icon icon="mdi-invoice-text-plus-outline" size="18" color="grey" />
        Showing
        <router-link to="#" class="strong">0 changed files</router-link>
        with 0 additions and 0 deletions.
      </CCol>
    </CRow>
  </div>
</template>

<style lang="scss">
.dark-theme {
  .d2h-file-header {
    background-color: #1c1d26;
  }

  .d2h-file-wrapper,
  .d2h-file-header,
  .d2h-code-linenumber,
  .d2h-code-side-linenumber {
    border-color: #4d4e57 !important;
  }

  .d2h-info {
    background-color: #2e2f3b;
    color: #999;
  }

  .line-num1,
  .line-num2,
  .d2h-cntx {
    background-color: #1c1d26;
    color: #ddd;
  }

  .d2h-ins,
  .d2h-ins > .line-num2 {
    background-color: #263834;
    color: #fff;
  }

  .d2h-del,
  .d2h-del > .line-num1 {
    background-color: #352c33;
    color: #fff;
  }

  .d2h-tag {
    background-color: #181924;
    color: #ccc;
  }

  .d2h-emptyplaceholder,
  .d2h-code-side-emptyplaceholder {
    background-color: #383940;
  }

  ins {
    background-color: #3d644d !important;
    color: #fff;
    text-decoration: none;
  }

  del {
    background-color: #6a3d42 !important;
  }

  .d2h-ins.d2h-change {
    background-color: #263834 !important;
  }

  .d2h-del.d2h-change {
    background-color: #352c33 !important;
  }
}
</style>
