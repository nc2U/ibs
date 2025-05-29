<script lang="ts" setup>
import { computed, onMounted, type PropType, ref, watch } from 'vue'
import { btnSecondary } from '@/utils/cssMixins.ts'
import type { Commit } from '@/store/types/work_github.ts'
import { html } from 'diff2html'
import 'diff2html/bundles/css/diff2html.min.css'
import sanitizeHtml from 'sanitize-html'

const props = defineProps({
  headCommit: { type: Object as PropType<Commit>, required: true },
  baseCommit: { type: Object as PropType<Commit>, required: true },
  diffText: { type: Object as PropType<any>, required: true },
})

watch(
  () => props.diffText,
  newVal => getDiffCode(newVal),
)

const emit = defineEmits(['get-back', 'get-diff'])

const getBack = () => emit('get-back')

const outputFormat = ref<'line-by-line' | 'side-by-side'>('line-by-line')

watch(
  () => outputFormat.value,
  newVal => getDiffCode(props.diffText),
)

const diffHtml = ref('')

const getDiffCode = (diffText: string) => {
  diffHtml.value = html(diffText, {
    drawFileList: false,
    matching: 'lines',
    outputFormat: outputFormat.value,
  })
}

const hasContent = computed(() => {
  const text = sanitizeHtml(diffHtml.value, { allowedTags: [], allowedAttributes: {} }).trim()
  return text.length > 0
})

const getDiff = () => emit('get-diff', true)

onMounted(async () => {
  if (props.diffText) getDiffCode(props.diffText)
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>리비전 {{ headCommit.pk }} : {{ baseCommit.pk }}</h5>
    </CCol>
  </CRow>
  <CRow class="mb-5">
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

  <CRow class="mb-4">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="getBack">돌아가기</v-btn>
    </CCol>
  </CRow>

  <div v-if="diffHtml" v-html="diffHtml" class="diff-container" />
  <div v-else>로딩 중...</div>

  <div v-if="diffHtml && !hasContent" class="p-4">
    <CRow class="pb-5 text-center">
      <CCol>
        <svg
          aria-hidden="true"
          height="26"
          viewBox="0 0 24 24"
          version="1.1"
          width="26"
          data-view-component="true"
          class="octicon octicon-git-compare blankslate-icon mb-4"
          stroke="grey"
          fill="grey"
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
        <h5 class="mb-4">비교할 것이 없습니다.</h5>

        <span class="strong">{{ baseCommit.commit_hash }}</span> 는 최신 버전입니다.
        <span class="strong">{{ headCommit.commit_hash }}</span>
        <span>
          의 커밋, 비교를 위해
          <router-link to="#" @click="getDiff"><u>베이스를 전환</u></router-link>
          해 보세요.
        </span>
      </CCol>
    </CRow>

    <CRow class="mt-5">
      <CCol class="pt-5">
        <v-icon icon="mdi-invoice-text-plus-outline" size="18" color="grey" />
        Showing
        <router-link to="#" class="strong">0 changed files</router-link>
        with 0 additions and 0 deletions.
      </CCol>
    </CRow>
  </div>

  <CRow class="mt-4">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="getBack">돌아가기</v-btn>
    </CCol>
  </CRow>
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
    background-color: #3d644d;
    color: #fff;
    text-decoration: none;
  }

  del {
    background-color: #6a3d42;
  }

  .d2h-ins.d2h-change {
    background-color: #263834;
  }

  .d2h-del.d2h-change {
    background-color: #352c33;
  }
}
</style>
