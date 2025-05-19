<script lang="ts" setup>
import { computed, onMounted, type PropType, ref, watch } from 'vue'
import { bgLight, btnSecondary } from '@/utils/cssMixins.ts'
import type { Commit } from '@/store/types/work.ts'
import { html } from 'diff2html'
import 'diff2html/bundles/css/diff2html.min.css'

const props = defineProps({
  headCommit: { type: Object as PropType<Commit>, required: true },
  baseCommit: { type: Object as PropType<Commit>, required: true },
  githubApiUrl: { type: String as PropType<string>, required: true },
  githubDiffApi: { type: Object as PropType<any>, required: true },
})

watch(
  () => props.githubDiffApi,
  newVal => getDiffCode(newVal),
)

const emit = defineEmits(['get-back'])

const getBack = () => emit('get-back')

const outputFormat = ref<'line-by-line' | 'side-by-side'>('line-by-line')

watch(
  () => outputFormat.value,
  newVal => getDiffCode(props.githubDiffApi),
)

const diffHtml = ref('')

const getDiffCode = (diff: string) => {
  diffHtml.value = html(diff, {
    drawFileList: false,
    matching: 'lines',
    outputFormat: outputFormat.value,
  })
}

const hasContent = computed(() => {
  const text = diffHtml.value.replace(/<[^>]*>/g, '').trim()
  return text.length > 0
})

onMounted(async () => getDiffCode(props.githubDiffApi))
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

  <div v-if="diffHtml && !hasContent" class="p-4" :class="bgLight">
    <CRow class="text-center">
      <CCol class="pb-5">
        <v-icon icon="mdi-file-arrow-left-right-outline" size="24" class="mb-3" />
        <h4 class="mb-4">There isn’t anything to compare.</h4>

        <span class="strong">{{ headCommit.commit_hash }}</span> 는
        <span class="strong">{{ baseCommit.commit_hash }} </span> 의 모든 커밋으로 최신 상태입니다.
        <p>
          비교를 위해
          <a
            :href="`${githubApiUrl}/compare/${baseCommit.commit_hash}...${headCommit.commit_hash}`"
            class="underline"
          >
            베이스 커밋을 변경
          </a>
          해 보세요.
        </p>
      </CCol>
    </CRow>

    <CRow class="mt-5">
      <CCol>
        <v-icon icon="mdi-invoice-text-plus-outline" size="18" />
        Showing
        <router-link to="" class="strong">0 changed files</router-link>
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

  .d2h-info {
    background-color: #181924;
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
    background-color: #3a7a4b;
    color: #fff;
  }

  .d2h-del,
  .d2h-del > .line-num1 {
    background-color: #9c4b4b;
    color: #fff;
  }

  .d2h-tag {
    background-color: #181924;
    color: #ccc;
  }

  .d2h-emptyplaceholder,
  .d2h-code-side-emptyplaceholder {
    background-color: #555;
  }

  ins {
    background-color: #3a7a4b;
    color: #fff;
    text-decoration: none;
  }

  del {
    background-color: #9c4b4b;
  }

  .d2h-ins.d2h-change {
    background-color: #68d985;
  }

  .d2h-del.d2h-change {
    background-color: #f37575;
  }
}
</style>
