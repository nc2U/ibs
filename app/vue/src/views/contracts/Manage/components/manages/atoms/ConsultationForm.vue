<script lang="ts" setup>
import { ref } from 'vue'
import type { ConsultationLog } from '@/store/types/contract'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

// Events
const emit = defineEmits<{
  submit: [data: Partial<ConsultationLog>]
}>()

// 폼 데이터
const formData = ref<Partial<ConsultationLog>>({
  consultation_date: new Date().toISOString().split('T')[0],
  channel: 'phone',
  category: 'question',
  title: '',
  content: '',
  status: '1',
  priority: 'normal',
  follow_up_required: false,
  follow_up_note: '',
  completion_date: null,
  is_important: false,
})

// 폼 제출
const submitForm = () => {
  if (!(formData.value.title as string)?.trim()) {
    alert('상담 제목을 입력해주세요.')
    return
  }
  emit('submit', formData.value as any)
  resetForm()
}

// 폼 초기화
const resetForm = () => {
  formData.value = {
    consultation_date: new Date().toISOString().split('T')[0],
    channel: 'phone',
    category: 'question',
    title: '',
    content: '',
    status: '1',
    priority: 'normal',
    follow_up_required: false,
    follow_up_note: '',
    completion_date: null,
    is_important: false,
  }
}
</script>

<template>
  <CCard class="mb-3">
    <CCardBody>
      <CRow class="g-2">
        <CCol :md="4">
          <CFormLabel>상담일자</CFormLabel>
          <DatePicker v-model="formData.consultation_date" />
        </CCol>
        <CCol :md="2">
          <CFormLabel>채널</CFormLabel>
          <CFormSelect v-model="formData.channel" size="sm">
            <option value="visit">방문</option>
            <option value="phone">전화</option>
            <option value="email">이메일</option>
            <option value="sms">문자</option>
            <option value="kakao">카카오톡</option>
            <option value="other">기타</option>
          </CFormSelect>
        </CCol>
        <CCol :md="2">
          <CFormLabel>유형</CFormLabel>
          <CFormSelect v-model="formData.category" size="sm">
            <option value="payment">납부상담</option>
            <option value="contract">계약상담</option>
            <option value="change">변경상담</option>
            <option value="complaint">민원/불만</option>
            <option value="question">문의</option>
            <option value="succession">승계상담</option>
            <option value="release">해지상담</option>
            <option value="document">서류관련</option>
            <option value="etc">기타</option>
          </CFormSelect>
        </CCol>
        <CCol :md="2">
          <CFormLabel>중요도</CFormLabel>
          <CFormSelect v-model="formData.priority" size="sm">
            <option value="low">낮음</option>
            <option value="normal">보통</option>
            <option value="high">높음</option>
            <option value="urgent">긴급</option>
          </CFormSelect>
        </CCol>
        <CCol :md="2">
          <CFormLabel>처리상태</CFormLabel>
          <CFormSelect v-model="formData.status" size="sm">
            <option value="1">처리대기</option>
            <option value="2">처리중</option>
            <option value="3">처리완료</option>
            <option value="4">보류</option>
          </CFormSelect>
        </CCol>
      </CRow>
      <CRow class="g-2 mt-0">
        <CCol :md="12">
          <CFormInput v-model="formData.title" size="sm" placeholder="상담 제목" />
        </CCol>

        <CCol :md="12">
          <CFormTextarea v-model="formData.content" rows="3" placeholder="상담 내용" />
        </CCol>
      </CRow>

      <CRow class="mt-3">
        <CCol class="text-end">
          <v-btn color="primary" size="small" @click="submitForm">
            <v-icon icon="mdi-plus" size="18" class="me-1" />
            등록
          </v-btn>
        </CCol>
      </CRow>
    </CCardBody>
  </CCard>
</template>
