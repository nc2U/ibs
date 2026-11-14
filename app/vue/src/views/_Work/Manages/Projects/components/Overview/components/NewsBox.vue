<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from '@/store'
import { usePerms } from '@/composables/usePerms'
import type { News } from '@/store/types/work_inform'
import { elapsedTime } from '@/utils/baseMixins'

defineProps({ newsList: { type: Array as PropType<News[]>, default: () => [] } })

const route = useRoute()
const store = useStore()
const isDark = computed(() => store.theme === 'dark')

const { canViewUser } = usePerms()
</script>

<template>
  <CCard :color="isDark ? '' : 'light'" class="mb-3">
    <CCardBody>
      <CCardSubtitle class="mb-2">
        <v-icon icon="mdi-newspaper" size="sm" color="grey" class="me-1" />
        최근 공지
      </CCardSubtitle>
      <CCardText>
        <div v-for="news in newsList" :key="news.pk" class="mb-2">
          <router-link
            :to="{
              name: '(공지) - 보기',
              params: { projId: news.project?.slug || route.params.projId, newsId: news.pk },
            }"
            class="fw-bold"
          >
            {{ news.title }}
          </router-link>
          <div v-if="news.summary" class="text-caption text-truncate">{{ news.summary }}</div>
          <div class="text-caption text-grey">
            <span>
              <router-link
                v-if="canViewUser(news.author?.pk)"
                :to="{ name: '사용자 - 보기', params: { userId: news.author?.pk } }"
              >
                {{ news.author?.username }}
              </router-link>
              <span v-else>{{ news.author?.username }}</span>
              이(가)
              <router-link
                :to="{
                  name: '(업무실행내역)',
                  params: { projId: news.project?.slug || route.params.projId },
                  query: { from: news.created.substring(0, 10) },
                }"
              >
                {{ elapsedTime(news.created) }}
              </router-link>
              에 추가함
            </span>
          </div>
        </div>
      </CCardText>
    </CCardBody>

    <CCardText class="mx-3 mb-2 form-text">
      <router-link :to="{ name: '(공지)', params: { projId: route.params.projId } }">
        모든 공지
      </router-link>
    </CCardText>
  </CCard>
</template>
