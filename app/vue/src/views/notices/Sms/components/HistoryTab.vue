<script lang="ts" setup>
import { ref } from 'vue'
import HistoryFilter from './HistoryFilter.vue'
import HistoryTable from './HistoryTable.vue'
import HistoryDetail from './HistoryDetail.vue'

// 히스토리 아이템 타입
interface HistoryItem {
  requestNo: string
  sendDate: string
  phone: string
  callback?: string
  msgType: 'SMS' | 'LMS' | 'MMS' | 'KAKAO'
  status: string
  statusMessage: string
  message: string
}

// 필터 데이터 타입
interface FilterData {
  startDate: string
  endDate: string
  messageType: string
  status: string
  phone: string
}

// 상태
const loading = ref(false)
const detailVisible = ref(false)
const selectedItem = ref<HistoryItem | null>(null)

// 검색 실행
const handleSearch = (filters: FilterData) => {
  console.log('검색 필터:', filters)
  loading.value = true

  // TODO: 실제 API 호출
  // await noticeStore.fetchSendHistory(...)

  setTimeout(() => {
    loading.value = false
  }, 1000)
}

// 필터 초기화
const handleReset = () => {
  console.log('필터 초기화')
  // TODO: 데이터 리셋
}

// 페이지 변경
const handlePageChange = (page: number) => {
  console.log('페이지 변경:', page)
  loading.value = true

  // TODO: 실제 API 호출 (페이지 번호와 함께)

  setTimeout(() => {
    loading.value = false
  }, 500)
}

// 상세보기
const handleDetail = (item: HistoryItem) => {
  selectedItem.value = item
  detailVisible.value = true
}

// 컴포넌트 마운트 시 초기 데이터 로드
const loadInitialData = () => {
  console.log('초기 데이터 로드')
  // TODO: 초기 데이터 로드 (최근 7일)
}

// 초기화
loadInitialData()
</script>

<template>
  <div>
    <!-- 필터 영역 -->
    <HistoryFilter
      @search="handleSearch"
      @reset="handleReset"
    />

    <!-- 테이블 영역 -->
    <HistoryTable
      :loading="loading"
      @detail="handleDetail"
      @page-change="handlePageChange"
    />

    <!-- 상세보기 다이얼로그 -->
    <HistoryDetail
      v-model:visible="detailVisible"
      :item="selectedItem"
    />
  </div>
</template>
