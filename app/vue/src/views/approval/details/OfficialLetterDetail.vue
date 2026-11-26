<script setup lang="ts">
import { computed } from 'vue'
import type { ApprovalContent, ApprovalDocument } from '@/store/types/approval'
import {
  asOptNum,
  asStr,
  getSafeExternalUrl,
  getSealTypeLabel,
  getSendMethodLabel,
} from '../utils/approvalMeta'

const props = defineProps<{
  content: ApprovalContent
  document?: ApprovalDocument | null
}>()

const officialLetterId = computed(() => asOptNum(props.content.official_letter_id))

const safeSealImageUrl = computed(() => getSafeExternalUrl(asStr(props.content.seal_image)))
</script>

<template>
  <div v-if="officialLetterId" class="d-flex justify-content-end mb-2">
    <router-link
      :to="{ name: '발송 공문 관리 - 보기', params: { letterId: officialLetterId } }"
      class="btn btn-outline-primary btn-sm"
    >
      <CIcon name="cilExternalLink" class="me-1" />
      발송 공문 바로가기
    </router-link>
  </div>

  <CTable small bordered responsive class="mb-0">
    <CTableBody>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          수신처
        </CTableHeaderCell>
        <CTableDataCell class="ps-3 fw-semibold text-primary">
          {{ content.receiver || '-' }}
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          참조처
        </CTableHeaderCell>
        <CTableDataCell class="ps-3">{{ content.refer_to || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">발신 명의</CTableHeaderCell>
        <CTableDataCell class="ps-3">{{ content.sender_name || '대표이사' }}</CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">대외 문서번호</CTableHeaderCell>
        <CTableDataCell class="ps-3">{{ content.doc_number_external || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">공문 제목</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3 fw-bold">
          {{ content.letter_subject || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">공문 본문(요지)</CTableHeaderCell>
        <CTableDataCell
          colspan="3"
          class="ps-3 py-3"
          style="white-space: pre-wrap; line-height: 1.6"
        >
          {{ content.letter_body || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.enclosed_files_desc">
        <CTableHeaderCell class="text-center bg-more-light">붙임 서류 내역</CTableHeaderCell>
        <CTableDataCell colspan="3" class="ps-3" style="white-space: pre-wrap">
          {{ content.enclosed_files_desc }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">발송 방법</CTableHeaderCell>
        <CTableDataCell class="ps-3">
          <v-chip color="info" variant="flat" size="x-small">
            {{ getSendMethodLabel(asStr(content.send_method, 'EMAIL')) }}
          </v-chip>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">발송 희망일</CTableHeaderCell>
        <CTableDataCell class="ps-3">{{ content.send_due_date || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">날인 인감</CTableHeaderCell>
        <CTableDataCell class="ps-3">
          <div class="d-flex align-items-center">
            <v-chip color="grey-darken-2" variant="flat" size="x-small" class="me-2">
              {{
                asStr(content.seal_name) || getSealTypeLabel(asStr(content.seal_type, 'CORP_SEAL'))
              }}
            </v-chip>
            <img
              v-if="safeSealImageUrl"
              :src="safeSealImageUrl"
              alt="인장"
              style="width: 28px; height: 28px; object-fit: contain"
              class="border rounded p-1 bg-more-white"
            />
          </div>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">날인 부수</CTableHeaderCell>
        <CTableDataCell class="ps-3">{{ content.seal_count ?? 1 }} 부</CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
