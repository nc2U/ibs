<script setup lang="ts">
import { computed, type ComputedRef, inject, type PropType } from 'vue'
import type { User } from '@/store/types/accounts'
import type { Docs } from '@/store/types/docs'
import { cutString, timeFormat } from '@/utils/baseMixins'

const props = defineProps({
  docs: { type: Object as PropType<Docs>, default: null },
  viewRoute: { type: String, required: true },
  isLawsuit: { type: Boolean, default: false },
})

const userInfo = inject<ComputedRef<User>>('userInfo')

const sortName = computed(() => props.docs?.proj_name || '본사 문서')
const sortColor = computed(() => (props.docs?.proj_sort === '2' ? 'success' : 'info'))
</script>

<template>
  <CTableRow v-if="docs" class="text-center">
    <CTableDataCell>{{ docs.pk }}</CTableDataCell>
    <CTableDataCell class="text-left">
      <v-badge :color="sortColor" :content="sortName" offset-x="-20" offset-y="-7" />
    </CTableDataCell>
    <CTableDataCell>{{ docs.execution_date }}</CTableDataCell>
    <CTableDataCell :style="{ background: `${docs.cate_color}33` || '' }">
      [{{ docs.cate_name }}]
    </CTableDataCell>
    <CTableDataCell v-if="isLawsuit" class="text-left">
      {{ cutString(docs.lawsuit_name ?? '', 26) }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <router-link
        v-if="!docs.is_secret || userInfo?.is_superuser || userInfo?.pk === docs.creator?.pk"
        :to="{ name: `${viewRoute} - 보기`, params: { docsId: docs.pk } }"
      >
        {{ cutString(docs.title, 32) }}
      </router-link>
      <span v-else class="text-grey">{{ cutString(docs.title, 32) }}</span>
      <v-icon v-if="docs.is_secret" icon="mdi-lock" size="sm" class="ml-2 text-grey" />
      <CBadge v-if="docs.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
    </CTableDataCell>
    <CTableDataCell>{{ docs.creator?.username }}</CTableDataCell>
    <CTableDataCell>{{ timeFormat(docs.created ?? '') }}</CTableDataCell>
    <CTableDataCell>{{ docs.hit }}</CTableDataCell>
  </CTableRow>
</template>
