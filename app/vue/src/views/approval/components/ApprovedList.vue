<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useApproval } from '@/store/pinia/approval'
import type { ApprovalDocument, DocumentStatus } from '@/store/types/approval'

const router = useRouter()
const store = useApproval()

const activeTab = ref<'approved' | 'observed'>('approved')
const searchText = ref('')

const approvedList = computed<ApprovalDocument[]>(() => store.approvedList)
const observedList = computed<ApprovalDocument[]>(() => store.observedList)

const currentList = computed<ApprovalDocument[]>(() => {
  return activeTab.value === 'approved' ? approvedList.value : observedList.value
})

const filteredList = computed<ApprovalDocument[]>(() => {
  if (!searchText.value) return currentList.value
  const q = searchText.value.toLowerCase()
  return currentList.value.filter(
    d =>
      d.title.toLowerCase().includes(q) ||
      (d.doc_type_name ?? '').toLowerCase().includes(q) ||
      (d.doc_number ?? '').toLowerCase().includes(q) ||
      (d.drafter?.full_name ?? '').toLowerCase().includes(q),
  )
})

const STATUS_LABEL: Record<DocumentStatus, string> = {
  draft: '임시저장',
  pending: '결재중',
  approved: '승인완료',
  rejected: '반려',
  cancelled: '취소',
}

const STATUS_COLOR: Record<DocumentStatus, string> = {
  draft: 'secondary',
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  cancelled: 'dark',
}

const fmtDate = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('ko-KR')
}

const goDetail = (id: number) => {
  router.push({ name: '결재 문서함 - 보기', params: { docId: id } })
}

onMounted(() => {
  store.fetchMyApproved()
  store.fetchMyObserved()
})
</script>

<template>
  <!-- 탭 전환 네비게이션 -->
  <CNav variant="tabs" class="mb-3">
    <CNavItem>
      <CNavLink
        href="javascript:void(0);"
        :active="activeTab === 'approved'"
        @click="activeTab = 'approved'"
      >
        <CIcon name="cilCheckCircle" class="me-1 text-success" />
        결재 완료 문서
        <CBadge color="success" shape="rounded-pill" class="ms-1">
          {{ approvedList.length }}
        </CBadge>
      </CNavLink>
    </CNavItem>
    <CNavItem>
      <CNavLink
        href="javascript:void(0);"
        :active="activeTab === 'observed'"
        @click="activeTab = 'observed'"
      >
        <CIcon name="cilUserFollow" class="me-1 text-info" />
        참조 / 공람 문서
        <CBadge color="info" shape="rounded-pill" class="ms-1">
          {{ observedList.length }}
        </CBadge>
      </CNavLink>
    </CNavItem>
  </CNav>

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
        {{ activeTab === 'approved' ? '결재 완료 문서' : '참조/공람 문서' }} 총
        <strong :class="activeTab === 'approved' ? 'text-success' : 'text-info'">
          {{ filteredList.length }}
        </strong>
        건
      </span>
    </CCol>
  </CRow>

  <!-- 목록 테이블 -->
  <CTable hover responsive bordered align="middle">
    <CTableHead color="light">
      <CTableRow class="text-center">
        <CTableHeaderCell style="width: 200px">문서번호</CTableHeaderCell>
        <CTableHeaderCell style="width: 130px">문서 유형</CTableHeaderCell>
        <CTableHeaderCell>제목</CTableHeaderCell>
        <CTableHeaderCell v-if="activeTab === 'observed'" style="width: 90px">
          상태
        </CTableHeaderCell>
        <CTableHeaderCell style="width: 120px">기안자</CTableHeaderCell>
        <CTableHeaderCell style="width: 140px">기안일</CTableHeaderCell>
        <CTableHeaderCell style="width: 140px">
          {{ activeTab === 'approved' ? '최종 승인일' : '완료일시' }}
        </CTableHeaderCell>
        <CTableHeaderCell style="width: 120px">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-if="!filteredList.length">
        <CTableDataCell
          :colspan="activeTab === 'observed' ? 8 : 7"
          class="text-center text-medium-emphasis py-5"
        >
          <CIcon
            :name="activeTab === 'approved' ? 'cilCheckCircle' : 'cilUserFollow'"
            size="xl"
            class="mb-2 text-muted"
          />
          <div>
            {{
              activeTab === 'approved'
                ? '결재 완료된 문서가 없습니다.'
                : '참조(공람)된 문서가 없습니다.'
            }}
          </div>
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
        <CTableDataCell class="text-center">
          <v-chip color="primary" size="x-small">{{ doc.doc_type_name }}</v-chip>
        </CTableDataCell>

        <!-- 제목 -->
        <CTableDataCell class="fw-semibold">
          {{ doc.title }}
        </CTableDataCell>

        <!-- 참조 탭 전용: 상태 뱃지 -->
        <CTableDataCell v-if="activeTab === 'observed'" class="text-center">
          <v-chip size="x-small" :color="STATUS_COLOR[doc.status]">
            {{ STATUS_LABEL[doc.status] }}
          </v-chip>
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
        <CTableDataCell class="text-center text-medium-emphasis">
          {{ fmtDate(doc.created_at) }}
        </CTableDataCell>

        <!-- 최종 승인일 / 완료일 -->
        <CTableDataCell class="text-center text-medium-emphasis">
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
