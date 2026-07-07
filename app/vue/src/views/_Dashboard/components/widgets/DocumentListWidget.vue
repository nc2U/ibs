<script setup lang="ts">
import { ref, computed, onBeforeMount } from 'vue'
import { useDocs } from '@/store/pinia/docs'
import { cutString, timeFormat } from '@/utils/baseMixins'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const docsStore = useDocs()
const docsList = computed(() => docsStore.docsList)

const loading = ref(true)

const fetchData = async () => {
  loading.value = true
  await docsStore.fetchDocsList({ limit: 5 })
  loading.value = false
}

onBeforeMount(() => {
  fetchData()
})
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable @refresh="fetchData">
    <div class="document-list-widget">
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
          <template v-for="item in docsList.slice(0, 5)" :key="item.pk ?? 0">
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
                <router-link
                  :to="{
                    name: '본사 일반 문서 - 보기',
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
          <tr v-if="!docsList.length">
            <td colspan="3" class="text-center text-medium-emphasis">등록된 문서가 없습니다.</td>
          </tr>
        </tbody>
      </v-table>

      <v-btn variant="text" color="primary" size="small" class="mt-2" block :to="{ name: '본사 일반 문서' }">
        전체 문서 보기
        <v-icon icon="mdi-chevron-right" size="small" />
      </v-btn>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.document-list-widget {
  height: 100%;
  overflow-y: auto;
}

.document-list-widget :deep(.v-table) {
  background: transparent;
}
</style>
