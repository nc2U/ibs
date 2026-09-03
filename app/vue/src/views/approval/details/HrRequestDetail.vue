<script setup lang="ts">
import {
  CTable,
  CTableBody,
  CTableRow,
  CTableHeaderCell,
  CTableDataCell,
  CBadge,
} from '@coreui/vue'

defineProps<{
  content: Record<string, any>
  document?: any
}>()
</script>

<template>
  <CTable small bordered responsive class="mb-0">
    <CTableBody>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          신청 구분
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <CBadge color="primary">{{ content.request_type || '제증명서 발급' }}</CBadge>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          수령 방법
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">
          {{ content.receive_method || 'PDF 이메일 수신' }}
        </CTableDataCell>
      </CTableRow>

      <!-- 증명서 전용 행 -->
      <template v-if="content.request_type === 'CERTIFICATE' || !content.request_type">
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">증명서 종류</CTableHeaderCell>
          <CTableDataCell class="pl-3 fw-semibold text-primary">
            {{ content.cert_type || '재직증명서' }} ({{
              content.cert_language === 'ENGLISH' ? '영문' : '국문'
            }}, {{ content.cert_count ?? 1 }}부)
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">제출처 / 용도</CTableHeaderCell>
          <CTableDataCell class="pl-3">
            {{ content.submit_to || '-' }} / {{ content.usage_purpose || '-' }}
          </CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">주민번호 표기</CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3">
            {{ content.include_resident_num ? '뒷자리 전체 표기' : '생년월일만 표기' }}
          </CTableDataCell>
        </CTableRow>
      </template>

      <!-- 경조사 전용 행 -->
      <template v-else-if="content.request_type === 'CONGRATULATION_CONDOLENCE'">
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">경조 구분</CTableHeaderCell>
          <CTableDataCell class="pl-3 fw-semibold text-danger">
            {{ content.event_type || '-' }}
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">경조 일자</CTableHeaderCell>
          <CTableDataCell class="pl-3">{{ content.event_date || '-' }}</CTableDataCell>
        </CTableRow>
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">경조 장소</CTableHeaderCell>
          <CTableDataCell class="pl-3">{{ content.event_place || '-' }}</CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">경조금 신청액</CTableHeaderCell>
          <CTableDataCell class="pl-3 fw-bold text-danger">
            {{ (Number(content.congratulation_amount ?? content.amount) || 0).toLocaleString() }}
            원
          </CTableDataCell>
        </CTableRow>
        <CTableRow v-if="content.support_items">
          <CTableHeaderCell class="text-center bg-more-light">물품 지원 요청</CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3">{{ content.support_items }}</CTableDataCell>
        </CTableRow>
      </template>

      <!-- 휴복직 전용 행 -->
      <template
        v-else-if="
          content.request_type === 'LEAVE_OF_ABSENCE' || content.request_type === 'REINSTATEMENT'
        "
      >
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">기간 / 희망일</CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3 fw-semibold">
            <span v-if="content.request_type === 'LEAVE_OF_ABSENCE'">
              휴직: {{ content.leave_start_date || '-' }} ~
              {{ content.leave_end_date || '-' }}
            </span>
            <span v-else> 복직 희망일: {{ content.reinstatement_date || '-' }} </span>
          </CTableDataCell>
        </CTableRow>
      </template>

      <!-- 공통 사유 -->
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">신청 사유 / 상세</CTableHeaderCell>
        <CTableDataCell
          colspan="3"
          class="pl-3 py-3"
          style="white-space: pre-wrap; line-height: 1.6"
        >
          {{ content.reason || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.note">
        <CTableHeaderCell class="text-center bg-more-light">비고 / 특이사항</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 text-muted">{{ content.note }}</CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
