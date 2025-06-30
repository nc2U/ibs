<script lang="ts" setup>
import type { PropType } from 'vue'
import type { News } from '@/store/types/work_inform.ts'
import NewsObj from './NewsObj.vue'
import NoData from '@/views/_Work/components/NoData.vue'

defineProps({
  newsList: { type: Array as PropType<News[]>, default: () => [] },
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>{{ $route.name.replace(/^\((.*)\)$/, '$1') }}</h5>
    </CCol>

    <CCol class="text-right">
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="sm" />
        <router-link to="" class="ml-1">새 공지</router-link>
      </span>
    </CCol>
  </CRow>

  <template v-if="!newsList.length">
    <NoData />
  </template>

  <template v-else>
    <NewsObj v-for="news in newsList" :news="news" :key="news.pk" />
  </template>
</template>
