<script setup lang="ts">
import { ref, computed, onBeforeMount } from 'vue'
import api from '@/api'
import { cutString, timeFormat } from '@/utils/baseMixins'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const activeTab = ref(1)
const loading = ref(true)

const generalDocs = ref<any[]>([])
const lawsuitDocs = ref<any[]>([])

const currentDocsList = computed(() => {
  return activeTab.value === 1 ? generalDocs.value : lawsuitDocs.value
})

const fetchData = async () => {
  loading.value = true
  try {
    const [res1, res2] = await Promise.all([
      api.get('/docs/?limit=5&doc_type=1'),
      api.get('/docs/?limit=5&doc_type=2'),
    ])
    generalDocs.value = res1.data.results || []
    lawsuitDocs.value = res2.data.results || []
  } catch (error) {
    console.error('Failed to fetch documents for widget:', error)
  } finally {
    loading.value = false
  }
}

onBeforeMount(() => {
  fetchData()
})
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable @refresh="fetchData">
    <div class="document-list-widget">
      <!-- 탭 선택기 -->
      <v-tabs v-model="activeTab" density="compact" color="primary" class="border-bottom mb-2">
        <v-tab :value="1" class="text-body-2 font-weight-bold">일반문서</v-tab>
        <v-tab :value="2" class="text-body-2 font-weight-bold">소송기록</v-tab>
      </v-tabs>

      <v-progress-linear v-if="loading" indeterminate color="primary" />

      <v-table v-else density="compact" hover>
        <thead>
          <tr>
            <th class="text-left" style="width: 100px">분류</th>
            <th class="text-left">문서 제목</th>
            <th class="text-center" style="width: 100px">등록일</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="item in currentDocsList" :key="item.pk ?? 0">
            <tr>
              <td class="truncate">
                <v-chip
                  size="x-small"
                  :color="item.cate_color || 'primary'"
                  variant="tonal"
                  class="text-caption font-weight-medium"
                >
                  {{ item.cate_name || '일반' }}
                </v-chip>
              </td>
              <td class="truncate">
                <span class="text-caption text-grey mr-1" v-if="item.proj_name">
                  [{{ item.proj_name }}]
                </span>
                <router-link
                  :to="{
                    name: activeTab === 1 ? '본사 일반 문서 - 보기' : '본사 소송 문서 - 보기',
                    params: { docsId: item.pk },
                  }"
                  class="text-body-2"
                >
                  {{ cutString(item.title, 40) }}
                </router-link>
              </td>
              <td class="text-right text-medium-emphasis truncate">
                {{ timeFormat(item.created ?? '').substring(0, 10) }}
              </td>
            </tr>
          </template>
          <tr v-if="!currentDocsList.length">
            <td colspan="3" class="text-center text-medium-emphasis py-4">
              등록된 문서가 없습니다.
            </td>
          </tr>
        </tbody>
      </v-table>

      <v-btn variant="text" color="primary" size="small" class="mt-2" block :to="{ name: '문서' }">
        전체 문서 보기
        <v-icon icon="mdi-chevron-right" size="small" />
      </v-btn>
    </div>
  </WidgetWrapper>
</template>

<style scoped lang="scss">
.document-list-widget {
  height: 100%;
  overflow-y: auto;
}

.document-list-widget :deep(.v-table) {
  background: transparent;
}

.border-bottom {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}
</style>
