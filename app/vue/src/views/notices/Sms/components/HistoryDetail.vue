<script lang="ts" setup>
import { computed } from 'vue'

// Props
interface Props {
  visible: boolean
  item: HistoryItem | null
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

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

// 모달 닫기
const handleClose = () => {
  emit('update:visible', false)
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
  return colors[props.item.msgType] || 'secondary'
})

// 상태 뱃지 색상
const getStatusColor = computed(() => {
  if (!props.item) return 'secondary'
  if (props.item.status === '01' || props.item.status === '200') return 'success'
  return 'danger'
})
</script>

<template>
  <CModal
    :visible="visible"
    @close="handleClose"
    size="lg"
    backdrop="static"
  >
    <CModalHeader>
      <CModalTitle>발송 상세 내역</CModalTitle>
    </CModalHeader>
    <CModalBody v-if="item">
      <CRow class="mb-3">
        <CCol :md="6">
          <div class="mb-3">
            <strong class="text-medium-emphasis">요청번호</strong>
            <div class="mt-1">{{ item.requestNo }}</div>
          </div>
        </CCol>
        <CCol :md="6">
          <div class="mb-3">
            <strong class="text-medium-emphasis">발송일시</strong>
            <div class="mt-1">{{ item.sendDate }}</div>
          </div>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CCol :md="6">
          <div class="mb-3">
            <strong class="text-medium-emphasis">수신번호</strong>
            <div class="mt-1">{{ item.phone }}</div>
          </div>
        </CCol>
        <CCol :md="6" v-if="item.callback">
          <div class="mb-3">
            <strong class="text-medium-emphasis">발신번호</strong>
            <div class="mt-1">{{ item.callback }}</div>
          </div>
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CCol :md="6">
          <div class="mb-3">
            <strong class="text-medium-emphasis">메시지 타입</strong>
            <div class="mt-1">
              <CBadge :color="getTypeColor" size="lg">
                {{ item.msgType }}
              </CBadge>
            </div>
          </div>
        </CCol>
        <CCol :md="6">
          <div class="mb-3">
            <strong class="text-medium-emphasis">발송 상태</strong>
            <div class="mt-1">
              <CBadge :color="getStatusColor" size="lg">
                {{ item.statusMessage }}
              </CBadge>
              <span class="ms-2 text-medium-emphasis">(코드: {{ item.status }})</span>
            </div>
          </div>
        </CCol>
      </CRow>

      <hr />

      <div class="mb-3">
        <strong class="text-medium-emphasis">메시지 내용</strong>
        <CCard class="mt-2">
          <CCardBody style="white-space: pre-wrap; background-color: #f8f9fa;">
            {{ item.message }}
          </CCardBody>
        </CCard>
      </div>

      <div v-if="item.status !== '01' && item.status !== '200'" class="alert alert-warning">
        <CIcon name="cilWarning" class="me-2" />
        <strong>발송 실패</strong>
        <div class="mt-1">상태 코드 {{ item.status }}에 대한 자세한 정보는 에러 코드 참조를 확인하세요.</div>
      </div>
    </CModalBody>
    <CModalFooter>
      <CButton color="secondary" @click="handleClose">
        닫기
      </CButton>
    </CModalFooter>
  </CModal>
</template>
