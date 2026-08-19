<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useApproval } from '@/store/pinia/approval'
import type { ApprovalDocument } from '@/store/types/approval'

const router = useRouter()
const store = useApproval()
const approvedList = computed<ApprovalDocument[]>(() => store.approvedList)

const searchText = ref('')

const filteredList = computed<ApprovalDocument[]>(() => {
  if (!searchText.value) return approvedList.value
  const q = searchText.value.toLowerCase()
  return approvedList.value.filter(
    d =>
      d.title.toLowerCase().includes(q) ||
      (d.doc_type_name ?? '').toLowerCase().includes(q) ||
      (d.doc_number ?? '').toLowerCase().includes(q) ||
      (d.drafter?.full_name ?? '').toLowerCase().includes(q),
  )
})

const fmtDate = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('ko-KR')
}

const fmtDatetime = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const goDetail = (id: number) => {
  router.push({ name: '결재 문서함 - 보기', params: { docId: id } })
}

onMounted(() => {
  store.fetchMyApproved()
})
</script>

<template>
  <!-- 상단 액션바: 검색 + 총 건수 -->
  <CRow class="mb-3">
    <CCol md="5">
      <CInputGroup>
        <CFormInput v-model="searchText" placeholder="제목, 문서유형, 기안자, 문서번호 검색..." />
        <CButton color="light" @click="searchText = ''">
          <v-icon icon="mdi-magnify" /> 검색
        </CButton>
      </CInputGroup>
    </CCol>
    <CCol class="d-flex align-items-center justify-content-end">
      <span class="text-muted small">
        결재 완료 문서 총 <strong class="text-success">{{ filteredList.length }}</strong>
        건
      </span>
    </CCol>
  </CRow>

  <!-- 목록 테이블 -->
  <CTable hover responsive bordered>
    <CTableHead color="light">
      <CTableRow class="text-center">
        <CTableHeaderCell style="width: 140px">문서번호</CTableHeaderCell>
        <CTableHeaderCell style="width: 130px">문서 유형</CTableHeaderCell>
        <CTableHeaderCell>제목</CTableHeaderCell>
        <CTableHeaderCell style="width: 100px">기안자</CTableHeaderCell>
        <CTableHeaderCell style="width: 110px">기안일</CTableHeaderCell>
        <CTableHeaderCell style="width: 110px">최종 승인일</CTableHeaderCell>
        <CTableHeaderCell style="width: 130px">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-if="!filteredList.length">
        <CTableDataCell colspan="7" class="text-center text-medium-emphasis py-5">
          <CIcon name="cilCheckCircle" size="xl" class="mb-2 text-success" />
          <div>결재 완료된 문서가 없습니다.</div>
        </CTableDataCell>
      </CTableRow>
      <CTableRow
        v-for="doc in filteredList"
        :key="doc.id"
        style="cursor: pointer"
        @click="goDetail(doc.id)"
      >
        <!-- 문서번호 -->
        <CTableDataCell class="text-center text-monospace small">
          {{ doc.doc_number || '-' }}
        </CTableDataCell>

        <!-- 문서 유형 -->
        <CTableDataCell>
          <CBadge color="primary" shape="rounded-pill">{{ doc.doc_type_name }}</CBadge>
        </CTableDataCell>

        <!-- 제목 -->
        <CTableDataCell class="fw-semibold">
          {{ doc.title }}
        </CTableDataCell>

        <!-- 기안자 -->
        <CTableDataCell class="text-center">
          <div>{{ doc.drafter?.full_name }}</div>
          <small
            v-if="doc.drafter_assignment_desc"
            class="text-muted d-block"
            style="font-size: 0.75rem"
          >
            {{ doc.drafter_assignment_desc.split('] ')[1] || '' }}
          </small>
        </CTableDataCell>

        <!-- 기안일 -->
        <CTableDataCell class="text-center text-medium-emphasis small">
          {{ fmtDate(doc.created_at) }}
        </CTableDataCell>

        <!-- 최종 승인일 -->
        <CTableDataCell class="text-center text-medium-emphasis small">
          {{ fmtDate(doc.completed_at) }}
        </CTableDataCell>

        <!-- 관리 버튼 -->
        <CTableDataCell class="text-center" @click.stop>
          <CButton
            size="sm"
            color="primary"
            variant="outline"
            class="me-1"
            @click="goDetail(doc.id)"
          >
            보기
          </CButton>
          <CButton
            v-if="doc.pdf_url"
            size="sm"
            color="danger"
            variant="outline"
            :href="doc.pdf_url"
            target="_blank"
          >
            <CIcon name="cilCloudDownload" size="sm" />
          </CButton>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
