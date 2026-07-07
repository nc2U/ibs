<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useWork } from '@/store/pinia/work_project'
import { useIssue } from '@/store/pinia/work_issue'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const workStore = useWork()
const issueStore = useIssue()
const loading = ref(false)

const projects = computed(() => workStore.visibleProjects)
const myIssues = computed(() => issueStore.issueNumByMember)

const totalProjects = computed(() => projects.value.length)

// 유형별 프로젝트 수
const hqProjects = computed(() => projects.value.filter(p => p.type === '1').length)
const devProjects = computed(() => projects.value.filter(p => p.type === '2').length)
const etcProjects = computed(() => projects.value.filter(p => p.type === '3').length)

// 내 할 일 진행률 계산
const myTaskProgress = computed(() => {
  const total = myIssues.value.all_charged || 0
  if (total === 0) return 0
  return Math.round(((myIssues.value.closed_charged || 0) / total) * 100)
})

const fetchWidgetData = async () => {
  loading.value = true
  try {
    await workStore.fetchVisibleProjectsList({ status: '1' })
    await issueStore.fetchIssueByMember()
  } catch (error) {
    console.error('Failed to fetch project status widget data:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchWidgetData)
</script>

<template>
  <WidgetWrapper
    :widget-id="widgetId"
    :title="title"
    :icon="icon"
    refreshable
    @refresh="fetchWidgetData"
  >
    <div class="project-status-widget d-flex flex-column h-100">
      <!-- 상단 요약 (3:9 가로 분할 배정) -->
      <v-row no-gutters class="align-center mb-2">
        <v-col cols="3" class="text-center pr-2">
          <div class="d-flex flex-column justify-center align-center">
            <div class="text-h4 font-weight-bold text-primary" style="line-height: 1.1">
              {{ totalProjects }}
            </div>
            <div class="text-caption text-medium-emphasis" style="font-size: 10px !important">
              전체 프로젝트
            </div>
          </div>
        </v-col>
        <v-col cols="9" class="pr-2">
          <v-row dense>
            <v-col cols="4">
              <v-card variant="tonal" color="primary" class="text-center py-3 px-1">
                <div class="text-body-2 font-weight-bold">{{ hqProjects }}</div>
                <div style="font-size: 0.9em; line-height: 1" class="text-medium-emphasis">
                  본사관리
                </div>
              </v-card>
            </v-col>
            <v-col cols="4">
              <v-card variant="tonal" color="green-darken-3" class="text-center py-3 px-1">
                <div class="text-body-2 font-weight-bold">{{ devProjects }}</div>
                <div style="font-size: 0.9em; line-height: 1" class="text-medium-emphasis">
                  부동산개발
                </div>
              </v-card>
            </v-col>
            <v-col cols="4">
              <v-card variant="tonal" color="purple-lighten-2" class="text-center py-3 px-1">
                <div class="text-body-2 font-weight-bold">{{ etcProjects }}</div>
                <div style="font-size: 0.9em; line-height: 1" class="text-medium-emphasis">
                  기타
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-col>
      </v-row>

      <v-divider class="my-1" />

      <!-- 내 담당 업무 진행 상황 -->
      <div class="my-tasks-status mb-2">
        <div class="d-flex align-center justify-space-between mb-1">
          <span class="text-caption font-weight-medium">내 담당 업무 해결률</span>
          <span class="text-caption font-weight-bold text-primary">
            {{ myIssues.closed_charged }} / {{ myIssues.all_charged }} 건 ({{ myTaskProgress }}%)
          </span>
        </div>
        <v-progress-linear
          :model-value="myTaskProgress"
          color="primary"
          height="6"
          rounded
          striped
        />
      </div>

      <v-divider class="my-1" />

      <!-- 최근 활성 프로젝트 미니 목록 -->
      <div class="recent-projects flex-grow-1 overflow-y-auto">
        <div class="text-caption text-medium-emphasis mb-2">참여 중인 주요 프로젝트</div>
        <v-list density="compact" class="pa-0 bg-transparent">
          <v-list-item
            v-for="proj in projects.slice(0, 10)"
            :key="proj.pk"
            class="px-2 py-1 mb-1 rounded border border-thin"
          >
            <template #prepend>
              <v-icon
                :icon="
                  proj.type === '1'
                    ? 'mdi-office-building-outline'
                    : proj.type === '2'
                      ? 'mdi-home-city-outline'
                      : 'mdi-folder-open-outline'
                "
                size="small"
                class="mr-2"
                :color="
                  proj.type === '1'
                    ? 'primary'
                    : proj.type === '2'
                      ? 'green-darken-3'
                      : 'purple-lighten-2'
                "
              />
            </template>
            <v-list-item-title class="text-caption font-weight-bold">
              {{ proj.name }}
            </v-list-item-title>
            <template #append>
              <span class="text-caption text-medium-emphasis">
                멤버 {{ proj.all_members?.length || 0 }}명
              </span>
            </template>
          </v-list-item>
        </v-list>
      </div>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.project-status-widget {
  min-height: 280px;
}

.border-thin {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}
</style>
