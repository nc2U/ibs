<script lang="ts" setup="">
import { type PropType } from 'vue'
import type { Docs } from '@/store/types/docs'
import { cutString, timeFormat } from '@/utils/baseMixins'
import DOMPurify from 'dompurify'

defineProps({ docs: { type: Object as PropType<Docs>, required: true } })
</script>

<template>
  <CRow class="p-2">
    <CCol sm="8">
      <router-link :to="{ name: '(문서) - 보기', params: { docId: docs.pk } }">
        {{ cutString(docs.title, 38) }}
      </router-link>
    </CCol>
    <CCol sm="4" class="text-right">{{ timeFormat(docs.created as string, true, '/') }}</CCol>
  </CRow>
  <v-divider />
  <CRow class="mb-2">
    <CCol class="text-body">
      <div v-html="DOMPurify.sanitize(cutString(docs.content, 80) || '-기재 사항 없음-')" />
    </CCol>
  </CRow>
</template>
