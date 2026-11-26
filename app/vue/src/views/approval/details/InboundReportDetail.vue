<script setup lang="ts">
import { computed } from 'vue'
import { CTable, CTableBody } from '@coreui/vue'
import type { ApprovalContent, ApprovalDocument } from '@/store/types/approval'
import {
  asOptNum,
  firstStr,
  getInboundActionTypeInfo,
  getInboundUrgencyInfo,
} from '../utils/approvalMeta'

const props = defineProps<{
  content: ApprovalContent
  document?: ApprovalDocument | null
}>()

const inboundDetail = computed(
  () =>
    (props.document as (ApprovalDocument & {
      related_inbound_letter_detail?: Record<string, string | null | undefined>
    }) | null)?.related_inbound_letter_detail,
)

const inboundId = computed(
  () => asOptNum(props.content.inbound_letter_id) ?? props.document?.related_inbound_letter ?? null,
)

const actionTypeInfo = computed(() => getInboundActionTypeInfo(props.content.action_type))
const urgencyInfo = computed(() => getInboundUrgencyInfo(props.content.urgency))

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
          <CTableDataCell class="ps-3 fw-bold text-primary" style="width: 35%">
            {{ firstStr(content.sender_name, inboundDetail?.sender_name) || '-' }}
            <span
              v-if="content.sender_contact || inboundDetail?.sender_contact"
              class="text-muted fw-normal small ms-1"
            >
              ({{ firstStr(content.sender_contact, inboundDetail?.sender_contact) }})
            </span>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light" style="width: 140px">
            발신처 문서번호
          </CTableHeaderCell>
          <CTableDataCell class="ps-3">
            {{ firstStr(content.document_number, inboundDetail?.document_number) || '-' }}
          </CTableDataCell>
        </CTableRow>

        <!-- 사내 접수번호 & 접수 일자 -->
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">사내 접수번호</CTableHeaderCell>
          <CTableDataCell class="ps-3">
            <v-chip color="secondary" variant="flat" size="x-small">
              {{ firstStr(content.receipt_number, inboundDetail?.receipt_number) || '-' }}
            </v-chip>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">접수 일자</CTableHeaderCell>
          <CTableDataCell class="ps-3">
            {{ firstStr(content.received_date, inboundDetail?.received_date) || '-' }}
          </CTableDataCell>
        </CTableRow>

        <!-- 회신 마감기한 & 대응 처리방향 -->
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">회신 마감기한</CTableHeaderCell>
          <CTableDataCell class="ps-3">
            <span
              v-if="content.reply_due_date || inboundDetail?.reply_due_date"
              class="text-danger fw-bold"
            >
              {{ firstStr(content.reply_due_date, inboundDetail?.reply_due_date) }}
            </span>
            <span v-else class="text-muted">기한 없음</span>
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">대응 처리방향</CTableHeaderCell>
          <CTableDataCell class="ps-3">
            <v-chip
              :color="actionTypeInfo.color"
              variant="flat"
              size="x-small"
              class="me-2 py-1 px-2"
            >
              {{ actionTypeInfo.label }}
            </v-chip>
            <v-chip
              v-if="urgencyInfo"
              :color="urgencyInfo.color"
              variant="flat"
              size="x-small"
              class="py-1 px-2"
            >
              {{ urgencyInfo.label }}
            </v-chip>
          </CTableDataCell>
        </CTableRow>

        <!-- 수신공문 제목 -->
        <CTableRow>
          <CTableHeaderCell class="text-center bg-more-light">수신공문 제목</CTableHeaderCell>
          <CTableDataCell colspan="3" class="ps-3 fw-bold fs-6">
            {{ firstStr(content.letter_subject, inboundDetail?.title, document?.title) || '-' }}
          </CTableDataCell>
        </CTableRow>

        <!-- 수신 내용 요약 -->
        <CTableRow
          v-if="content.letter_summary || content.letter_content || inboundDetail?.content"
        >
          <CTableHeaderCell class="text-center bg-more-light">수신 내용 요약</CTableHeaderCell>
          <CTableDataCell
            colspan="3"
            class="ps-3 py-3 bg-more-light"
            style="white-space: pre-wrap; line-height: 1.6"
          >
            {{
              firstStr(content.letter_summary, content.letter_content, inboundDetail?.content)
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
            class="ps-3 py-3"
            style="white-space: pre-wrap; line-height: 1.8; min-height: 80px"
          >
            {{ firstStr(content.review_opinion, content.body, document?.title) || '-' }}
          </CTableDataCell>
        </CTableRow>

        <!-- 회신 예정일 & 소요 예산 -->
        <CTableRow v-if="content.reply_planned_date || content.action_budget || content.amount">
          <CTableHeaderCell class="text-center bg-more-light">회신 예정일</CTableHeaderCell>
          <CTableDataCell class="ps-3">
            {{ content.reply_planned_date || '-' }}
          </CTableDataCell>
          <CTableHeaderCell class="text-center bg-more-light">조치 소요예산</CTableHeaderCell>
          <CTableDataCell class="ps-3">
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
