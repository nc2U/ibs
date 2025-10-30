<script lang="ts" setup>
import type { ConsultationLog } from '@/store/types/contract'

// Props
const props = defineProps<{
  log: ConsultationLog
}>()

// Events
const emit = defineEmits<{
  save: [log: ConsultationLog]
  cancel: []
}>()

// 저장
const save = () => {
  emit('save', props.log)
}

// 취소
const cancel = () => {
  emit('cancel')
}
</script>

<template>
  <div class="p-3">
    <CRow class="g-2">
      <CCol :md="3">
        <CFormLabel>상담일자</CFormLabel>
        <CFormInput v-model="log.consultation_date" type="date" size="sm" />
      </CCol>
      <CCol :md="2">
        <CFormLabel>채널</CFormLabel>
        <CFormSelect v-model="log.channel" size="sm">
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
        <CFormSelect v-model="log.category" size="sm">
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
        <CFormLabel>처리상태</CFormLabel>
        <CFormSelect v-model="log.status" size="sm">
          <option value="1">처리대기</option>
          <option value="2">처리중</option>
          <option value="3">처리완료</option>
          <option value="4">보류</option>
        </CFormSelect>
      </CCol>
      <CCol :md="3">
        <CFormLabel>중요도</CFormLabel>
        <CFormSelect v-model="log.priority" size="sm">
          <option value="low">낮음</option>
          <option value="normal">보통</option>
          <option value="high">높음</option>
          <option value="urgent">긴급</option>
        </CFormSelect>
      </CCol>
    </CRow>

    <CRow class="g-2 mt-2">
      <CCol :md="12">
        <CFormLabel>제목</CFormLabel>
        <CFormInput v-model="log.title" size="sm" />
      </CCol>
    </CRow>

    <CRow class="g-2 mt-2">
      <CCol :md="12">
        <CFormLabel>내용</CFormLabel>
        <CFormTextarea v-model="log.content" rows="4" size="sm" />
      </CCol>
    </CRow>

    <CRow class="g-2 mt-2">
      <CCol :md="12">
        <CFormLabel>후속조치 내용</CFormLabel>
        <CFormTextarea v-model="log.follow_up_note" rows="2" size="sm" />
      </CCol>
    </CRow>

    <CRow class="mt-3">
      <CCol class="text-end">
        <v-btn color="secondary" size="small" @click="cancel" class="me-2"> 취소 </v-btn>
        <v-btn color="success" size="small" @click="save">저장</v-btn>
      </CCol>
    </CRow>
  </div>
</template>
