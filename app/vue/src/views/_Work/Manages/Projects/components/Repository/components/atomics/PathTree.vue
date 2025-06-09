<script lang="ts" setup>
import { type PropType } from 'vue'
import type { ChangedFile } from '@/store/types/work_github.ts'

defineProps({ changeTrees: { type: Object as PropType<ChangedFile>, required: true } })
</script>

<template>
  <CRow class="text-right">
    <CCol>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-plus-circle" color="success" size="" /> 추가됨
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-circle" color="warning" size="" /> 변경됨
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-circle" color="info" size="" /> 복사됨
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-circle" color="purple" size="" /> 이름바뀜
      </span>
      <span class="mr-2" style="font-size: 0.8em">
        <v-icon icon="mdi-minus-circle" color="danger" size="" /> 삭제됨
      </span>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      {{ changeTrees }}
    </CCol>
  </CRow>
</template>
