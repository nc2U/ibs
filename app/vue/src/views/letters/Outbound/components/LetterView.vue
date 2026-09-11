<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import type { OfficialLetter } from '@/store/types/docs'
import type { LetterFilter } from '@/store/pinia/docs'
import { useDocs } from '@/store/pinia/docs'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import { usePerms } from '@/composables/usePerms.ts'

import { useAccount } from '@/store/pinia/account'

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
const accStore = useAccount()

const showDeleteModal = ref(false)
const pdfLoading = ref(false)
const scanUploadLoading = ref(false)
const scanFileInputRef = ref<HTMLInputElement | null>(null)

// 발송완료 여부
const isDispatched = computed(() => !!props.letter?.dispatched_at)

// 결재완료 여부
const isApproved = computed(() => props.letter?.approval_status === 'approved')

// 관리자 여부 (슈퍼유저 또는 work_manager)
const isManager = computed(() => {
  return !!accStore.superAuth || !!accStore.workManager
})

// 재생성 가능 여부:
// 1. 발송 완료된 경우: 자료 유실/변조 방지를 위해 슈퍼유저 포함 무조건 전면 금지
// 2. 결재 승인 완료된 경우: 관리자만 가능
// 3. 그 외: docs.create 권한자 가능
const canRegeneratePdf = computed(() => {
  if (isDispatched.value) return false
  if (!canDocsCreate.value) return false
  if (isApproved.value) return isManager.value
  return true
})

// 스캔본 업로드 가능 여부:
// 발송 완료된 공문은 관리자만 교체/등록 가능, 발송 전은 create 권한자 가능
const canUploadScan = computed(() => {
  if (!canDocsCreate.value) return false
  if (isDispatched.value) return isManager.value
  return true
})

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
    if (isDispatched.value) {
      alert('이미 대외 발송이 완료된 공문서는 자료 유실 및 변조 방지를 위해 PDF 재생성이 금지됩니다.')
      return
    }
    if (isApproved.value && !isManager.value) {
      alert('최종 결재 승인된 공문서는 관리자만 재생성할 수 있습니다.')
      return
    }
    pdfLoading.value = true
    try {
      emit('generatePdf', props.letter.pk)
    } finally {
      pdfLoading.value = false
    }
  }
}

const onScanFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0] && props.letter?.pk) {
    if (isDispatched.value && !isManager.value) {
      alert('이미 발송 완료된 공문의 스캔 파일 교체는 관리자만 가능합니다.')
      target.value = ''
      return
    }

    if (isDispatched.value) {
      if (!confirm('이미 발송 완료된 공문서입니다. 등록 시 기존 최종 발송본 파일이 대체됩니다. 계속하시겠습니까?')) {
        target.value = ''
        return
      }
    }

    const file = target.files[0]
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('PDF 파일(.pdf)만 등록 가능합니다.')
      target.value = ''
      return
    }
    scanUploadLoading.value = true
    try {
      await docStore.uploadLetterPdf(props.letter.pk, file)
    } finally {
      scanUploadLoading.value = false
      target.value = ''
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

const formatDate = (dateStr: string | null | undefined) => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

const formatDateTime = (dateStr: string | null | undefined) => {
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
            <CBadge v-else color="secondary" class="ms-1"> 미상신 (임시/초안) </CBadge>
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

    <!-- Letter Info (수신 & 발신/날인) -->
    <CRow>
      <CCol md="6">
        <CCard class="mb-4">
          <CCardHeader>
            <CIcon name="cilAddressBook" class="me-1" />
            <strong>수신 정보</strong>
          </CCardHeader>
          <CCardBody>
            <table class="table table-borderless mb-0">
              <tbody>
                <tr>
                  <th style="width: 100px">수신처명</th>
                  <td class="fw-bold">{{ letter.recipient_name }}</td>
                </tr>
                <tr>
                  <th>경유</th>
                  <td>{{ letter.via || '-' }}</td>
                </tr>
                <tr>
                  <th>참조</th>
                  <td>{{ letter.recipient_reference || '-' }}</td>
                </tr>
                <tr>
                  <th>공개구분</th>
                  <td>
                    <CBadge
                      :color="
                        letter.disclosure_type === '3'
                          ? 'danger'
                          : letter.disclosure_type === '2'
                            ? 'warning'
                            : 'success'
                      "
                    >
                      {{ letter.disclosure_type_desc || (letter.disclosure_type === '3' ? '비공개' : letter.disclosure_type === '2' ? '부분공개' : '공개') }}
                    </CBadge>
                  </td>
                </tr>
                <tr>
                  <th>시행(발신)일</th>
                  <td>
                    <span v-if="letter.dispatched_at" class="fw-bold text-success">
                      {{ formatDate(letter.effective_issue_date || letter.dispatched_at) }}
                      <CBadge color="success" class="ms-1">발송완료</CBadge>
                    </span>
                    <span v-else-if="letter.approval_status === 'approved'" class="fw-bold text-primary">
                      {{ formatDate(letter.effective_issue_date || letter.issue_date) }}
                      <CBadge color="primary" class="ms-1">승인확정</CBadge>
                    </span>
                    <span v-else class="text-secondary">
                      {{ formatDate(letter.issue_date) }}
                      <small class="text-muted ms-1">(발신 요청일)</small>
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </CCardBody>
        </CCard>
      </CCol>

      <CCol md="6">
        <CCard class="mb-4">
          <CCardHeader>
            <CIcon name="cilPen" class="me-1" />
            <strong>발신 및 날인 정보</strong>
          </CCardHeader>
          <CCardBody>
            <table class="table table-borderless mb-0">
              <tbody>
                <tr>
                  <th style="width: 100px">날인 인감</th>
                  <td>
                    <div v-if="letter.seal_detail" class="d-flex align-items-center">
                      <span class="me-2">{{ letter.seal_detail.name }} ({{ letter.seal_detail.seal_type_desc }})</span>
                      <img
                        v-if="letter.seal_detail.seal_image"
                        :src="letter.seal_detail.seal_image"
                        alt="인장"
                        style="width: 28px; height: 28px; object-fit: contain"
                        class="border rounded p-1 bg-white"
                      />
                    </div>
                    <span v-else class="text-muted">(직인생략 또는 미선택)</span>
                  </td>
                </tr>
                <tr>
                  <th>기안/담당자</th>
                  <td>
                    <span>{{ letter.drafter_name }} {{ letter.drafter_position ? `(${letter.drafter_position})` : '' }}</span>
                    <CBadge v-if="letter.is_solo_approval" color="info" class="ms-1">승인권자 직접기안</CBadge>
                  </td>
                </tr>
                <tr v-if="letter.sender_address">
                  <th>발신지주소</th>
                  <td>
                    <span v-if="letter.sender_zipcode">({{ letter.sender_zipcode }}) </span>
                    {{ letter.sender_address }}
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
        <CIcon name="cilDescription" class="me-1" />
        <strong>공문 본문</strong>
      </CCardHeader>
      <CCardBody>
        <div class="letter-content" style="white-space: pre-wrap; line-height: 1.8">
          {{ letter.content }}
        </div>
      </CCardBody>
    </CCard>

    <!-- Attachment Section (붙임 텍스트 및 첨부파일) -->
    <CCard class="mb-4">
      <CCardHeader>
        <CIcon name="cilPaperclip" class="me-1" />
        <strong>붙임 (첨부 서류 및 파일)</strong>
      </CCardHeader>
      <CCardBody>
        <div v-if="letter.attachment_text" class="mb-3 p-3 bg-light rounded border">
          <div class="fw-bold mb-1">인쇄용 붙임 목록:</div>
          <div style="white-space: pre-wrap">{{ letter.attachment_text }}</div>
        </div>

        <div v-if="letter.attachments && letter.attachments.length > 0">
          <div class="fw-bold mb-2">첨부 파일 목록:</div>
          <ul class="list-group">
            <li
              v-for="att in letter.attachments"
              :key="att.pk"
              class="list-group-item d-flex justify-content-between align-items-center"
            >
              <div>
                <CIcon name="cilFile" class="me-2 text-primary" />
                <strong>{{ att.name || att.file_name }}</strong>
                <span class="text-muted ms-2">({{ att.quantity || '1부' }})</span>
              </div>
              <a
                v-if="typeof att.file === 'string'"
                :href="att.file"
                target="_blank"
                class="btn btn-sm btn-outline-primary"
              >
                <CIcon name="cilCloudDownload" class="me-1" /> 다운로드
              </a>
            </li>
          </ul>
        </div>
        <div v-else-if="!letter.attachment_text" class="text-muted">
          등록된 붙임 서류나 첨부파일이 없습니다.
        </div>
      </CCardBody>
    </CCard>

    <!-- Dispatch Meta Section (발송 대장 관리 정보) -->
    <CCard class="mb-4 border-secondary">
      <CCardHeader class="bg-light">
        <CIcon name="cilTruck" class="me-1 text-secondary" />
        <strong>발송 및 대장 관리 메타 정보</strong>
      </CCardHeader>
      <CCardBody>
        <CRow>
          <CCol md="6">
            <table class="table table-borderless mb-0">
              <tbody>
                <tr>
                  <th style="width: 120px">발송 방법</th>
                  <td>
                    <CBadge color="dark">{{ letter.dispatch_method_desc || letter.dispatch_method || '이메일' }}</CBadge>
                  </td>
                </tr>
                <tr>
                  <th>등기/송장 번호</th>
                  <td>{{ letter.tracking_number || '-' }}</td>
                </tr>
                <tr>
                  <th>발송 완료일시</th>
                  <td>{{ formatDateTime(letter.dispatched_at) }}</td>
                </tr>
              </tbody>
            </table>
          </CCol>
          <CCol md="6">
            <table class="table table-borderless mb-0">
              <tbody>
                <tr>
                  <th style="width: 120px">우편 발송지</th>
                  <td>{{ letter.recipient_address || '-' }}</td>
                </tr>
                <tr>
                  <th>수신처 연락처</th>
                  <td>{{ letter.recipient_contact || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>

    <!-- PDF Section (최종 발송본 PDF 관리) -->
    <CCard class="mb-4">
      <CCardHeader class="d-flex justify-content-between align-items-center">
        <strong>
          <CIcon name="cilFile" class="me-1" />
          공문 PDF 파일 (최종 발송/보관본)
        </strong>
        <div>
          <CBadge v-if="isDispatched" color="dark">대외 발송완료 (재생성 금지)</CBadge>
          <CBadge v-else-if="isApproved" color="secondary">결재승인완료 (재생성 제한)</CBadge>
        </div>
      </CCardHeader>
      <CCardBody>
        <div v-if="letter.pdf_file" class="d-flex flex-wrap align-items-center justify-content-between gap-2">
          <div class="d-flex align-items-center">
            <CBadge color="success" class="me-3 p-2">
              <CIcon name="cilFile" class="me-1" />
              최종 PDF 등록됨
            </CBadge>
            <CButton color="primary" size="sm" @click="downloadPdf">
              <CIcon name="cilCloudDownload" class="me-1" />
              PDF 다운로드
            </CButton>
          </div>

          <!-- 작업 버튼 그룹: 스캔본 교체 업로드 & 시스템 재생성 -->
          <div class="d-flex align-items-center gap-2">
            <!-- 실물 날인 스캔본 직접 업로드 / 교체 (발송 후는 관리자만) -->
            <template v-if="canUploadScan">
              <input
                ref="scanFileInputRef"
                type="file"
                accept=".pdf"
                class="d-none"
                @change="onScanFileSelect"
              />
              <CButton
                color="info"
                variant="outline"
                size="sm"
                :disabled="scanUploadLoading"
                @click="scanFileInputRef?.click()"
              >
                <CSpinner v-if="scanUploadLoading" size="sm" class="me-1" />
                <CIcon v-else name="cilCloudUpload" class="me-1" />
                실물날인 스캔본(PDF) 업로드/교체
              </CButton>
            </template>
            <small v-else-if="isDispatched" class="text-muted">
              (발송 완료된 공문의 스캔본 교체는 관리자만 가능)
            </small>

            <!-- 시스템 양식 PDF 재생성 (발송 완료 시 무조건 금지, 결재 승인 시 관리자만) -->
            <CButton
              v-if="canRegeneratePdf"
              color="warning"
              variant="outline"
              size="sm"
              :disabled="pdfLoading"
              @click="onGeneratePdf"
            >
              <CSpinner v-if="pdfLoading" size="sm" class="me-1" />
              <CIcon v-else name="cilReload" class="me-1" />
              시스템 PDF 재생성
            </CButton>
            <small v-else-if="isDispatched" class="text-muted ms-1">
              (발송 완료되어 증빙 보호를 위해 PDF 재생성 불가)
            </small>
            <small v-else-if="isApproved" class="text-muted ms-1">
              (최종 결재 승인되어 관리자만 시스템 PDF 재생성 가능)
            </small>
          </div>
        </div>

        <!-- PDF 미생성 상태 -->
        <div v-else class="d-flex flex-wrap align-items-center justify-content-between gap-2">
          <span class="text-muted">PDF 파일이 아직 생성되거나 등록되지 않았습니다.</span>
          <div class="d-flex align-items-center gap-2">
            <!-- 직접 스캔본 업로드 -->
            <input
              ref="scanFileInputRef"
              type="file"
              accept=".pdf"
              class="d-none"
              @change="onScanFileSelect"
            />
            <CButton
              v-if="canDocsCreate"
              color="info"
              variant="outline"
              size="sm"
              :disabled="scanUploadLoading"
              @click="scanFileInputRef?.click()"
            >
              <CSpinner v-if="scanUploadLoading" size="sm" class="me-1" />
              <CIcon v-else name="cilCloudUpload" class="me-1" />
              스캔본(PDF) 직접 업로드
            </CButton>

            <!-- 시스템 PDF 생성 -->
            <CButton
              v-if="canDocsCreate"
              color="primary"
              size="sm"
              :disabled="pdfLoading"
              @click="onGeneratePdf"
            >
              <CSpinner v-if="pdfLoading" size="sm" class="me-1" />
              <CIcon v-else name="cilFile" class="me-1" />
              시스템 양식 PDF 생성
            </CButton>
          </div>
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
