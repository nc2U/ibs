<script lang="ts" setup>
import type { News } from '@/store/types/work_inform'
import { useInform } from '@/store/pinia/work_inform'
import NewsItem from './NewsItem.vue'
import NoData from '@/components/NoData/Index.vue'
import Pagination from '@/components/Pagination'

interface Props {
  page?: number
  viewForm?: boolean
  newsList?: News[]
}

withDefaults(defineProps<Props>(), {
  page: 1,
  viewForm: false,
  newsList: () => [],
})

const emit = defineEmits<{
  (e: 'page-select', page: number): void
}>()

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
    <NewsItem v-for="news in newsList" :news="news" :key="news.pk" />
  </template>

  <Pagination
    v-if="newsPages(10) > 1"
    :active-page="page"
    :limit="8"
    :pages="newsPages(10)"
    @active-page-change="pageSelect"
    class="mt-3"
  />
</template>
