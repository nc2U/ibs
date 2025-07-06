<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import { elapsedTime } from '@/utils/baseMixins.ts'
import type { News } from '@/store/types/work_inform.ts'
import { VueMarkdownIt } from '@f3ve/vue-markdown-it'
import { CRow } from '@coreui/vue'

defineProps({ news: { type: Object as PropType<News>, required: true } })

const route = useRoute()

const isProj = computed(() => !!route.params.projId)
</script>

<template>
  <CRow>
    <CCol>
      <h6>
        <span v-if="!isProj">
          <router-link :to="{ name: '(개요)', params: { projId: news.project?.slug } }">
            {{ news.project?.name }}
          </router-link>
          :
        </span>
        <router-link
          :to="{ name: '(공지) - 보기', params: { projId: news.project?.slug, newsId: news.pk } }"
        >
          {{ news.title }}

          <CBadge v-if="news.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
          <CBadge v-if="news.comments?.length" color="warning" size="sm" class="ml-1">
            +{{ news.comments.length }} 개의 댓글
          </CBadge>
          <!--          <span v-if="news.comments?.length" class="strong">-->
          <!--            ({{ news.comments.length }} 개의 댓글)-->
          <!--          </span>-->
        </router-link>
      </h6>
    </CCol>
  </CRow>

  <CRow class="mb-4 text-grey">
    <CCol>
      <router-link :to="{ name: '사용자 - 보기', params: { userId: news.author?.pk } }">
        Austin Kho
      </router-link>
      이(가)
      <router-link :to="{ name: '(작업내역)', params: { projId: news.project?.slug } }">
        {{ elapsedTime(news.created) }}
      </router-link>
      에 추가함
    </CCol>
  </CRow>

  <CRow class="mb-0">
    <VueMarkdownIt :source="news.content" />
  </CRow>

  <v-divider class="mb-4" />
</template>
