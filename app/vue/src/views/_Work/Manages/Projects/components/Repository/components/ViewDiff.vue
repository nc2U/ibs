<script lang="ts" setup>
import { type PropType } from 'vue'
import { btnSecondary } from '@/utils/cssMixins.ts'
import 'diff2html/bundles/css/diff2html.min.css'
import Diff from './atomics/Diff.vue'

const props = defineProps({ gitDiff: { type: Object as PropType<any>, required: true } })

const emit = defineEmits(['get-back', 'get-diff'])

const getBack = () => emit('get-back')
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>리비전 {{ gitDiff?.head.substring(0, 8) }} : {{ gitDiff?.base.substring(0, 8) }}</h5>
    </CCol>
  </CRow>

  <CRow class="mb-4">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="getBack">돌아가기</v-btn>
    </CCol>
  </CRow>

  <Diff :git-diff="gitDiff" @get-diff="emit('get-diff', $event)" />

  <CRow class="mt-4">
    <CCol>
      <v-btn size="small" variant="outlined" :color="btnSecondary" @click="getBack">돌아가기</v-btn>
    </CCol>
  </CRow>
</template>
