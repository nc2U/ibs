<script lang="ts" setup>
import { computed, nextTick, onMounted, type PropType, ref, watch } from 'vue'
import { btnSecondary } from '@/utils/cssMixins.ts'
import type { Commit } from '@/store/types/work.ts'
import { html } from 'diff2html'
import 'diff2html/bundles/css/diff2html.min.css'

const props = defineProps({
  headCommit: { type: Object as PropType<Commit>, required: true },
  baseCommit: { type: Object as PropType<Commit>, required: true },
  githubDiffApi: { type: Object as PropType<{ files: any }>, required: true },
})

const emit = defineEmits(['get-back'])

const getBack = () => emit('get-back')

const diffContainer = ref<HTMLElement | null>(null)
const outputFormat = ref<'line-by-line' | 'side-by-side'>('line-by-line')

const diffCode = computed(
  () =>
    props.githubDiffApi?.files
      ?.map((f: any) => f.patch)
      .filter(Boolean)
      .join('\n') || '',
)

const fetchDiff = () => {
  if (diffContainer.value) {
    ;(diffContainer.value as HTMLElement).innerHTML = html(diffCode.value, {
      drawFileList: true,
      matching: 'lines',
      outputFormat: outputFormat.value,
    })
  }
}

onMounted(() => {
  nextTick(() => {
    fetchDiff()
  })
})

watch(outputFormat, fetchDiff)

watch(
  () => props.githubDiffApi,
  newVal => {
    if (newVal?.files?.length && diffContainer.value) {
      fetchDiff()
    }
  },
  { immediate: true, deep: true },
)
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

  <div ref="diffContainer"></div>

  <CRow class="mt-5">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="getBack">돌아가기</v-btn>
    </CCol>
  </CRow>
</template>
