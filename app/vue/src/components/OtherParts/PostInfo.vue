<script lang="ts" setup>
import { type PropType } from 'vue'
import { toPrint } from '@/utils/docsMixins'
import { timeFormat } from '@/utils/baseMixins'
import type { Docs } from '@/store/types/docs'

defineProps({ docs: { type: Object as PropType<Docs>, required: true } })
</script>

<template>
  <CRow class="text-blue-grey mb-5">
    <CCol>
      <small class="me-3">작성자 : {{ docs.creator?.username }}</small>
      <small class="me-2">
        <v-icon icon="mdi-eye" size="small" />
        <span class="ms-1">{{ docs.hit }}</span>
      </small>
      <small class="me-2 text-btn" @click="toPrint(docs.title)">
        <v-icon icon="mdi-printer" size="small" />
        <span class="ms-1">프린트</span>
      </small>
    </CCol>

    <CCol class="text-end" md="3">
      <small>
        <v-icon icon="mdi-calendar-clock" size="small" />
        <span class="ms-2">{{ timeFormat(docs.created ?? '') }}</span>
      </small>
    </CCol>
  </CRow>
</template>
