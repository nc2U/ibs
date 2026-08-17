<template>
  <CRow>
    <CCol>
      <CCard class="mb-4">
        <CCardHeader class="d-flex align-items-center justify-content-between">
          <span>
            <CIcon icon="cil-description" class="me-2" />
            기안함
          </span>
          <CButton color="primary" size="sm" @click="router.push('/approval/create')">
            <CIcon icon="cil-plus" class="me-1" />새 기안
          </CButton>
        </CCardHeader>
        <CCardBody>
          <CTable hover responsive>
            <CTableHead color="light">
              <CTableRow>
                <CTableHeaderCell style="width: 140px">문서 유형</CTableHeaderCell>
                <CTableHeaderCell>제목</CTableHeaderCell>
                <CTableHeaderCell style="width: 80px">상태</CTableHeaderCell>
                <CTableHeaderCell style="width: 80px">단계</CTableHeaderCell>
                <CTableHeaderCell style="width: 120px">기안일시</CTableHeaderCell>
                <CTableHeaderCell style="width: 120px">완료일시</CTableHeaderCell>
                <CTableHeaderCell style="width: 80px" class="text-center">관리</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              <CTableRow v-if="!draftedList.length">
                <CTableDataCell colspan="7" class="text-center text-medium-emphasis py-4">
                  기안한 문서가 없습니다.
                </CTableDataCell>
              </CTableRow>
              <CTableRow
                v-for="doc in draftedList"
                :key="doc.id"
                class="cursor-pointer"
                @click="router.push(`/approval/${doc.id}`)"
              >
                <CTableDataCell>
                  <CBadge color="primary" shape="rounded-pill">{{ doc.doc_type_name }}</CBadge>
                </CTableDataCell>
                <CTableDataCell class="fw-semibold">{{ doc.title }}</CTableDataCell>
                <CTableDataCell>
                  <CBadge :color="statusColor(doc.status)">{{ statusLabel(doc.status) }}</CBadge>
                </CTableDataCell>
                <CTableDataCell class="text-center">
                  <span v-if="doc.status === 'pending'">{{ doc.current_step }}단계</span>
                  <span v-else class="text-medium-emphasis">-</span>
                </CTableDataCell>
                <CTableDataCell class="text-medium-emphasis small">{{ fmtDate(doc.created_at) }}</CTableDataCell>
                <CTableDataCell class="text-medium-emphasis small">{{ fmtDate(doc.completed_at) }}</CTableDataCell>
                <CTableDataCell class="text-center" @click.stop>
                  <CDropdown variant="btn-group">
                    <CDropdownToggle color="secondary" variant="outline" size="sm" caret>···</CDropdownToggle>
                    <CDropdownMenu>
                      <CDropdownItem @click="router.push(`/approval/${doc.id}`)">상세 보기</CDropdownItem>
                      <CDropdownItem
                        v-if="doc.status === 'draft' || doc.status === 'rejected'"
                        @click="router.push(`/approval/${doc.id}/edit`)"
                      >
                        수정
                      </CDropdownItem>
                      <CDropdownItem
                        v-if="doc.status === 'draft' || doc.status === 'rejected'"
                        @click="confirmSubmit(doc.id)"
                      >
                        상신
                      </CDropdownItem>
                      <CDropdownItem
                        v-if="doc.pdf_url"
                        :href="doc.pdf_url"
                        target="_blank"
                      >
                        PDF 다운로드
                      </CDropdownItem>
                      <CDropdownDivider v-if="doc.status !== 'approved'" />
                      <CDropdownItem
                        v-if="doc.status !== 'approved'"
                        class="text-danger"
                        @click="confirmCancel(doc.id)"
                      >
                        취소
                      </CDropdownItem>
                    </CDropdownMenu>
                  </CDropdown>
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApproval } from '@/store/pinia/approval'
import type { DocumentStatus } from '@/store/types/approval'

const router = useRouter()
const store = useApproval()
const { draftedList, fetchMyDrafted, submitDocument, cancelDocument } = store

const fmtDate = (d: string | null) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('ko-KR')
}

const statusLabel = (s: DocumentStatus) => {
  const m: Record<DocumentStatus, string> = {
    draft: '임시저장', pending: '결재중', approved: '승인', rejected: '반려', cancelled: '취소',
  }
  return m[s] ?? s
}

const statusColor = (s: DocumentStatus) => {
  const m: Record<DocumentStatus, string> = {
    draft: 'secondary', pending: 'warning', approved: 'success', rejected: 'danger', cancelled: 'dark',
  }
  return m[s] ?? 'secondary'
}

const confirmSubmit = async (id: number) => {
  if (confirm('상신하시겠습니까? 상신 후에는 수정할 수 없습니다.')) {
    await submitDocument(id)
  }
}

const confirmCancel = async (id: number) => {
  if (confirm('결재를 취소하시겠습니까?')) {
    await cancelDocument(id)
  }
}

onMounted(fetchMyDrafted)
</script>
