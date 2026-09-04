<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import type { OfficialLetter } from '@/store/types/docs'
import type { LetterFilter } from '@/store/pinia/docs'
import { useDocs } from '@/store/pinia/docs'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import { usePerms } from '@/composables/usePerms.ts'

const props = defineProps<{
  letter: OfficialLetter | null
  viewRoute: string
  letterFilter: LetterFilter
}>()

const emit = defineEmits<{
  onDelete: [pk: number]
  generatePdf: [pk: number]
}>()

const { can, PERM } = usePerms()
const canDocsCreate = computed(() => can(PERM.DOCS_CREATE))
const canDocsUpdate = computed(() => can(PERM.DOCS_UPDATE))
const canDocsDelete = computed(() => can(PERM.DOCS_DELETE))

const router = useRouter()
const docStore = useDocs()

const showDeleteModal = ref(false)
const pdfLoading = ref(false)

const letterNav = computed(() => docStore.getLetterNav)

const prevPk = computed(() => {
  const nav = letterNav.value.find(n => n.pk === props.letter?.pk)
  return nav?.prev_pk
})

const nextPk = computed(() => {
  const nav = letterNav.value.find(n => n.pk === props.letter?.pk)
  return nav?.next_pk
})

const goToList = () => {
  router.push({ name: props.viewRoute })
}

const goToEdit = () => {
  if (props.letter?.pk) {
    router.push({ name: `${props.viewRoute} - 수정`, params: { letterId: props.letter.pk } })
  }
}

const goToPrev = () => {
  if (prevPk.value) {
    router.push({ name: `${props.viewRoute} - 보기`, params: { letterId: prevPk.value } })
  }
}

const goToNext = () => {
  if (nextPk.value) {
    router.push({ name: `${props.viewRoute} - 보기`, params: { letterId: nextPk.value } })
  }
}

const confirmDelete = () => {
  showDeleteModal.value = true
}

const onDelete = () => {
  if (props.letter?.pk) {
    emit('onDelete', props.letter.pk)
  }
  showDeleteModal.value = false
}

const onGeneratePdf = async () => {
  if (props.letter?.pk) {
    pdfLoading.value = true
    try {
      emit('generatePdf', props.letter.pk)
    } finally {
      pdfLoading.value = false
    }
  }
}

const downloadPdf = () => {
  if (props.letter?.pdf_file) {
    window.open(props.letter.pdf_file, '_blank')
  }
}

const approvalLoading = ref(false)

const onSubmitApproval = async () => {
  if (props.letter?.pk) {
    approvalLoading.value = true
    try {
      await docStore.submitApproval(props.letter.pk)
    } finally {
      approvalLoading.value = false
    }
  }
}

const goToApprovalDetail = (docId: number) => {
  router.push({ name: '결재 문서함 - 보기', params: { docId } })
}

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

const formatDateTime = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return dateStr.replace('T', ' ').substring(0, 19)
}
</script>

<template>
  <div v-if="letter">
    <!-- Navigation -->
    <CRow class="mb-3">
      <CCol class="d-flex justify-content-between align-items-center">
        <CButton color="secondary" variant="outline" size="sm" @click="goToList">
          <CIcon name="cilList" class="me-1" />
          목록
        </CButton>
        <div>
          <CButton color="light" size="sm" class="me-1" :disabled="!prevPk" @click="goToPrev">
            <CIcon name="cilChevronLeft" />
            이전
          </CButton>
          <CButton color="light" size="sm" :disabled="!nextPk" @click="goToNext">
            다음
            <CIcon name="cilChevronRight" />
          </CButton>
        </div>
      </CCol>
    </CRow>

    <!-- Approval Integration Banner -->
    <CCard class="mb-4 border-primary">
      <CCardBody class="d-flex justify-content-between align-items-center py-2 px-3">
        <div class="d-flex align-items-center">
          <CIcon name="cilShieldAlt" size="lg" class="text-primary me-2" />
          <div>
            <strong>전자결재 연동 상태: </strong>
            <CBadge v-if="letter.approval_status === 'approved'" color="success" class="ms-1">
              결재 승인완료 ({{ letter.approval_document_detail?.doc_number || '공문' }})
            </CBadge>
            <CBadge v-else-if="letter.approval_status === 'pending'" color="warning" class="ms-1">
              결재 진행중
            </CBadge>
            <CBadge v-else-if="letter.approval_status === 'rejected'" color="danger" class="ms-1">
              결재 반려
            </CBadge>
            <CBadge v-else color="secondary" class="ms-1">
              미상신 (임시/초안)
            </CBadge>
          </div>
        </div>
        <div>
          <CButton
            v-if="letter.approval_document"
            color="info"
            variant="outline"
            size="sm"
            class="me-2"
            @click="goToApprovalDetail(letter.approval_document)"
          >
            <CIcon name="cilExternalLink" class="me-1" />
            결재 문서 보기
          </CButton>
          <CButton
            v-if="letter.approval_status === 'none' || letter.approval_status === 'rejected'"
            color="primary"
            size="sm"
            :disabled="approvalLoading"
            @click="onSubmitApproval"
          >
            <CSpinner v-if="approvalLoading" size="sm" class="me-1" />
            <CIcon v-else name="cilPaperPlane" class="me-1" />
            {{ letter.approval_status === 'rejected' ? '전자결재 재상신' : '전자결재 상신하기' }}
          </CButton>
        </div>
      </CCardBody>
    </CCard>

    <!-- Letter Header -->
    <CCard class="mb-4">
      <CCardHeader class="d-flex justify-content-between align-items-center">
        <div>
          <CBadge color="primary" class="me-2">{{ letter.document_number }}</CBadge>
          <strong>{{ letter.title }}</strong>
        </div>
        <div>
          <small class="text-muted">
            작성자: {{ letter.creator?.username || '-' }} | 작성일:
            {{ formatDateTime(letter.created) }}
          </small>
        </div>
      </CCardHeader>
    </CCard>

    <!-- Letter Info -->
    <CRow>
      <CCol md="6">
        <CCard class="mb-4">
          <CCardHeader>
            <strong>수신처 정보</strong>
          </CCardHeader>
          <CCardBody>
            <table class="table table-borderless mb-0">
              <tbody>
                <tr>
                  <th style="width: 100px">수신처명</th>
                  <td>{{ letter.recipient_name }}</td>
                </tr>
                <tr v-if="letter.recipient_reference">
                  <th>참조</th>
                  <td>{{ letter.recipient_reference }}</td>
                </tr>
                <tr v-if="letter.recipient_address">
                  <th>주소</th>
                  <td>{{ letter.recipient_address }}</td>
                </tr>
                <tr v-if="letter.recipient_contact">
                  <th>연락처</th>
                  <td>{{ letter.recipient_contact }}</td>
                </tr>
              </tbody>
            </table>
          </CCardBody>
        </CCard>
      </CCol>

      <CCol md="6">
        <CCard class="mb-4">
          <CCardHeader>
            <strong>발신자 정보</strong>
          </CCardHeader>
          <CCardBody>
            <table class="table table-borderless mb-0">
              <tbody>
                <tr>
                  <th style="width: 100px">발신자명</th>
                  <td>{{ letter.sender_name }}</td>
                </tr>
                <tr v-if="letter.sender_position">
                  <th>직위</th>
                  <td>{{ letter.sender_position }}</td>
                </tr>
                <tr v-if="letter.sender_department">
                  <th>부서</th>
                  <td>{{ letter.sender_department }}</td>
                </tr>
                <tr>
                  <th>발신일자</th>
                  <td>{{ formatDate(letter.issue_date) }}</td>
                </tr>
                <tr v-if="letter.seal_detail">
                  <th>날인인감</th>
                  <td>
                    <div class="d-flex align-items-center">
                      <span class="me-2">{{ letter.seal_detail.name }} ({{ letter.seal_detail.seal_type_desc }})</span>
                      <img
                        v-if="letter.seal_detail.seal_image"
                        :src="letter.seal_detail.seal_image"
                        alt="인장"
                        style="width: 28px; height: 28px; object-fit: contain;"
                        class="border rounded p-1 bg-white"
                      />
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>

    <!-- Letter Content -->
    <CCard class="mb-4">
      <CCardHeader>
        <strong>공문 내용</strong>
      </CCardHeader>
      <CCardBody>
        <div class="letter-content" style="white-space: pre-wrap; line-height: 1.8">
          {{ letter.content }}
        </div>
      </CCardBody>
    </CCard>

    <!-- PDF Section -->
    <CCard class="mb-4">
      <CCardHeader>
        <strong>PDF 파일</strong>
      </CCardHeader>
      <CCardBody>
        <div v-if="letter.pdf_file" class="d-flex align-items-center">
          <CBadge color="success" class="me-3">
            <CIcon name="cilFile" class="me-1" />
            PDF 생성됨
          </CBadge>
          <CButton color="primary" size="sm" @click="downloadPdf">
            <CIcon name="cilCloudDownload" class="me-1" />
            다운로드
          </CButton>
          <CButton
            v-if="canDocsCreate"
            color="warning"
            size="sm"
            class="ms-2"
            :disabled="pdfLoading"
            @click="onGeneratePdf"
          >
            <CSpinner v-if="pdfLoading" size="sm" class="me-1" />
            <CIcon v-else name="cilReload" class="me-1" />
            재생성
          </CButton>
        </div>
        <div v-else>
          <span class="text-muted me-3">PDF 파일이 아직 생성되지 않았습니다.</span>
          <CButton
            v-if="canDocsCreate"
            color="primary"
            size="sm"
            :disabled="pdfLoading"
            @click="onGeneratePdf"
          >
            <CSpinner v-if="pdfLoading" size="sm" class="me-1" />
            <CIcon v-else name="cilFile" class="me-1" />
            PDF 생성
          </CButton>
        </div>
      </CCardBody>
    </CCard>

    <!-- Action Buttons -->
    <CRow>
      <CCol class="d-flex justify-content-between">
        <CButton color="secondary" variant="outline" @click="goToList">
          <CIcon name="cilList" class="me-1" />
          목록으로
        </CButton>
        <div>
          <CButton
            v-if="canDocsDelete"
            color="danger"
            variant="outline"
            class="me-2"
            @click="confirmDelete"
          >
            <CIcon name="cilTrash" class="me-1" />
            삭제
          </CButton>
          <CButton v-if="canDocsUpdate" color="primary" @click="goToEdit">
            <CIcon name="cilPencil" class="me-1" />
            수정
          </CButton>
        </div>
      </CCol>
    </CRow>

    <!-- Delete Confirm Modal -->
    <ConfirmModal v-model="showDeleteModal" @confirmed="onDelete">
      <template #header>공문 삭제</template>
      <template #default>
        <p>이 공문을 삭제하시겠습니까?</p>
        <p class="text-muted mb-0">
          <small>문서번호: {{ letter.document_number }}</small
          ><br />
          <small>제목: {{ letter.title }}</small>
        </p>
      </template>
    </ConfirmModal>
  </div>

  <div v-else class="text-center py-5">
    <CSpinner color="primary" />
    <p class="mt-3 text-muted">공문 정보를 불러오는 중...</p>
  </div>
</template>

<style scoped>
.letter-content {
  min-height: 200px;
  padding: 1rem;
  background-color: #fafafa;
  border-radius: 4px;
}
</style>
