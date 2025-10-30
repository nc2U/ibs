<script lang="ts" setup>
import { ref, onBeforeMount } from 'vue'
import { useNotice } from '@/store/pinia/notice'
import type { MessageSendHistory, HistoryListParams } from '@/store/types/notice'
import HistoryFilter from './HistoryFilter.vue'
import HistoryTable from './HistoryTable.vue'
import HistoryDetail from './HistoryDetail.vue'

// 필터 데이터 타입
interface FilterData {
  startDate: string
  endDate: string
  messageType: string
  senderNumber: string
}

const noticeStore = useNotice()

// 상태
const loading = ref(false)
const detailVisible = ref(false)
const selectedItem = ref<MessageSendHistory | null>(null)
const currentPage = ref(1)
const pageSize = ref(15)

// 현재 필터
const currentFilters = ref<FilterData>({
  startDate: '',
  endDate: '',
  messageType: '',
  senderNumber: '',
})

// 검색 실행
const handleSearch = async (filters: FilterData) => {
  currentFilters.value = { ...filters }
  currentPage.value = 1 // 검색 시 첫 페이지로 리셋
  await loadHistory()
}

// 필터 초기화
const handleReset = async () => {
  currentFilters.value = {
    startDate: '',
    endDate: '',
    messageType: '',
    senderNumber: '',
  }
  currentPage.value = 1
  await loadHistory()
}

// 페이지 변경
const handlePageChange = async (page: number) => {
  currentPage.value = page
  await loadHistory()
}

// 히스토리 로드
const loadHistory = async () => {
  loading.value = true
  try {
    const params: HistoryListParams = {
      page: currentPage.value,
      page_size: pageSize.value,
      ordering: '-created',
    }

    // 필터 적용
    if (currentFilters.value.startDate) {
      params.start_date = currentFilters.value.startDate
    }
    if (currentFilters.value.endDate) {
      params.end_date = currentFilters.value.endDate
    }
    if (currentFilters.value.messageType) {
      params.message_type = currentFilters.value.messageType
    }
    if (currentFilters.value.senderNumber) {
      params.sender_number = currentFilters.value.senderNumber
    }

    await noticeStore.fetchMessageSendHistory(params)
  } catch (error) {
    console.error('히스토리 로드 실패:', error)
  } finally {
    loading.value = false
  }
}

// 상세보기
const handleDetail = async (id: number) => {
  try {
    const detail = await noticeStore.fetchMessageSendHistoryDetail(id)
    selectedItem.value = detail
    detailVisible.value = true
  } catch (error) {
    console.error('상세 조회 실패:', error)
  }
}

// 초기 데이터 로드 (최근 7일)
const loadInitialData = () => {
  const today = new Date()
  const sevenDaysAgo = new Date(today)
  sevenDaysAgo.setDate(today.getDate() - 7)

  currentFilters.value = {
    startDate: sevenDaysAgo.toISOString().split('T')[0],
    endDate: today.toISOString().split('T')[0],
    messageType: '',
    senderNumber: '',
  }

  loadHistory()
}

// 컴포넌트 마운트 시 초기화
onBeforeMount(() => {
  loadInitialData()
})
</script>

<template>
  <div>
    <!-- 필터 영역 -->
    <HistoryFilter @search="handleSearch" @reset="handleReset" />

    <!-- 테이블 영역 -->
    <HistoryTable :loading="loading" @detail="handleDetail" @page-change="handlePageChange" />

    <!-- 상세보기 다이얼로그 -->
    <HistoryDetail v-model:visible="detailVisible" :item="selectedItem" />
  </div>
</template>
