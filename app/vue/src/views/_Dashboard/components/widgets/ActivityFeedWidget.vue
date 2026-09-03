<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useLogging } from '@/store/pinia/work_logging.ts'
import { useAccount } from '@/store/pinia/account.ts'
import type { ActLogEntry } from '@/store/types/work_logging.ts'
import { elapsedTime } from '@/utils/baseMixins'
import WidgetWrapper from '../WidgetWrapper.vue'
import { useRouter } from 'vue-router'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const router = useRouter()
const logStore = useLogging()
const accountStore = useAccount()

// 'all' = 전체 활동, 'my' = 내 활동만
const filterMode = ref<'all' | 'my'>('all')

const fetchLogs = async () => {
  const params: Record<string, any> = { limit: 5 }
  if (filterMode.value === 'my' && accountStore.userInfo?.pk) {
    params.creator = accountStore.userInfo.pk
  }
  await logStore.fetchActivityLogList(params)
}

onMounted(fetchLogs)

// 필터 토글 시 재조회
watch(filterMode, fetchLogs)

const activityLogs = computed<ActLogEntry[]>(() => logStore.activityLogList || [])

// 행동 텍스트 매핑 (신규 등록 및 상태 변경 구분)
const getActionText = (log: ActLogEntry) => {
  if (log.sort === '1') {
    return log.status_log
      ? `업무 상태를 [${log.status_log}](으)로 변경했습니다`
      : '새 업무를 등록했습니다'
  }
  if (log.sort === '2') return '댓글을 남겼습니다'
  if (log.sort === '3') {
    return log.status_log
      ? `회의록 상태를 [${log.status_log}](으)로 변경했습니다`
      : '회의록을 작성했습니다'
  }
  if (log.sort === '4') return '공지를 등록했습니다'
  if (log.sort === '5') return '문서를 등록했습니다'
  if (log.sort === '6') return '게시글을 작성했습니다'
  return '활동을 수행했습니다'
}

// 대상 텍스트 매핑
const getTargetText = (log: ActLogEntry) => {
  return log.title || log.summary || ''
}

// 아이콘 매핑
const getLogIcon = (log: ActLogEntry) => {
  if (log.sort === '1') return 'mdi-clipboard-text-outline'
  if (log.sort === '2') return 'mdi-comment-text'
  if (log.sort === '3') return 'mdi-calendar-plus'
  if (log.sort === '4') return 'mdi-bullhorn-variant-outline'
  if (log.sort === '5') return 'mdi-file-upload'
  if (log.sort === '6') return 'mdi-forum-outline'
  return 'mdi-bell-outline'
}

// 색상 매핑
const getLogColor = (log: ActLogEntry) => {
  if (log.sort === '2') return 'primary'
  if (log.sort === '1') return 'success'
  if (log.sort === '3') return 'warning'
  if (log.sort === '4') return 'red-lighten-1'
  if (log.sort === '5') return 'info'
  if (log.sort === '6') return 'deep-purple-lighten-2'
  return 'grey'
}

const handleLogClick = (log: ActLogEntry) => {
  if (!log.project?.slug || !log.target_id) return
  if (log.sort === '1') {
    router.push({
      name: '(업무) - 보기',
      params: { projId: log.project.slug, issueId: log.target_id },
    })
  } else if (log.sort === '2') {
    router.push({
      name: '(업무) - 보기',
      params: { projId: log.project.slug, issueId: log.parent_id },
      query: { tap: 2 },
      hash: `#note-${log.target_id}`,
    })
  } else if (log.sort === '3') {
    router.push({
      name: '(회의) - 보기',
      params: { projId: log.project.slug, meetingId: log.target_id },
    })
  } else if (log.sort === '4') {
    router.push({
      name: '(공지) - 보기',
      params: { projId: log.project.slug, newsId: log.target_id },
    })
  } else if (log.sort === '5') {
    router.push({
      name: '(문서) - 보기',
      params: { projId: log.project.slug, docId: log.target_id },
    })
  } else if (log.sort === '6') {
    router.push({
      name: '(게시판) - 게시물 보기',
      params: { projId: log.project.slug, forumId: log.parent_id, postId: log.target_id },
    })
  }
}
</script>

<template>
  <WidgetWrapper :widget-id="widgetId" :title="title" :icon="icon" refreshable @refresh="fetchLogs">
    <div class="activity-feed-widget">
      <!-- 상단 내활동/전체활동 필터 토글 -->
      <div class="d-flex align-center justify-space-between mb-3">
        <span class="text-caption text-medium-emphasis">실시간 시스템 활동 피드</span>
        <v-btn-toggle
          v-model="filterMode"
          mandatory
          density="compact"
          color="primary"
          class="activity-toggle rounded-lg"
          variant="outlined"
        >
          <v-btn value="all" size="x-small" class="text-caption font-weight-medium px-2">
            전체 활동
          </v-btn>
          <v-btn value="my" size="x-small" class="text-caption font-weight-medium px-2">
            내 활동만
          </v-btn>
        </v-btn-toggle>
      </div>

      <div
        v-if="activityLogs.length === 0"
        class="d-flex align-center justify-center py-8 text-grey text-caption"
      >
        해당 활동 내역이 없습니다.
      </div>

      <!-- 리스트형 피드 구조 (좁은 위젯 공간에서 v-timeline이 찌그러지는 현상 방지) -->
      <div v-else class="activity-list">
        <div
          v-for="log in activityLogs"
          :key="log.pk"
          class="activity-item-card d-flex align-start pa-3 mb-2 rounded-lg cursor-pointer"
          @click="handleLogClick(log)"
        >
          <!-- 좌측 원형 아이콘 -->
          <v-avatar
            :color="getLogColor(log)"
            size="30"
            class="mr-3 flex-shrink-0 text-white elevation-1"
          >
            <v-icon :icon="getLogIcon(log)" size="16" />
          </v-avatar>

          <!-- 우측 상세 정보 -->
          <div class="flex-grow-1 min-width-0">
            <div class="d-flex align-center justify-space-between mb-1">
              <div class="text-body-2 text-truncate" style="max-width: 75%">
                <strong>{{ log.creator.username }}</strong>
                &nbsp; -
                <span class="text-medium-emphasis ml-1">{{ getActionText(log) }}</span>
              </div>
              <span class="text-caption text-grey-darken-1 flex-shrink-0">{{
                elapsedTime(log.timestamp)
              }}</span>
            </div>

            <div class="text-caption font-weight-medium text-primary text-truncate mb-1">
              {{ getTargetText(log) }}
            </div>

            <div class="text-caption text-grey-darken-1">
              {{ log.project.name }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </WidgetWrapper>
</template>

<style scoped lang="scss">
.activity-feed-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.activity-toggle {
  height: 24px !important;
  background-color: rgba(var(--v-theme-on-surface), 0.02);

  :deep(.v-btn) {
    height: 24px !important;
    min-width: unset;
  }
}

.activity-list {
  overflow-y: auto;
  flex-grow: 1;
}

.activity-item-card {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  background-color: rgba(var(--v-theme-on-surface), 0.01);
  transition: all 0.2s ease;

  &:hover {
    background-color: rgba(var(--v-theme-on-surface), 0.04);
    border-color: rgba(var(--v-theme-on-surface), 0.1);
  }
}

body.dark-theme {
  .activity-item-card {
    border-color: rgba(255, 255, 255, 0.06);
    background-color: rgba(255, 255, 255, 0.02);

    &:hover {
      background-color: rgba(255, 255, 255, 0.05);
      border-color: rgba(255, 255, 255, 0.08);
    }
  }

  .activity-toggle {
    :deep(.v-btn) {
      color: rgba(255, 255, 255, 0.8) !important;
      &.v-btn--selected {
        color: rgb(var(--v-theme-primary)) !important;
      }
    }
  }
}

.text-truncate-custom {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal;
}
</style>
