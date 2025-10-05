<script lang="ts" setup>
import { computed } from 'vue'
import { useNotice } from '@/store/pinia/notice'
import { cutString } from '@/utils/baseMixins.ts'
import type { HistoryListResponse, MessageSendHistoryList } from '@/store/types/notice'

// Props
interface Props {
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

// Emits
const emit = defineEmits<{
  detail: [id: number]
  pageChange: [page: number]
}>()

// Store
const noticeStore = useNotice()

// 히스토리 데이터
const historyData = computed<HistoryListResponse>(() => noticeStore.messageSendHistory)
const historyList = computed(() => historyData.value?.results || [])
const totalCount = computed(() => historyData.value?.count || 0)
const currentPage = computed(() => {
  const nextUrl = historyData.value?.next
  const prevUrl = historyData.value?.previous
  if (!nextUrl && !prevUrl) return 1
  // URL에서 page 번호 추출하여 계산
  return 1 // 기본값
})

// 페이지네이션
const pageSize = 15
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize))

// 페이지 변경
const handlePageChange = (page: number) => {
  emit('pageChange', page)
}

// 상세보기
const handleDetail = (item: MessageSendHistoryList) => emit('detail', item.id as any)

// 메시지 타입 뱃지 색상
const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    SMS: 'primary',
    LMS: 'info',
    MMS: 'success',
    KAKAO: 'warning',
  }
  return colors[type] || 'secondary'
}

// 날짜 포맷팅
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}
</script>

<template>
  <CCard>
    <CCardHeader>
      <strong>발송 내역</strong>
      <span class="text-medium-emphasis ms-2">(전체 {{ totalCount }}건)</span>
    </CCardHeader>
    <CCardBody>
      <CTable hover responsive>
        <CTableHead>
          <CTableRow>
            <CTableHeaderCell scope="col" class="text-center" style="width: 150px">
              발송일시
            </CTableHeaderCell>
            <CTableHeaderCell scope="col" class="text-center" style="width: 120px">
              발신번호
            </CTableHeaderCell>
            <CTableHeaderCell scope="col" class="text-center" style="width: 80px">
              타입
            </CTableHeaderCell>
            <CTableHeaderCell scope="col" class="text-center" style="width: 100px">
              수신자 수
            </CTableHeaderCell>
            <CTableHeaderCell scope="col">제목</CTableHeaderCell>
            <CTableHeaderCell scope="col" class="text-center" style="width: 100px">
              발송자
            </CTableHeaderCell>
            <CTableHeaderCell scope="col" class="text-center" style="width: 80px">
              상세
            </CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <!-- 로딩 중 -->
          <CTableRow v-if="loading">
            <CTableDataCell colspan="7" class="text-center py-5">
              <CSpinner color="primary" />
              <div class="mt-2 text-medium-emphasis">데이터를 불러오는 중...</div>
            </CTableDataCell>
          </CTableRow>

          <!-- 데이터 없음 -->
          <CTableRow v-else-if="historyList.length === 0">
            <CTableDataCell colspan="7" class="text-center py-5">
              <div class="text-medium-emphasis">조회된 내역이 없습니다.</div>
            </CTableDataCell>
          </CTableRow>

          <!-- 데이터 목록 -->
          <CTableRow v-else v-for="item in historyList" :key="item.id">
            <CTableDataCell class="text-center">
              {{ formatDate(item.sent_at) }}
            </CTableDataCell>
            <CTableDataCell class="text-center">
              {{ item.sender_number }}
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <CBadge :color="getTypeColor(item.message_type)">
                {{ item.message_type }}
              </CBadge>
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <CBadge color="info"> {{ item.recipient_count }}명 </CBadge>
            </CTableDataCell>
            <CTableDataCell>
              {{ cutString(item.title || '(제목 없음)') }}
            </CTableDataCell>
            <CTableDataCell class="text-center">
              {{ item.sent_by?.username || '-' }}
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <v-btn color="info" size="x-small" @click="handleDetail(item)"> 확인 </v-btn>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>

      <!-- 페이지네이션 -->
      <div v-if="!loading && historyList.length > 0" class="d-flex justify-content-center mt-3">
        <CPagination
          :pages="totalPages"
          :active-page="currentPage"
          @update:active-page="handlePageChange"
        />
      </div>
    </CCardBody>
  </CCard>
</template>
