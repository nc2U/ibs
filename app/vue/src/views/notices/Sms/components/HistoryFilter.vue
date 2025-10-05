<script lang="ts" setup>
import { ref } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

// Emits
const emit = defineEmits<{
  search: [filters: FilterData]
  reset: []
}>()

// 필터 데이터 타입
interface FilterData {
  startDate: string
  endDate: string
  messageType: string
  senderNumber: string
}

// 필터 데이터
const filterData = ref<FilterData>({
  startDate: '',
  endDate: '',
  messageType: 'all',
  senderNumber: '',
})

// 메시지 타입 옵션
const messageTypeOptions = [
  { label: '전체', value: 'all' },
  { label: 'SMS', value: 'SMS' },
  { label: 'LMS', value: 'LMS' },
  { label: 'MMS', value: 'MMS' },
  { label: '카카오', value: 'KAKAO' },
]

// 검색 실행
const handleSearch = () => {
  emit('search', filterData.value)
}

// 필터 초기화
const handleReset = () => {
  filterData.value = {
    startDate: '',
    endDate: '',
    messageType: 'all',
    senderNumber: '',
  }
  emit('reset')
}

// 초기 날짜 설정 (최근 7일)
const initDates = () => {
  const today = new Date()
  const weekAgo = new Date(today)
  weekAgo.setDate(weekAgo.getDate() - 7)

  filterData.value.endDate = today.toISOString().split('T')[0]
  filterData.value.startDate = weekAgo.toISOString().split('T')[0]
}

// 컴포넌트 마운트 시 초기 날짜 설정
initDates()
</script>

<template>
  <CCard class="mb-3">
    <CCardHeader>
      <strong>검색 필터</strong>
    </CCardHeader>
    <CCardBody>
      <CRow class="g-3">
        <!-- 날짜 범위 -->
        <CCol :md="12" lg="4">
          <CFormLabel>기간</CFormLabel>
          <CRow class="g-2">
            <CCol :md="6">
              <DatePicker v-model="filterData.startDate" type="date" placeholder="시작일" />
            </CCol>
            <CCol :md="6">
              <DatePicker v-model="filterData.endDate" type="date" placeholder="종료일" />
            </CCol>
          </CRow>
          <!--          <CFormText class="text-medium-emphasis"> 최대 90일까지 조회 가능합니다. </CFormText>-->
        </CCol>

        <!-- 메시지 타입 -->
        <CCol :md="6" lg="3">
          <CFormLabel>메시지 타입</CFormLabel>
          <CFormSelect v-model="filterData.messageType">
            <option v-for="option in messageTypeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </CFormSelect>
        </CCol>

        <!-- 발신번호 검색 -->
        <CCol :md="6" lg="3">
          <CFormLabel>발신번호</CFormLabel>
          <CFormInput v-model="filterData.senderNumber" type="text" placeholder="발신번호 입력" />
        </CCol>

        <!-- 버튼 -->
        <CCol :md="6" lg="2" class="d-flex align-items-end">
          <CButton color="primary" class="me-2" @click="handleSearch">
            <CIcon name="cilSearch" class="me-1" />
            검색
          </CButton>
          <CButton color="secondary" variant="outline" @click="handleReset">
            <CIcon name="cilReload" class="me-1" />
            초기화
          </CButton>
        </CCol>
      </CRow>
    </CCardBody>
  </CCard>
</template>
