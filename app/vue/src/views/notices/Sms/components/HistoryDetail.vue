<script lang="ts" setup>
import { computed } from 'vue'
import type { MessageSendHistory } from '@/store/types/notice'

// Props
interface Props {
  visible: boolean
  item: MessageSendHistory | null
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

// 모달 닫기
const handleClose = () => {
  emit('update:visible', false)
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

// 메시지 타입 뱃지 색상
const getTypeColor = computed(() => {
  if (!props.item) return 'secondary'
  const colors: Record<string, string> = {
    SMS: 'primary',
    LMS: 'info',
    MMS: 'success',
    KAKAO: 'warning',
  }
  return colors[props.item.message_type] || 'secondary'
})
</script>

<template>
  <CModal :visible="visible" @close="handleClose" size="lg" backdrop="static" alignment="center">
    <CModalHeader>
      <CModalTitle>발송 상세 내역</CModalTitle>
    </CModalHeader>
    <CModalBody v-if="item">
      <CRow class="mb-3">
        <CCol :md="6">
          <div class="mb-3">
            <strong class="text-medium-emphasis">요청번호</strong>
            <div class="mt-1">{{ item.request_no }}</div>
          </div>
        </CCol>
        <CCol :md="6">
          <div class="mb-3">
            <strong class="text-medium-emphasis">발송일시</strong>
            <div class="mt-1">{{ formatDate(item.sent_at) }}</div>
          </div>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CCol :md="6">
          <div class="mb-3">
            <strong class="text-medium-emphasis">발신번호</strong>
            <div class="mt-1">{{ item.sender_number }}</div>
          </div>
        </CCol>
        <CCol :md="6">
          <div class="mb-3">
            <strong class="text-medium-emphasis">수신자 수</strong>
            <div class="mt-1">
              <CBadge color="info" size="lg"> {{ item.recipient_count }}명 </CBadge>
            </div>
          </div>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CCol :md="6">
          <div class="mb-3">
            <strong class="text-medium-emphasis">메시지 타입</strong>
            <div class="mt-1">
              <CBadge :color="getTypeColor" size="lg">
                {{ item.message_type }}
              </CBadge>
            </div>
          </div>
        </CCol>
        <CCol :md="6">
          <div class="mb-3">
            <strong class="text-medium-emphasis">발송자</strong>
            <div class="mt-1">{{ item.sent_by?.username || '-' }}</div>
          </div>
        </CCol>
      </CRow>

      <CRow class="mb-3" v-if="item.scheduled_send && item.schedule_datetime">
        <CCol :md="12">
          <div class="mb-3">
            <strong class="text-medium-emphasis">예약 발송 일시</strong>
            <div class="mt-1">
              <CBadge color="warning" size="lg">
                {{ formatDate(item.schedule_datetime) }}
              </CBadge>
            </div>
          </div>
        </CCol>
      </CRow>

      <hr />

      <div class="mb-3" v-if="item.title">
        <strong class="text-medium-emphasis">제목</strong>
        <div class="mt-1">{{ item.title }}</div>
      </div>

      <div class="mb-3">
        <strong class="text-medium-emphasis">메시지 내용</strong>
        <CCard class="mt-2">
          <CCardBody style="white-space: pre-wrap; background-color: #f8f9fa">
            {{ item.message_content }}
          </CCardBody>
        </CCard>
      </div>

      <div class="mb-3">
        <strong class="text-medium-emphasis">수신번호 목록</strong>
        <CCard class="mt-2">
          <CCardBody style="max-height: 200px; overflow-y: auto; background-color: #f8f9fa">
            <div v-for="(phone, index) in item.recipients" :key="index" class="mb-1">
              {{ index + 1 }}. {{ phone }}
            </div>
          </CCardBody>
        </CCard>
      </div>
    </CModalBody>
    <CModalFooter>
      <CButton color="secondary" @click="handleClose"> 닫기 </CButton>
    </CModalFooter>
  </CModal>
</template>
