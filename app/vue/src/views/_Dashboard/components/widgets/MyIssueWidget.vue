<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { useIssue } from '@/store/pinia/work_issue'
import WidgetWrapper from '../WidgetWrapper.vue'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const accountStore = useAccount()
const issueStore = useIssue()

const isLoading = ref(false)

// 로그인한 사용자 정보
const userInfo = computed(() => accountStore.userInfo)

// 내 미완료 업무 목록 (최대 5개 표시)
const myIssues = computed(() => issueStore.issueList.slice(0, 5))

const fetchMyIssues = async () => {
  if (!userInfo.value?.pk) return
  try {
    isLoading.value = true
    await issueStore.fetchIssueList({
      assignee: userInfo.value.pk,
      status__closed: '0', // 미완료 업무
      page: 1,
    })
  } catch (error) {
    console.error('내 업무 목록 로드 실패:', error)
  } finally {
    isLoading.value = false
  }
}

// 상태 텍스트 매핑 색상
const getStatusColor = (statusName: string | undefined) => {
  if (!statusName) return 'secondary'
  if (statusName.includes('준비')) return 'info'
  if (statusName.includes('진행')) return 'primary'
  if (statusName.includes('검토')) return 'danger'
  if (statusName.includes('보류')) return 'warning'
  return 'success'
}

// 우선순위 텍스트 매핑 색상
const getPriorityColor = (priorityName: string | undefined) => {
  if (!priorityName) return 'grey'
  if (priorityName.includes('낮음')) return 'info'
  if (priorityName.includes('보통')) return 'primary'
  if (priorityName.includes('높음')) return 'warning'
  if (priorityName.includes('긴급')) return 'danger'
  if (priorityName.includes('즉시')) return 'error'
  return 'success'
}

onMounted(() => {
  fetchMyIssues()
})
</script>

<template>
  <WidgetWrapper
    :widget-id="widgetId"
    :title="title"
    :icon="icon"
    refreshable
    @refresh="fetchMyIssues"
  >
    <div class="my-issue-widget">
      <!-- 로딩 인디케이터 -->
      <div v-if="isLoading" class="d-flex justify-center align-center h-100 py-5">
        <v-progress-circular indeterminate color="primary" size="24" />
      </div>

      <!-- 데이터 없음 -->
      <div
        v-else-if="myIssues.length === 0"
        class="d-flex flex-column justify-center align-center h-100 text-grey py-5"
      >
        <v-icon icon="mdi-checkbox-marked-circle-outline" size="large" class="mb-2" />
        <div class="text-caption">진행 중인 내 업무가 없습니다.</div>

        <v-btn
          variant="text"
          color="primary"
          size="small"
          class="mt-2"
          block
          :to="{ name: '업무' }"
        >
          업무 생성하기
          <v-icon icon="mdi-chevron-right" size="small" />
        </v-btn>
      </div>

      <!-- 업무 목록 테이블 -->
      <template v-else>
        <v-table density="compact" hover>
          <thead>
            <tr>
              <th class="text-left">프로젝트</th>
              <th class="text-left">제목</th>
              <th class="text-center" style="width: 120px">상태</th>
              <th class="text-center" style="width: 120px">우선순위</th>
              <th class="text-center" style="width: 150px">기한</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="issue in myIssues" :key="issue.pk">
              <td>
                <div class="text-truncate" style="max-width: 150px">
                  <router-link :to="{ name: '(업무)', params: { projId: issue.project?.slug } }">
                    {{ issue.project?.name }}
                  </router-link>
                </div>
              </td>
              <td>
                <div class="text-body-2 text-truncate">
                  <router-link
                    :to="{
                      name: '(업무) - 보기',
                      params: { projId: issue.project?.slug, issueId: issue.pk },
                    }"
                  >
                    {{ issue.subject }}
                  </router-link>
                </div>
              </td>
              <td class="text-center">
                <v-chip
                  :color="getStatusColor(issue.status?.name)"
                  size="x-small"
                  variant="tonal"
                  class="font-weight-medium"
                >
                  {{ issue.status?.name }}
                </v-chip>
              </td>
              <td class="text-center">
                <v-chip
                  :color="getPriorityColor(issue.priority?.name)"
                  size="x-small"
                  variant="outlined"
                  class="font-weight-medium"
                >
                  {{ issue.priority?.name }}
                </v-chip>
              </td>
              <td class="text-center text-no-wrap">
                {{ issue.due_date || '-' }}
              </td>
            </tr>
          </tbody>
        </v-table>

        <v-btn
          variant="text"
          color="primary"
          size="small"
          class="mt-2"
          block
          :to="{ name: '업무' }"
        >
          전체 업무 보기
          <v-icon icon="mdi-chevron-right" size="small" />
        </v-btn>
      </template>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.my-issue-widget {
  height: 100%;
  overflow-y: auto;
}

.my-issue-widget :deep(.v-table) {
  background: transparent;
}
</style>
