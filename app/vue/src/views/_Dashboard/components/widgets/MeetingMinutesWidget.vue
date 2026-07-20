<script setup lang="ts">
import { ref, computed, onBeforeMount } from 'vue'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import { cutString } from '@/utils/baseMixins.ts'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const meetingStore = useMeeting()
const meetingList = computed(() => meetingStore.meetingList)

const loading = ref(true)

const fetchData = async () => {
  loading.value = true
  await meetingStore.fetchMeetingList({})
  loading.value = false
}

onBeforeMount(() => {
  fetchData()
})
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable @refresh="fetchData">
    <div class="meeting-minutes-widget">
      <!-- 로딩 시 스켈레톤 행 표시 (UX 향상) -->
      <div v-if="loading" class="pa-2">
        <v-skeleton-loader type="table-row-divider, table-row, table-row" bg-color="transparent" />
      </div>

      <template v-else>
        <v-table density="compact" hover>
          <thead>
            <tr>
              <th class="text-left project-col">프로젝트</th>
              <th class="text-left">제목</th>
              <th class="text-right date-col">날짜</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in meetingList.slice(0, 5)" :key="item.pk ?? 0">
              <td>
                <router-link
                  v-if="item.project_desc"
                  :to="{ name: '(회의)', params: { projId: item.project_desc?.slug } }"
                  class="text-body-2 text-decoration-none"
                >
                  {{ item.project_desc?.name }}
                </router-link>
              </td>
              <td>
                <router-link
                  :to="{
                    name: '(회의) - 보기',
                    params: { projId: item.project_desc?.slug, meetingId: item.pk },
                  }"
                  class="text-body-2 text-decoration-none text-truncate d-inline-block"
                  style="max-width: 250px"
                >
                  {{ cutString(item.title, 40) }}
                </router-link>
              </td>
              <td class="text-right text-medium-emphasis">
                {{ (item.meeting_date || '').substring(0, 10) }}
              </td>
            </tr>
            <tr v-if="!meetingList.length">
              <td colspan="3" class="text-center text-medium-emphasis py-4">회의록이 없습니다.</td>
            </tr>
          </tbody>
        </v-table>

        <v-btn
          variant="text"
          color="primary"
          size="small"
          class="mt-2"
          block
          :to="{ name: '회의' }"
        >
          전체 회의록 보기
          <v-icon icon="mdi-chevron-right" size="small" />
        </v-btn>
      </template>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.meeting-minutes-widget {
  height: 100%;
  overflow-y: auto;
}

.meeting-minutes-widget :deep(.v-table) {
  background: transparent;
  table-layout: fixed;
  width: 100%;
}

/* Column width settings */
.project-col {
  width: 140px;
}

.date-col {
  width: 90px;
}

/* Ensure links truncate correctly on small screens */
.meeting-minutes-widget :deep(td) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 0; /* Important for table-layout: fixed text-truncation */
}

.meeting-minutes-widget :deep(td a) {
  display: block;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 600px) {
  .project-col {
    width: 90px;
  }
  .date-col {
    width: 80px;
  }
}
</style>
