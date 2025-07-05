<script setup lang="ts">
import { computed, type PropType } from 'vue'
import type { Docs } from '@/store/types/docs'
import { cutString, timeFormat } from '@/utils/baseMixins'

const props = defineProps({ docs: { type: Object as PropType<Docs>, default: null } })

const viewRoute = computed(() => {
  if (!!props.docs?.project) {
    if (props.docs.doc_type === 1) return 'PR 일반 문서'
    else if (props.docs.doc_type === 2) return 'PR 소송 문서'
  } else {
    if (props.docs.doc_type === 1) return '본사 일반 문서'
    else if (props.docs.doc_type === 2) return '본사 소송 문서'
  }
  return 'PR 일반 문서'
})
</script>

<template>
  <CTableRow v-if="docs" class="text-center">
    <CTableDataCell>{{ docs.pk }}</CTableDataCell>
    <CTableDataCell>
      {{ docs.type_name }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <router-link
        :to="{ name: `${viewRoute} - 보기`, params: { docsId: docs.pk } }"
        target="_blank"
      >
        {{ cutString(docs.title, 50) }}
      </router-link>
      <CBadge v-if="docs.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
    </CTableDataCell>
    <CTableDataCell>{{ timeFormat(docs.created ?? '') }}</CTableDataCell>
  </CTableRow>
</template>
