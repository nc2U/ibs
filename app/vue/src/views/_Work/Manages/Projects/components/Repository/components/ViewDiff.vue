<script lang="ts" setup>
import { type PropType } from 'vue'
import { btnSecondary } from '@/utils/cssMixins.ts'
import 'diff2html/bundles/css/diff2html.min.css'
import Diff from './atomics/Diff.vue'

const props = defineProps({ gitDiff: { type: Object as PropType<any>, required: true } })

const emit = defineEmits(['get-back', 'get-diff'])
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>리비전 {{ gitDiff?.head.substring(0, 8) }} : {{ gitDiff?.base.substring(0, 8) }}</h5>
    </CCol>
  </CRow>

  <CRow class="mb-3">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="emit('get-back')"
        >목록으로</v-btn
      >
    </CCol>
  </CRow>

  <Diff :git-diff="gitDiff" @get-diff="emit('get-diff', $event)" />

  <CRow class="mt-3">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="emit('get-back')"
        >목록으로</v-btn
      >
    </CCol>
  </CRow>
</template>
