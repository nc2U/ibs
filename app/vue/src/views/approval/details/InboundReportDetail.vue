<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  content: Record<string, any>
  document?: any
}>()

const inboundId = computed(() => {
  return props.content.inbound_letter_id || props.document?.related_inbound_letter || null
})

const actionTypeInfo = computed(() => {
  const type = props.content.action_type
  const map: Record<string, { label: string; color: string }> = {
    REPLY_LETTER: { label: '대외 회신(답신) 공문 발송 필요', color: 'primary' },
    INTERNAL_ACTION: { label: '내부 조치 및 처리 (회신 불필요)', color: 'success' },
    RECEIPT_ONLY: { label: '단순 접수 및 부서 공람 / 보고', color: 'info' },
    BUDGET_ACTION: { label: '예산 집행 및 시정·보수 조치 수반', color: 'warning' },
    OTHER: { label: '기타', color: 'secondary' },
  }
  return (type && map[type]) || { label: type || '대외 회신 공문 발송', color: 'primary' }
})

const urgencyInfo = computed(() => {
  const urgency = props.content.urgency
  const map: Record<string, { label: string; color: string }> = {
    NORMAL: { label: '보통', color: 'secondary' },
    URGENT: { label: '긴급', color: 'warning' },
    VERY_URGENT: { label: '당일/익일 긴급', color: 'danger' },
  }
  return urgency && map[urgency] ? map[urgency] : null
})

const formattedBudget = computed(() => {
  const b = props.content.action_budget ?? props.content.amount
  if (b === undefined || b === null || b === '') return null
  const num = Number(b)
  return isNaN(num) ? String(b) : num.toLocaleString()
})
</script>

<template>
  <div class="inbound-report-detail">
    <!-- 연동 수신 공문 바로가기 버튼 -->
    <div v-if="inboundId" class="d-flex justify-content-end mb-2">
      <router-link
        :to="{ name: '수신 공문 관리 - 보기', params: { letterId: inboundId } }"
        class="btn btn-outline-primary btn-sm"
      >
        <CIcon name="cilExternalLink" class="me-1" />
        원문 수신 공문 바로가기
      </router-link>
    </div>

    <CTable small bordered responsive class="mb-0">
      <CTableBody>
        <!-- 발신처 & 발신처 문서번호 -->
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 140px">
            발신처
          </CTableHeaderCell>
          <CTableDataCell class="pl-3 fw-bold text-primary" style="width: 35%">
            {{ content.sender_name || document?.related_inbound_letter_detail?.sender_name || '-' }}
            <span
              v-if="
                content.sender_contact || document?.related_inbound_letter_detail?.sender_contact
              "
              class="text-muted fw-normal small ms-1"
            >
              ({{
                content.sender_contact || document?.related_inbound_letter_detail?.sender_contact
              }})
            </span>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 140px">
            발신처 문서번호
          </CTableHeaderCell>
          <CTableDataCell class="pl-3">
            {{
              content.document_number ||
              document?.related_inbound_letter_detail?.document_number ||
              '-'
            }}
          </CTableDataCell>
        </CTableRow>

        <!-- 사내 접수번호 & 접수 일자 -->
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light"> 사내 접수번호 </CTableHeaderCell>
          <CTableDataCell class="pl-3">
            <CBadge color="secondary" variant="outline">
              {{
                content.receipt_number ||
                document?.related_inbound_letter_detail?.receipt_number ||
                '-'
              }}
            </CBadge>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light"> 접수 일자 </CTableHeaderCell>
          <CTableDataCell class="pl-3">
            {{
              content.received_date || document?.related_inbound_letter_detail?.received_date || '-'
            }}
          </CTableDataCell>
        </CTableRow>

        <!-- 회신 마감기한 & 대응 처리방향 -->
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light"> 회신 마감기한 </CTableHeaderCell>
          <CTableDataCell class="pl-3">
            <span
              v-if="
                content.reply_due_date || document?.related_inbound_letter_detail?.reply_due_date
              "
              class="text-danger fw-bold"
            >
              {{
                content.reply_due_date || document?.related_inbound_letter_detail?.reply_due_date
              }}
            </span>
            <span v-else class="text-muted">기한 없음</span>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light"> 대응 처리방향 </CTableHeaderCell>
          <CTableDataCell class="pl-3">
            <CBadge :color="actionTypeInfo.color" class="me-2 py-1 px-2">
              {{ actionTypeInfo.label }}
            </CBadge>
            <CBadge v-if="urgencyInfo" :color="urgencyInfo.color" class="py-1 px-2">
              {{ urgencyInfo.label }}
            </CBadge>
          </CTableDataCell>
        </CTableRow>

        <!-- 수신공문 제목 -->
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light"> 수신공문 제목 </CTableHeaderCell>
          <CTableDataCell colspan="3" class="pl-3 fw-bold fs-6">
            {{
              content.letter_subject ||
              document?.related_inbound_letter_detail?.title ||
              document?.title ||
              '-'
            }}
          </CTableDataCell>
        </CTableRow>

        <!-- 수신 내용 요약 -->
        <CTableRow
          v-if="
            content.letter_summary ||
            content.letter_content ||
            document?.related_inbound_letter_detail?.content
          "
        >
          <CTableHeaderCell class="text-center bg-more-light"> 수신 내용 요약 </CTableHeaderCell>
          <CTableDataCell
            colspan="3"
            class="pl-3 py-3 bg-more-light"
            style="white-space: pre-wrap; line-height: 1.6"
          >
            {{
              content.letter_summary ||
              content.letter_content ||
              document?.related_inbound_letter_detail?.content
            }}
          </CTableDataCell>
        </CTableRow>

        <!-- 검토 및 조치계획 (기안 내용) -->
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">
            검토 및 조치계획<br />(기안 내용)
          </CTableHeaderCell>
          <CTableDataCell
            colspan="3"
            class="pl-3 py-3"
            style="white-space: pre-wrap; line-height: 1.8; min-height: 80px"
          >
            {{ content.review_opinion || content.body || document?.title || '-' }}
          </CTableDataCell>
        </CTableRow>

        <!-- 회신 예정일 & 소요 예산 -->
        <CTableRow v-if="content.reply_planned_date || content.action_budget || content.amount">
          <CTableHeaderCell class="text-center bg-more-light"> 회신 예정일 </CTableHeaderCell>
          <CTableDataCell class="pl-3">
            {{ content.reply_planned_date || '-' }}
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light"> 조치 소요예산 </CTableHeaderCell>
          <CTableDataCell class="pl-3">
            <span v-if="formattedBudget && formattedBudget !== '0'" class="text-primary fw-bold">
              {{ formattedBudget }} 원
            </span>
            <span v-else class="text-muted">예산 비소요 (0원)</span>
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>
  </div>
</template>
