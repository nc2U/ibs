<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useDocs } from '@/store/pinia/docs'
import type { Docs as Document } from '@/store/types/docs'
import NoData from '@/views/_Work/components/NoData.vue'
import CategoryTabs from '@/components/Documents/CategoryTabs.vue'
import Docs from './Docs.vue'
import Pagination from '@/components/Pagination'

defineProps({
  limit: { type: Number, default: 10 },
  page: { type: Number, default: 1 },
  category: { type: Number, default: 0 },
  categoryList: { type: Array, default: () => [] },
  docsList: { type: Array as PropType<Document[]>, default: () => [] },
})

const emit = defineEmits(['page-select', 'select-cate'])

const docsStore = useDocs()
const docsCount = computed(() => docsStore.docsCount)
const docsPages = (num: number) => docsStore.docsPages(num)
const pageSelect = (page: number) => emit('page-select', page)

const selectCate = (cate: number) => emit('select-cate', cate)
</script>

<template>
  <CategoryTabs
    :category="category"
    :category-list="categoryList"
    @select-cate="selectCate"
    class="mb-4"
  />

  <NoData v-if="!docsList.length" class="mt-5" />

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
