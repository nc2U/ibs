<script setup lang="ts">
defineProps<{
  content: Record<string, any>
  document?: any
}>()
</script>

<template>
  <div v-if="content.official_letter_id" class="d-flex justify-content-end mb-2">
    <router-link
      :to="{ name: '발송 공문 관리 - 보기', params: { letterId: content.official_letter_id } }"
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
        <CTableDataCell class="pl-3 fw-semibold text-primary">
          {{ content.receiver || '-' }}
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light" style="width: 130px">
          참조처
        </CTableHeaderCell>
        <CTableDataCell class="pl-3">{{ content.refer_to || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">발신 명의</CTableHeaderCell>
        <CTableDataCell class="pl-3">{{ content.sender_name || '대표이사' }}</CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">대외 문서번호</CTableHeaderCell>
        <CTableDataCell class="pl-3">{{ content.doc_number_external || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">공문 제목</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3 fw-bold">
          {{ content.letter_subject || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">공문 본문(요지)</CTableHeaderCell>
        <CTableDataCell
          colspan="3"
          class="pl-3 py-3"
          style="white-space: pre-wrap; line-height: 1.6"
        >
          {{ content.letter_body || '-' }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow v-if="content.enclosed_files_desc">
        <CTableHeaderCell class="text-center bg-more-light">붙임 서류 내역</CTableHeaderCell>
        <CTableDataCell colspan="3" class="pl-3" style="white-space: pre-wrap">
          {{ content.enclosed_files_desc }}
        </CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">발송 방법</CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <v-chip color="info" variant="flat" size="x-small">{{
            content.send_method || '이메일'
          }}</v-chip>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">발송 희망일</CTableHeaderCell>
        <CTableDataCell class="pl-3">{{ content.send_due_date || '-' }}</CTableDataCell>
      </CTableRow>
      <CTableRow>
        <CTableHeaderCell class="text-center bg-more-light">날인 인감</CTableHeaderCell>
        <CTableDataCell class="pl-3">
          <div class="d-flex align-items-center">
            <v-chip color="dark" variant="flat" size="x-small" class="me-2">
              {{ content.seal_name || content.seal_type || '법인인감' }}
            </v-chip>
            <img
              v-if="content.seal_image"
              :src="content.seal_image"
              alt="인장"
              style="width: 28px; height: 28px; object-fit: contain"
              class="border rounded p-1 bg-white"
            />
          </div>
        </CTableDataCell>
        <CTableHeaderCell class="text-center bg-more-light">날인 부수</CTableHeaderCell>
        <CTableDataCell class="pl-3">{{ content.seal_count ?? 1 }} 부</CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
