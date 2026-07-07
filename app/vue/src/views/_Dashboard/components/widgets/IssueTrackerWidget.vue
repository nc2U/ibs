<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useIssue } from '@/store/pinia/work_issue'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const issueStore = useIssue()
const isLoading = ref(false)

// 최근 등록된 이슈 5개 추출 (전체 목록에서 최신순 정렬)
const recentIssues = computed(() => {
  return [...issueStore.allIssueList].sort((a, b) => b.pk - a.pk).slice(0, 5)
})

// 상태별 실시간 집계 계산
const issueStats = computed(() => {
  const list = issueStore.allIssueList
  const stats = {
    new: 0,
    progress: 0,
    resolved: 0,
    reserved: 0,
  }

  list.forEach(issue => {
    const statusName = issue.status?.name || ''
    if (statusName.includes('준비')) {
      stats.new++
    } else if (statusName.includes('진행') || statusName.includes('검토')) {
      stats.progress++
    } else if (statusName.includes('보류')) {
      stats.reserved++
    } else if (statusName.includes('완료') || statusName.includes('취소')) {
      stats.resolved++
    } else {
      // 그 외 기본값 매핑
      if (issue.status?.closed) {
        stats.resolved++
      } else {
        stats.progress++
      }
    }
  })

  return stats
})

const issueCategories = computed(() => [
  { label: '준비', value: issueStats.value.new, color: 'info', icon: 'mdi-alert-circle-outline' },
  {
    label: '진행중',
    value: issueStats.value.progress,
    color: 'primary',
    icon: 'mdi-progress-clock',
  },
  {
    label: '보류',
    value: issueStats.value.reserved,
    color: 'grey-darken-1',
    icon: 'mdi-access-point-off',
  },
  {
    label: '해결됨',
    value: issueStats.value.resolved,
    color: 'success',
    icon: 'mdi-checkbox-marked-circle-outline',
  },
])

const fetchTrackerData = async () => {
  try {
    isLoading.value = true
    // 프로젝트 전체 혹은 스코프 무관하게 전체 미완료/종료 이슈를 로드
    // closed 파라미터를 빈 문자열이나 생략하여 모든 상태를 로드할 수 있도록 빈 값 설정
    await issueStore.fetchAllIssueList('', '') // 모든 이슈 로드
  } catch (error) {
    console.error('이슈 트래커 데이터 로드 실패:', error)
  } finally {
    isLoading.value = false
  }
}

// 우선순위별 칩 컬러 매핑
const getPriorityColor = (priorityName: string | undefined) => {
  if (!priorityName) return 'grey'
  if (priorityName.includes('낮음')) return 'blue-grey'
  if (priorityName.includes('보통')) return 'blue'
  if (priorityName.includes('높음')) return 'orange'
  if (priorityName.includes('긴급')) return 'deep-orange'
  if (priorityName.includes('즉시')) return 'red'
  return 'success'
}

onMounted(() => {
  fetchTrackerData()
})
</script>

<template>
  <WidgetWrapper
    :widget-id="widgetId"
    :title="title"
    :icon="icon"
    refreshable
    @refresh="fetchTrackerData"
  >
    <div class="issue-tracker-widget d-flex flex-column h-100">
      <!-- 로딩 바 -->
      <div v-if="isLoading" class="d-flex justify-center align-center py-10 my-auto">
        <v-progress-circular indeterminate color="primary" size="32" />
      </div>

      <template v-else>
        <!-- 상단 카드 섹션: 상태별 집계 -->
        <v-row dense align="start" class="mb-4" style="flex: 0 0 auto">
          <v-col v-for="cat in issueCategories" :key="cat.label" cols="3" class="py-0">
            <v-card variant="tonal" :color="cat.color" class="text-center py-2 rounded-lg">
              <v-icon :icon="cat.icon" size="small" class="mb-1 opacity-70" />
              <div class="text-h5 font-weight-bold tracking-tight">
                {{ cat.value }}
              </div>
              <div class="text-caption font-weight-medium opacity-80 mt-n1">
                {{ cat.label }}
              </div>
            </v-card>
          </v-col>
        </v-row>

        <v-divider class="mb-3" />

        <!-- 하단 섹션: 최근 이슈 요약 -->
        <div class="d-flex align-center justify-space-between mb-2">
          <span class="text-subtitle-2 font-weight-bold text-medium-emphasis">최근 업무 현황</span>
          <v-btn variant="text" color="primary" size="small" class="px-1" :to="{ name: '업무' }">
            전체 보기
            <v-icon icon="mdi-chevron-right" />
          </v-btn>
        </div>

        <div
          v-if="recentIssues.length === 0"
          class="d-flex flex-column align-center justify-center py-5 text-grey"
        >
          <v-icon icon="mdi-tray-blank" size="large" class="mb-1" />
          <span class="text-caption">최근 생성된 이슈가 없습니다.</span>
        </div>

        <v-list v-else density="compact" class="pa-0 bg-transparent flex-grow-1 overflow-y-auto">
          <v-list-item
            v-for="issue in recentIssues"
            :key="issue.pk"
            class="mb-2 rounded-lg list-item pa-2 border-all"
            variant="flat"
            :to="{
              name: '(업무) - 보기',
              params: { projId: issue.project?.slug, issueId: issue.pk },
            }"
          >
            <template #prepend>
              <!-- 우선순위 마커 칩 -->
              <v-chip
                :color="getPriorityColor(issue.priority?.name)"
                size="x-small"
                variant="flat"
                class="mr-2 font-weight-bold"
              >
                {{ issue.priority?.name || '보통' }}
              </v-chip>
            </template>

            <v-list-item-title class="text-body-2 font-weight-medium pr-1 text-truncate">
              <span class="text-grey font-weight-bold text-caption mr-1">#{{ issue.pk }}</span>
              {{ issue.subject }}

              <span class="ml-2 text-caption text-grey align-center">
                <v-chip size="x-small" variant="outlined" color="primary" class="mr-2 py-0">
                  {{ issue.tracker?.name }}
                </v-chip>
                <span class="text-truncate mr-2" style="max-width: 100px">
                  {{ issue.project?.name }}
                </span>
                <span class="text-grey-lighten-1 mr-2">•</span>
                <span class="text-truncate">작성 : {{ issue.creator?.username }}</span>
              </span>
            </v-list-item-title>

            <!--            <v-list-item-subtitle class="text-caption text-grey mt-1 align-center">-->
            <!--              <v-chip size="x-small" variant="outlined" color="primary" class="mr-2 py-0">-->
            <!--                {{ issue.tracker?.name }}-->
            <!--              </v-chip>-->
            <!--              <span class="text-truncate mr-2" style="max-width: 100px">-->
            <!--                {{ issue.project?.name }}-->
            <!--              </span>-->
            <!--              <span class="text-grey-lighten-1 mr-2">•</span>-->
            <!--              <span class="text-truncate">작성: {{ issue.creator?.username }}</span>-->
            <!--            </v-list-item-subtitle>-->

            <template #append>
              <!-- 담당자 정보 표시 -->
              <span v-if="issue.assigned_to" class="text-muted text-caption">
                담당 : {{ issue.assigned_to.username }}
              </span>
              <v-icon v-else icon="mdi-account-question-outline" size="x-small" color="grey" />
              <!--              <v-tooltip-->
              <!--                :text="-->
              <!--                  issue.assigned_to ? `담당자: ${issue.assigned_to.username}` : '담당자 미지정'-->
              <!--                "-->
              <!--                location="top"-->
              <!--              >-->
              <!--                <template #activator="{ props }">-->
              <!--                  <v-avatar-->
              <!--                    v-bind="props"-->
              <!--                    size="24"-->
              <!--                    :color="issue.assigned_to ? 'primary' : 'grey-lighten-2'"-->
              <!--                    class="text-caption font-weight-bold"-->
              <!--                  >-->
              <!--                    <span v-if="issue.assigned_to" class="text-white">-->
              <!--                      {{ issue.assigned_to.username.substring(0, 1) }}-->
              <!--                    </span>-->
              <!--                    <v-icon-->
              <!--                      v-else-->
              <!--                      icon="mdi-account-question-outline"-->
              <!--                      size="x-small"-->
              <!--                      color="grey"-->
              <!--                    />-->
              <!--                  </v-avatar>-->
              <!--                </template>-->
              <!--              </v-tooltip>-->
            </template>
          </v-list-item>
        </v-list>
      </template>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.issue-tracker-widget {
  min-height: 280px;
}

.list-item {
  background-color: rgb(var(--v-theme-surface));
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  cursor: pointer;
}

.border-all {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06) !important;
}

.list-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border-color: rgba(var(--v-theme-primary), 0.2) !important;
}

.tracking-tight {
  letter-spacing: -0.05em;
}

.opacity-70 {
  opacity: 0.7;
}

.opacity-80 {
  opacity: 0.8;
}
</style>
