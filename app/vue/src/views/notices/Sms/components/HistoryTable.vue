<script lang="ts" setup>
import { ref, computed } from 'vue'

// Props
interface Props {
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

// Emits
const emit = defineEmits<{
  detail: [item: HistoryItem]
  pageChange: [page: number]
}>()

// 히스토리 아이템 타입
interface HistoryItem {
  requestNo: string
  sendDate: string
  phone: string
  msgType: 'SMS' | 'LMS' | 'MMS' | 'KAKAO'
  status: string
  statusMessage: string
  message: string
}

// 더미 데이터 (실제로는 props로 받거나 store에서 가져옴)
const historyList = ref<HistoryItem[]>([
  {
    requestNo: '20250103001',
    sendDate: '2025-01-03 14:30:25',
    phone: '010-1234-5678',
    msgType: 'SMS',
    status: '01',
    statusMessage: '전송 성공',
    message: '[테스트] 안녕하세요. 발송 테스트입니다.',
  },
  {
    requestNo: '20250103002',
    sendDate: '2025-01-03 15:45:12',
    phone: '010-9876-5432',
    msgType: 'LMS',
    status: '01',
    statusMessage: '전송 성공',
    message: '[공지] 긴 메시지 테스트입니다. 이 메시지는 LMS로 발송되었습니다.',
  },
  {
    requestNo: '20250103003',
    sendDate: '2025-01-03 16:20:45',
    phone: '010-5555-6666',
    msgType: 'KAKAO',
    status: '200',
    statusMessage: '발송 성공',
    message: '[알림] 카카오 알림톡 테스트입니다.',
  },
])

// 페이지네이션
const currentPage = ref(1)
const pageSize = ref(15)
const totalCount = ref(100)

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))

// 페이지 변경
const handlePageChange = (page: number) => {
  currentPage.value = page
  emit('pageChange', page)
}

// 상세보기
const handleDetail = (item: HistoryItem) => {
  emit('detail', item)
}

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

// 상태 뱃지 색상
const getStatusColor = (status: string) => {
  if (status === '01' || status === '200') return 'success'
  return 'danger'
}

// 메시지 요약 (30자)
const getSummary = (message: string) => {
  return message.length > 30 ? message.substring(0, 30) + '...' : message
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
              수신번호
            </CTableHeaderCell>
            <CTableHeaderCell scope="col" class="text-center" style="width: 80px">
              타입
            </CTableHeaderCell>
            <CTableHeaderCell scope="col" class="text-center" style="width: 100px">
              상태
            </CTableHeaderCell>
            <CTableHeaderCell scope="col">메시지</CTableHeaderCell>
            <CTableHeaderCell scope="col" class="text-center" style="width: 80px">
              상세
            </CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <!-- 로딩 중 -->
          <CTableRow v-if="loading">
            <CTableDataCell colspan="6" class="text-center py-5">
              <CSpinner color="primary" />
              <div class="mt-2 text-medium-emphasis">데이터를 불러오는 중...</div>
            </CTableDataCell>
          </CTableRow>

          <!-- 데이터 없음 -->
          <CTableRow v-else-if="historyList.length === 0">
            <CTableDataCell colspan="6" class="text-center py-5">
              <div class="text-medium-emphasis">조회된 내역이 없습니다.</div>
            </CTableDataCell>
          </CTableRow>

          <!-- 데이터 목록 -->
          <CTableRow v-else v-for="item in historyList" :key="item.requestNo">
            <CTableDataCell class="text-center">
              {{ item.sendDate }}
            </CTableDataCell>
            <CTableDataCell class="text-center">
              {{ item.phone }}
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <CBadge :color="getTypeColor(item.msgType)">
                {{ item.msgType }}
              </CBadge>
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <CBadge :color="getStatusColor(item.status)">
                {{ item.statusMessage }}
              </CBadge>
            </CTableDataCell>
            <CTableDataCell>
              {{ getSummary(item.message) }}
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <CButton
                color="info"
                variant="outline"
                size="sm"
                @click="handleDetail(item)"
              >
                <CIcon name="cilZoom" />
              </CButton>
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
