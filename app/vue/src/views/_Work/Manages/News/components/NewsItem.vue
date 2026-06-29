<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { markdownRender } from '@/utils/helper.ts'
import { elapsedTime } from '@/utils/baseMixins.ts'
import type { News } from '@/store/types/work_inform.ts'

defineProps({ news: { type: Object as PropType<News>, required: true } })

const route = useRoute()

const isProj = computed(() => !!route.params.projId)

const { can, PERM } = usePerms()
</script>

<template>
  <v-card
    variant="flat"
    border
    class="mb-4 pa-4 news-card"
    :class="news.is_important ? 'card-yellow' : 'card-white'"
  >
    <CRow>
      <CCol>
        <h6 class="mb-1">
          <span v-if="!isProj">
            <router-link
              :to="{ name: '(개요)', params: { projId: news.project?.slug } }"
              class="text-info"
            >
              [{{ news.project?.name }}]
            </router-link>
          </span>
          <router-link
            v-if="can(PERM.NEWS_READ)"
            :to="{ name: '(공지) - 보기', params: { projId: news.project?.slug, newsId: news.pk } }"
            class="text-decoration-none font-weight-bold"
          >
            <CBadge v-if="news.is_important" color="primary" size="" class="mr-2">중요 공지</CBadge>
            {{ news.title }}

            <CBadge v-if="news.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
            <CBadge v-if="news.comments?.length" color="info" size="sm" class="ml-1">
              <v-icon icon="mdi-comment-outline" size="x-small" /> {{ news.comments.length }}
            </CBadge>
          </router-link>
          <span v-else class="font-weight-bold text-muted">
            <CBadge v-if="news.is_important" color="primary" size="" class="mr-2">중요 공지</CBadge>
            {{ news.title }}

            <CBadge v-if="news.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
            <CBadge v-if="news.comments?.length" color="info" size="sm" class="ml-1">
              <v-icon icon="mdi-comment-outline" size="x-small" /> {{ news.comments.length }}
            </CBadge>
          </span>
        </h6>
      </CCol>
    </CRow>

    <CRow class="mb-3 text-grey small">
      <CCol>
        <v-icon icon="mdi-account-outline" size="small" class="mr-1" />
        <router-link :to="{ name: '사용자 - 보기', params: { userId: news.author?.pk } }">
          Austin Kho
        </router-link>
        <span class="mx-2">|</span>
        <v-icon icon="mdi-clock-outline" size="small" class="mr-1" />
        <router-link :to="{ name: '(실행기록)', params: { projId: news.project?.slug } }">
          {{ elapsedTime(news.created) }}
        </router-link>
      </CCol>
    </CRow>

    <CRow class="mb-0">
      <CCol v-html="markdownRender(news.content)" class="news-content" />
    </CRow>
  </v-card>
</template>
