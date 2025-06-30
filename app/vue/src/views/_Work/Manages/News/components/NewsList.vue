<script lang="ts" setup>
import type { PropType } from 'vue'
import type { News } from '@/store/types/work_inform.ts'
import NewsObj from './NewsObj.vue'

defineProps({
  newsList: { type: Array as PropType<News[]>, default: () => [] },
})
</script>

<template>
  <template v-for="news in newsList" :key="news.pk">
    <NewsObj :news="news" />
  </template>
</template>
