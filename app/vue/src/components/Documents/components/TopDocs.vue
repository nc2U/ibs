<script setup lang="ts">
import { computed, type PropType } from 'vue'
import type { Docs } from '@/store/types/docs'
import { usePerms } from '@/composables/usePerms.ts'
import { cutString, timeFormat } from '@/utils/baseMixins'

const props = defineProps({
  docs: { type: Object as PropType<Docs>, default: null },
  viewRoute: { type: String, required: true },
  isLawsuit: { type: Boolean, default: false },
})

const { can, PERM } = usePerms()

const sortName = computed(() => props.docs?.project?.name || '본사 문서')
const sortColor = computed(() => (props.docs?.project ? 'success' : 'info'))
</script>

<template>
  <CTableRow v-if="docs" class="text-center">
    <CTableDataCell>
      <v-badge color="primary" content=" 공지 " offset-x="5" offset-y="-7" />
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <v-badge :color="sortColor" :content="sortName" offset-x="-5" offset-y="-7" />
    </CTableDataCell>
    <CTableDataCell>{{ docs.execution_date }}</CTableDataCell>
    <CTableDataCell v-if="isLawsuit" class="text-left">
      {{ cutString(docs.lawsuit_name ?? '', 26) }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <v-icon v-if="docs.is_blind" icon="mdi-eye-off" size="sm" class="mr-1 text-danger" />
      <v-icon v-if="docs.is_secret" icon="mdi-lock" size="sm" class="mr-1 text-grey" />
      <router-link
        v-if="can(PERM.DOCS_READ)"
        :to="{ name: `${viewRoute} - 보기`, params: { docsId: docs.pk } }"
      >
        {{ cutString(docs.title, 32) }}
      </router-link>
      <span v-else class="text-grey">{{ cutString(docs.title, 32) }}</span>
      <CBadge v-if="docs.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
    </CTableDataCell>
    <CTableDataCell>{{ docs.creator?.username }}</CTableDataCell>
    <CTableDataCell>{{ timeFormat(docs.created ?? '') }}</CTableDataCell>
    <CTableDataCell>{{ docs.hit }}</CTableDataCell>
  </CTableRow>
</template>
