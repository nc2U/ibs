<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApproval } from '@/store/pinia/approval.ts'
import { cutString, timeFormat } from '@/utils/baseMixins.ts'
import WidgetWrapper from '../WidgetWrapper.vue'
import type { ApprovalDocument } from '@/store/types/approval.ts'

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const router = useRouter()
const approvalStore = useApproval()

const activeTab = ref<'pending' | 'drafted' | 'approved'>('pending')
const loading = ref(false)

const pendingList = computed(() => approvalStore.pendingList || [])
const draftedList = computed(() => approvalStore.draftedList || [])
const approvedList = computed(() => approvalStore.approvedList || [])

const currentList = computed<ApprovalDocument[]>(() => {
  if (activeTab.value === 'pending') return pendingList.value.slice(0, 5)
  if (activeTab.value === 'drafted') return draftedList.value.slice(0, 5)
  return approvedList.value.slice(0, 5)
})

const fetchApprovalData = async () => {
  loading.value = true
  try {
    await Promise.allSettled([
      approvalStore.fetchMyPending(),
      approvalStore.fetchMyDrafted(),
      approvalStore.fetchMyApproved(),
    ])
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchApprovalData()
})

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'pending':
      return { text: '결재 대기', color: 'warning' }
    case 'approved':
      return { text: '승인 완료', color: 'success' }
    case 'rejected':
      return { text: '반려', color: 'error' }
    case 'draft':
      return { text: '임시 저장', color: 'grey' }
    case 'cancelled':
      return { text: '회수/취소', color: 'secondary' }
    default:
      return { text: status, color: 'info' }
  }
}

const handleRowClick = (item: ApprovalDocument) => {
  if (activeTab.value === 'pending') {
    router.push({ name: '결재 대기함 - 보기', params: { docId: item.id } })
  } else if (activeTab.value === 'drafted') {
    router.push({ name: '기안 문서함 - 보기', params: { docId: item.id } })
  } else {
    router.push({ name: '결재 문서함 - 보기', params: { docId: item.id } })
  }
}
</script>

<template>
  <WidgetWrapper
    :widget-id="widgetId"
    :title="title"
    :icon="icon || 'mdi-file-sign'"
    refreshable
    @refresh="fetchApprovalData"
  >
    <div class="approval-status-widget d-flex flex-column h-100">
      <!-- 상단 요약 카운터 배지 바 -->
      <div class="summary-chips d-flex align-center gap-2 mb-2 px-1">
        <v-chip
          size="small"
          :color="pendingList.length ? 'deep-orange' : 'grey-lighten-1'"
          :variant="activeTab === 'pending' ? 'flat' : 'tonal'"
          class="cursor-pointer font-weight-medium"
          @click="activeTab = 'pending'"
        >
          <v-icon icon="mdi-file-clock-outline" size="14" class="mr-1" />
          결재 대기
          <v-badge
            v-if="pendingList.length"
            :content="pendingList.length"
            inline
            color="error"
            class="ml-1"
          />
        </v-chip>

        <v-chip
          size="small"
          color="primary"
          :variant="activeTab === 'drafted' ? 'flat' : 'tonal'"
          class="cursor-pointer font-weight-medium"
          @click="activeTab = 'drafted'"
        >
          <v-icon icon="mdi-file-document-edit-outline" size="14" class="mr-1" />
          내 기안함
          <span v-if="draftedList.length" class="ml-1 font-weight-bold">
            ({{ draftedList.length }})
          </span>
        </v-chip>

        <v-chip
          size="small"
          color="success"
          :variant="activeTab === 'approved' ? 'flat' : 'tonal'"
          class="cursor-pointer font-weight-medium"
          @click="activeTab = 'approved'"
        >
          <v-icon icon="mdi-file-check-outline" size="14" class="mr-1" />
          완료 문서
        </v-chip>
      </div>

      <!-- 로딩 인디케이터 -->
      <v-progress-linear v-if="loading" indeterminate color="primary" class="my-1" />

      <!-- 문서 목록 테이블 -->
      <div class="table-container flex-grow-1 overflow-y-auto">
        <v-table density="compact" hover>
          <thead class="bg-more-light border-top border-bottom">
            <tr>
              <th class="text-left" style="width: 100px">유형</th>
              <th class="text-left">문서 제목</th>
              <th
                v-if="activeTab !== 'drafted'"
                class="text-center"
                style="width: 90px"
              >
                기안자
              </th>
              <th v-else class="text-center" style="width: 90px">상태</th>
              <th class="text-right" style="width: 90px">
                {{ activeTab === 'pending' ? '도착일' : '일시' }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in currentList"
              :key="item.id"
              class="border-bottom cursor-pointer"
              @click="handleRowClick(item)"
            >
              <td class="text-truncate">
                <v-chip
                  size="x-small"
                  variant="tonal"
                  color="indigo-lighten-1"
                  class="font-weight-medium"
                >
                  {{ item.doc_type_name || item.doc_type_detail?.name || '일반' }}
                </v-chip>
              </td>
              <td class="text-truncate">
                <span class="text-body-2 font-weight-medium text-decoration-none">
                  {{ cutString(item.title, 35) }}
                </span>
                <span
                  v-if="item.attachment_count"
                  class="ml-1 text-caption text-medium-emphasis"
                >
                  <v-icon icon="mdi-paperclip" size="12" />
                </span>
              </td>
              <td
                v-if="activeTab !== 'drafted'"
                class="text-center text-truncate text-caption"
              >
                {{ item.drafter?.full_name || item.drafter?.username || '-' }}
              </td>
              <td v-else class="text-center">
                <v-chip
                  size="x-small"
                  :color="getStatusBadge(item.status).color"
                  variant="tonal"
                  class="font-weight-medium"
                >
                  {{ getStatusBadge(item.status).text }}
                </v-chip>
              </td>
              <td class="text-right text-caption text-medium-emphasis text-no-wrap">
                {{ timeFormat(item.submitted_at || item.created_at || '').substring(5, 10) }}
              </td>
            </tr>
            <tr v-if="!currentList.length">
              <td
                colspan="4"
                class="text-center text-medium-emphasis py-4 text-caption"
              >
                {{
                  activeTab === 'pending'
                    ? '결재 대기 중인 문서가 없습니다.'
                    : activeTab === 'drafted'
                      ? '기안한 문서가 없습니다.'
                      : '완료된 문서가 없습니다.'
                }}
              </td>
            </tr>
          </tbody>
        </v-table>
      </div>

      <!-- 하단 바로가기 버튼 액션 -->
      <div class="action-footer d-flex justify-space-between align-center pt-2 mt-auto border-top">
        <v-btn
          variant="tonal"
          color="primary"
          size="small"
          prepend-icon="mdi-pencil-plus"
          :to="{ name: '기안 문서함 - 작성' }"
        >
          기안 작성
        </v-btn>
        <v-btn
          variant="text"
          color="primary"
          size="small"
          append-icon="mdi-chevron-right"
          :to="{
            name:
              activeTab === 'pending'
                ? '결재 대기함'
                : activeTab === 'drafted'
                  ? '기안 문서함'
                  : '결재 문서함',
          }"
        >
          {{
            activeTab === 'pending'
              ? '대기함 전체'
              : activeTab === 'drafted'
                ? '기안함 전체'
                : '문서함 전체'
          }}
        </v-btn>
      </div>
    </div>
  </WidgetWrapper>
</template>

<style scoped>
.approval-status-widget {
  height: 100%;
}

.table-container {
  min-height: 140px;
}

.table-container :deep(.v-table) {
  background: transparent;
  table-layout: fixed;
  width: 100%;
}

.cursor-pointer {
  cursor: pointer;
}

.gap-2 {
  gap: 8px;
}
</style>
