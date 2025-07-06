<script lang="ts" setup>
import { type PropType } from 'vue'
import type { News } from '@/store/types/work_inform.ts'
import { useInform } from '@/store/pinia/work_inform.ts'
import NewsObj from './NewsObj.vue'
import NoData from '@/views/_Work/components/NoData.vue'
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
  <CRow class="py-2">
    <CCol>
      <h5>{{ ($route?.name as string).replace(/^\((.*)\)$/, '$1') }}</h5>
    </CCol>

    <CCol v-if="!viewForm" class="text-right">
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="15" />
        <router-link to="" class="ml-1" @click="emit('view-form')">새 공지</router-link>
      </span>

      <span v-if="$route.params.projId" class="mr-2 form-text">
        <v-icon icon="mdi-star" color="secondary" size="15" />
        <router-link to="" class="ml-1" @click="">지켜보기</router-link>
      </span>
    </CCol>
  </CRow>

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
