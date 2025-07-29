<script lang="ts" setup>
import { type PropType } from 'vue'
import type { News } from '@/store/types/work_inform.ts'
import { useInform } from '@/store/pinia/work_inform.ts'
import NewsObj from './NewsObj.vue'
import NoData from '@/components/NoData/Index.vue'
import Pagination from '@/components/Pagination'

defineProps({
  page: { type: Number, default: 1 },
  viewForm: { type: Boolean, default: false },
  newsList: { type: Array as PropType<News[]>, default: () => [] },
})

const emit = defineEmits(['view-form', 'page-select'])

const infStore = useInform()
const newsPages = (pageNum: number) => infStore.newsPages(pageNum)
const pageSelect = (page: number) => {
  emit('page-select', page)
}
</script>

<template>
  <template v-if="!newsList.length">
    <NoData />
  </template>

  <template v-else>
    <NewsObj v-for="news in newsList" :news="news" :key="news.pk" />
  </template>

  <Pagination
    :active-page="page"
    :limit="8"
    :pages="newsPages(10)"
    @active-page-change="pageSelect"
    class="mt-3"
  />
</template>
