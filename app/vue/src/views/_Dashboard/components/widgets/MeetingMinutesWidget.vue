<script setup lang="ts">
import { ref, computed, onBeforeMount } from 'vue'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import { cutString, timeFormat } from '@/utils/baseMixins.ts'
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
          <tr v-for="item in meetingList.slice(0, 5)" :key="item.pk ?? 0">
            <td>
              <router-link
                v-if="item.project_desc"
                :to="{ name: '(개요)', params: { projId: item.project_desc?.slug } }"
                class="text-body-2"
              >
                {{ item.project_desc?.name }}
              </router-link>
            </td>
            <td>
              <router-link
                :to="{
                  name: '회의 - 보기',
                  params: { meetingId: item.pk },
                }"
                class="text-body-2"
              >
                {{ cutString(item.title, 40) }}
              </router-link>
            </td>
            <td class="text-right text-caption text-medium-emphasis">
              {{ (item.meeting_date || '').substring(0, 10) }}
            </td>
          </tr>
          <tr v-if="!meetingList.length">
            <td colspan="3" class="text-center text-medium-emphasis">회의록이 없습니다.</td>
          </tr>
        </tbody>
      </v-table>

      <v-btn variant="text" color="primary" size="small" class="mt-2" block :to="{ name: '회의' }">
        전체 회의록 보기
        <v-icon icon="mdi-chevron-right" size="small" />
      </v-btn>
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
}
</style>
