<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useApproval } from '@/store/pinia/approval'
import type { ApprovalDocumentListItem } from '@/store/types/approval'
import { TableSecondary } from '@/utils/cssMixins'
import {
  DOC_STATUS_CHIP_COLOR,
  DOC_STATUS_LABEL,
  SECURITY_LEVEL_META,
  fmtDate,
  getSafeExternalUrl,
  getUserDisplayName,
} from '../utils/approvalMeta'

const router = useRouter()
const store = useApproval()

const activeTab = ref<'approved' | 'observed'>('approved')
const searchText = ref('')

const approvedList = computed<ApprovalDocumentListItem[]>(() => store.approvedList)
const observedList = computed<ApprovalDocumentListItem[]>(() => store.observedList)

const currentList = computed<ApprovalDocumentListItem[]>(() => {
  return activeTab.value === 'approved' ? approvedList.value : observedList.value
})

const filteredList = computed<ApprovalDocumentListItem[]>(() => {
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
        component="button"
        type="button"
        :active="activeTab === 'approved'"
        @click="activeTab = 'approved'"
      >
        <CIcon name="cilCheckCircle" class="me-1 text-success" />
        결재 완료 문서
        <v-chip color="success" variant="flat" size="x-small" class="ms-1">
          {{ approvedList.length }}
        </v-chip>
      </CNavLink>
    </CNavItem>
    <CNavItem>
      <CNavLink
        component="button"
        type="button"
        :active="activeTab === 'observed'"
        @click="activeTab = 'observed'"
      >
        <CIcon name="cilUserFollow" class="me-1 text-info" />
        참조 / 공람 문서
        <v-chip color="info" variant="flat" size="x-small" class="ms-1">
          {{ observedList.length }}
        </v-chip>
      </CNavLink>
    </CNavItem>
  </CNav>

  <!-- 상단 액션바: 검색 + 총 건수 -->
  <CRow class="mb-3">
    <CCol md="5">
      <CInputGroup>
        <CInputGroupText class="bg-more-light">
          <v-icon icon="mdi-magnify" size="small" />
        </CInputGroupText>
        <CFormInput v-model="searchText" placeholder="제목, 문서유형, 기안자, 문서번호 검색..." />
        <CButton
          v-if="searchText"
          color="light"
          type="button"
          title="검색어 초기화"
          @click="searchText = ''"
        >
          <v-icon icon="mdi-close" size="small" />
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
    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center">
        <CTableHeaderCell style="width: 180px">문서번호</CTableHeaderCell>
        <CTableHeaderCell style="width: 120px">문서 유형</CTableHeaderCell>
        <CTableHeaderCell style="width: 90px">공개등급</CTableHeaderCell>
        <CTableHeaderCell>제목</CTableHeaderCell>
        <CTableHeaderCell v-if="activeTab === 'observed'" style="width: 90px">
          상태
        </CTableHeaderCell>
        <CTableHeaderCell style="width: 120px">기안자</CTableHeaderCell>
        <CTableHeaderCell style="width: 130px">기안일</CTableHeaderCell>
        <CTableHeaderCell style="width: 130px">
          {{ activeTab === 'approved' ? '최종 승인일' : '완료일시' }}
        </CTableHeaderCell>
        <CTableHeaderCell style="width: 100px">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow v-if="!filteredList.length">
        <CTableDataCell
          :colspan="activeTab === 'observed' ? 9 : 8"
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
        <CTableDataCell class="text-center font-monospace small">
          {{ doc.doc_number || '-' }}
        </CTableDataCell>

        <!-- 문서 유형 -->
        <CTableDataCell class="text-center">
          <v-chip color="primary" size="x-small" variant="outlined">{{ doc.doc_type_name }}</v-chip>
        </CTableDataCell>

        <!-- 공개 등급 -->
        <CTableDataCell class="text-center">
          <v-chip
            v-if="doc.security_level"
            size="x-small"
            variant="tonal"
            :color="SECURITY_LEVEL_META[doc.security_level].color"
          >
            {{ SECURITY_LEVEL_META[doc.security_level].shortLabel }}
          </v-chip>
          <span v-else class="text-muted small">-</span>
        </CTableDataCell>

        <!-- 제목 -->
        <CTableDataCell class="fw-semibold">
          {{ doc.title }}
        </CTableDataCell>

        <!-- 참조 탭 전용: 상태 뱃지 -->
        <CTableDataCell v-if="activeTab === 'observed'" class="text-center">
          <v-chip size="x-small" :color="DOC_STATUS_CHIP_COLOR[doc.status]">
            {{ DOC_STATUS_LABEL[doc.status] }}
          </v-chip>
        </CTableDataCell>

        <!-- 기안자 -->
        <CTableDataCell class="text-center">
          <div>{{ getUserDisplayName(doc.drafter) }}</div>
          <small
            v-if="doc.drafter_assignment_desc"
            class="text-muted d-block"
            style="font-size: 0.75rem"
          >
            {{ doc.drafter_assignment_desc.split('] ')[1] || doc.drafter_assignment_desc }}
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
            v-if="getSafeExternalUrl(doc.pdf_url)"
            size="sm"
            color="danger"
            variant="outline"
            :href="getSafeExternalUrl(doc.pdf_url)"
            target="_blank"
            rel="noopener noreferrer"
          >
            <CIcon name="cilCloudDownload" size="sm" />
          </CButton>
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
