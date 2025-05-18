<script lang="ts" setup>
import { onMounted, type PropType, ref, watch } from 'vue'
import { btnSecondary } from '@/utils/cssMixins.ts'
import type { Commit } from '@/store/types/work.ts'
import { html } from 'diff2html'
import 'diff2html/bundles/css/diff2html.min.css'

const props = defineProps({
  headCommit: { type: Object as PropType<Commit>, required: true },
  baseCommit: { type: Object as PropType<Commit>, required: true },
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

  <CRow class="mt-4">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="getBack">돌아가기</v-btn>
    </CCol>
  </CRow>
</template>
