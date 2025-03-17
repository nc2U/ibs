<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useDocs } from '@/store/pinia/docs'
import type { Docs as Document } from '@/store/types/docs'
import NoData from '@/views/_Work/components/NoData.vue'
import Pagination from '@/components/Pagination'
import Docs from './Docs.vue'

defineProps({
  limit: { type: Number, default: 10 },
  page: { type: Number, default: 1 },
  docsList: { type: Array as PropType<Document[]>, default: () => [] },
})

const emit = defineEmits(['page-select'])

const docsStore = useDocs()
const docsCount = computed(() => docsStore.docsCount)
const docsPages = (num: number) => docsStore.docsPages(num)
const pageSelect = (page: number) => emit('page-select', page)
</script>

<template>
  <NoData v-if="!docsList.length" />

  <CRow v-else>
    <Docs v-for="docs in docsList" :key="docs.pk" :docs="docs" />
  </CRow>

  <Pagination
    v-if="docsCount > limit"
    :active-page="page"
    :pages="docsPages(limit)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
