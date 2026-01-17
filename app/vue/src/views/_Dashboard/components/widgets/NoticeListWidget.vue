<script setup lang="ts">
import { ref, computed, onBeforeMount } from 'vue'
import { useInform } from '@/store/pinia/work_inform.ts'
import { cutString, timeFormat } from '@/utils/baseMixins.ts'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const infStore = useInform()
const newsList = computed(() => infStore.newsList)

const loading = ref(true)

const fetchData = async () => {
  loading.value = true
  await infStore.fetchNewsList({})
  loading.value = false
}

onBeforeMount(() => {
  fetchData()
})
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable @refresh="fetchData">
    <div class="notice-list-widget">
      <v-progress-linear v-if="loading" indeterminate color="primary" />

      <v-table v-else density="compact" hover>
        <thead>
          <tr>
            <th class="text-left" style="width: 120px">프로젝트</th>
            <th class="text-left">제목</th>
            <th class="text-right" style="width: 100px">날짜</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in newsList.slice(0, 5)" :key="item.pk ?? 0">
            <td>
              <router-link
                v-if="item.project"
                :to="{ name: '(개요)', params: { projId: item.project?.slug } }"
                class="text-body-2"
              >
                {{ item.project?.name }}
              </router-link>
            </td>
            <td>
              <router-link
                :to="{
                  name: '(공지) - 보기',
                  params: { projId: item.project?.slug, newsId: item.pk },
                }"
                class="text-body-2"
              >
                {{ cutString(item.title, 40) }}
              </router-link>
              <CBadge v-if="item.is_new" color="warning" size="sm" class="ml-2">new</CBadge>
              <CBadge v-if="item.comments?.length" color="warning" size="sm" class="ml-1">
                +{{ item.comments.length }}
              </CBadge>
            </td>
            <td class="text-right text-caption text-medium-emphasis">
              {{ timeFormat(item.created ?? '').substring(0, 10) }}
            </td>
          </tr>
          <tr v-if="!newsList.length">
            <td colspan="3" class="text-center text-medium-emphasis">공지사항이 없습니다.</td>
          </tr>
        </tbody>
      </v-table>

      <v-btn variant="text" color="primary" size="small" class="mt-2" block :to="{ name: '공지' }">
        전체 공지 보기
        <v-icon icon="mdi-chevron-right" size="small" />
      </v-btn>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.notice-list-widget {
  height: 100%;
  overflow-y: auto;
}

.notice-list-widget :deep(.v-table) {
  background: transparent;
}
</style>
