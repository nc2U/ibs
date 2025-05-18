<script lang="ts" setup>
import { computed, onMounted, type PropType, ref, watch } from 'vue'
import { btnSecondary } from '@/utils/cssMixins.ts'
import type { Commit } from '@/store/types/work.ts'
import 'diff2html/bundles/css/diff2html.min.css'
import { html } from 'diff2html'

const props = defineProps({
  headCommit: { type: Object as PropType<Commit>, required: true },
  baseCommit: { type: Object as PropType<Commit>, required: true },
})

const emit = defineEmits(['get-back'])

const getBack = () => emit('get-back')

const diffContainer = ref<HTMLElement | null>(null)
const outputFormat = ref<'line-by-line' | 'side-by-side'>('line-by-line')

// 예시 API 엔드포인트 (공개 저장소에서 token 없이 사용 가능, rate limit 주의)
const owner = 'nc2u'
const repo = 'ibs'
const base = computed(() => props.baseCommit?.commit_hash ?? '')
const head = computed(() => props.headCommit?.commit_hash ?? '')

const fetchDiff = async () => {
  const res = await fetch(
    `https://api.github.com/repos/${owner}/${repo}/compare/${base.value}...${head.value}`,
    {
      headers: {
        Accept: 'application/vnd.github.v3+json',
      },
    },
  )
  const data = await res.json()
  const patches =
    data.files
      ?.map((f: any) => f.patch)
      .filter(Boolean)
      .join('\n') || ''

  if (diffContainer.value) {
    ;(diffContainer.value as HTMLElement).innerHTML = html(patches, {
      drawFileList: true,
      matching: 'lines',
      outputFormat: outputFormat.value,
    })
  }
}

onMounted(fetchDiff)

watch(outputFormat, fetchDiff)
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
