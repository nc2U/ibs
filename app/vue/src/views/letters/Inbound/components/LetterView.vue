<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import type { InboundLetter } from '@/store/types/docs'
import type { InboundLetterFilter } from '@/store/pinia/docs'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps<{
  letter: InboundLetter | null
  viewRoute: string
  letterFilter: InboundLetterFilter
}>()

const emit = defineEmits<{
  onDelete: [pk: number]
  onStatusChange: [pk: number, status: string]
}>()

const { can, PERM } = usePerms()
const canDocsUpdate = computed(() => can(PERM.DOCS_UPDATE))
const canDocsDelete = computed(() => can(PERM.DOCS_DELETE))

const router = useRouter()

const showDeleteModal = ref(false)

const formatDate = (dateStr: string | undefined | null) => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

const formatDateTime = (dateTimeStr: string | undefined | null) => {
  if (!dateTimeStr) return '-'
  return dateTimeStr.substring(0, 16).replace('T', ' ')
}

const getDDayBadgeColor = (dDay: number | null | undefined) => {
  if (dDay === null || dDay === undefined) return 'secondary'
  if (dDay < 0) return 'danger'
  if (dDay === 0) return 'warning'
  if (dDay <= 3) return 'danger'
  if (dDay <= 7) return 'warning'
  return 'info'
}

const getDDayText = (dDay: number | null | undefined) => {
  if (dDay === null || dDay === undefined) return ''
  if (dDay < 0) return `기한초과 (D+${Math.abs(dDay)})`
  if (dDay === 0) return '오늘 마감 (D-Day)'
  return `${dDay}일 남음 (D-${dDay})`
}

const scanFileExt = computed(() => {
  if (!props.letter?.scan_file) return ''
  const cleanUrl = props.letter.scan_file.split('?')[0].split('#')[0]
  const parts = cleanUrl.split('.')
  return parts.length > 1 ? parts.pop()!.toLowerCase() : ''
})

const isScanPdf = computed(() => scanFileExt.value === 'pdf')
const isScanHwp = computed(() => ['hwp', 'hwpx'].includes(scanFileExt.value))
const isScanImage = computed(() =>
  ['jpg', 'jpeg', 'png', 'gif', 'webp', 'tif', 'tiff'].includes(scanFileExt.value),
)

const scanFileName = computed(() => {
  if (!props.letter?.scan_file) return ''
  const cleanUrl = props.letter.scan_file.split('?')[0].split('#')[0]
  return decodeURIComponent(cleanUrl.split('/').pop() || '')
})

const goToList = () => {
  router.push({ name: props.viewRoute })
}

const goToEdit = () => {
  if (props.letter?.pk) {
    router.push({
      name: `${props.viewRoute} - 수정`,
      params: { letterId: props.letter.pk },
    })
  }
}

const goToPrev = () => {
  if (props.letter?.prev_pk) {
    router.push({
      name: `${props.viewRoute} - 보기`,
      params: { letterId: props.letter.prev_pk },
    })
  }
}

const goToNext = () => {
  if (props.letter?.next_pk) {
    router.push({
      name: `${props.viewRoute} - 보기`,
      params: { letterId: props.letter.next_pk },
    })
  }
}

const handleDeleteConfirm = () => {
  if (props.letter?.pk) {
    emit('onDelete', props.letter.pk)
  }
  showDeleteModal.value = false
}

// 전자결재 품의 상신 연계
const goToApprovalDraft = () => {
  if (props.letter?.approval_document) {
    router.push({
      name: '전체 문서함 - 보기',
      params: { docId: props.letter.approval_document },
    })
    return
  }
  router.push({
    name: '기안 문서함 - 작성',
    query: {
      inbound_letter: props.letter?.pk,
      title: `[수신 공문 보고] ${props.letter?.title || ''}`,
    },
  })
}

// 회신 공문 작성 이동
const goToOutboundReply = () => {
  router.push({
    name: '발송 공문 관리 - 작성',
    query: {
      reply_to_inbound: props.letter?.pk,
      recipient_name: props.letter?.sender_name,
      title: `[회신] ${props.letter?.title || ''}`,
    },
  })
}

const updateStatus = (newStatus: string) => {
  if (props.letter?.pk) {
    emit('onStatusChange', props.letter.pk, newStatus)
  }
}
</script>

<template>
  <div v-if="letter" class="inbound-view">
    <!-- Top Action Bar -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div class="d-flex align-items-center gap-2">
        <CButton
          color="secondary"
          variant="outline"
          size="sm"
          :disabled="!letter.prev_pk"
          @click="goToPrev"
        >
          <v-icon icon="mdi-chevron-left" size="small" />
          이전
        </CButton>
        <CButton
          color="secondary"
          variant="outline"
          size="sm"
          :disabled="!letter.next_pk"
          @click="goToNext"
        >
          다음
          <v-icon icon="mdi-chevron-right" size="small" />
        </CButton>
      </div>

      <div class="d-flex align-items-center gap-2">
        <CButton
          v-if="canDocsUpdate"
          color="success"
          variant="outline"
          size="sm"
          :disabled="letter.status === 'closed'"
          @click="goToApprovalDraft"
        >
          <v-icon
            :icon="
              letter.approval_document
                ? 'mdi-file-document-check-outline'
                : 'mdi-file-document-edit-outline'
            "
            size="small"
            class="me-1"
          />
          {{ letter.approval_document ? '연동 품의서 확인' : '처리품의 상신' }}
        </CButton>
        <CButton
          v-if="canDocsUpdate"
          color="primary"
          variant="outline"
          size="sm"
          @click="goToOutboundReply"
        >
          <v-icon icon="mdi-reply" size="small" class="me-1" />
          회신 공문 작성
        </CButton>
        <CButton v-if="canDocsUpdate" color="primary" size="sm" @click="goToEdit">
          <v-icon icon="mdi-pencil" size="small" class="me-1" />
          수정
        </CButton>
        <CButton
          v-if="canDocsDelete"
          color="danger"
          variant="outline"
          size="sm"
          @click="showDeleteModal = true"
        >
          <v-icon icon="mdi-delete" size="small" class="me-1" />
          삭제
        </CButton>
        <CButton color="secondary" size="sm" @click="goToList">
          <v-icon icon="mdi-format-list-bulleted" size="small" class="me-1" />
          목록으로
        </CButton>
      </div>
    </div>

    <!-- Header Status Card -->
    <CCard class="mb-4 shadow-sm border-0 bg-light">
      <CCardBody class="p-4">
        <div class="d-flex justify-content-between align-items-start mb-2">
          <div>
            <div class="d-flex align-items-center gap-2 mb-1">
              <span class="badge bg-primary fs-6">{{ letter.receipt_number }}</span>
              <span class="text-muted small">발신처 문서번호: {{ letter.document_number }}</span>
            </div>
            <h3 class="fw-bold mb-1">{{ letter.title }}</h3>
            <div class="text-muted small">
              발신처: <strong>{{ letter.sender_name }}</strong>
              <span v-if="letter.sender_contact" class="ms-2 text-secondary">
                ({{ letter.sender_contact }})
              </span>
            </div>
          </div>
          <div class="text-end">
            <div class="d-flex align-items-center gap-2 justify-content-end mb-1">
              <CBadge v-if="letter.status === 'received'" color="info" class="fs-6">접수</CBadge>
              <CBadge v-else-if="letter.status === 'in_progress'" color="warning" class="fs-6"
                >처리중</CBadge
              >
              <CBadge v-else-if="letter.status === 'replied'" color="primary" class="fs-6"
                >회신완료</CBadge
              >
              <CBadge v-else-if="letter.status === 'closed'" color="secondary" class="fs-6"
                >종결</CBadge
              >
            </div>
            <CBadge
              v-if="letter.reply_due_date"
              :color="getDDayBadgeColor(letter.d_day)"
              class="fs-7"
            >
              <v-icon icon="mdi-clock-alert-outline" size="small" class="me-1" />
              회신기한: {{ formatDate(letter.reply_due_date) }} ({{ getDDayText(letter.d_day) }})
            </CBadge>
          </div>
        </div>

        <hr class="my-3 opacity-25" />

        <!-- 메타 정보 행 -->
        <CRow class="small text-muted g-2">
          <CCol md="3"> <strong>접수일자:</strong> {{ formatDate(letter.received_date) }} </CCol>
          <CCol md="3">
            <strong>배부 부서:</strong>
            <span class="badge bg-white text-dark border ms-1">
              {{ letter.recipient_dept_name || '미지정' }}
            </span>
          </CCol>
          <CCol md="3">
            <strong>처리 담당자:</strong> {{ letter.recipient_manager_name || '미지정' }}
          </CCol>
          <CCol md="3" class="text-end">
            <strong>등록일시:</strong> {{ formatDateTime(letter.created) }} ({{
              letter.creator?.username || '-'
            }})
          </CCol>
        </CRow>
      </CCardBody>
    </CCard>

    <!-- Main Content Layout -->
    <CRow>
      <!-- Left: 내용 요약 & 스캔 PDF 뷰어 -->
      <CCol lg="8">
        <!-- 요약 및 내용 -->
        <CCard class="mb-4">
          <CCardHeader class="bg-light fw-semibold">
            <CIcon name="cilAlignLeft" class="me-1" />
            공문 주요 내용 및 요약
          </CCardHeader>
          <CCardBody>
            <div
              v-if="letter.content"
              style="white-space: pre-wrap; line-height: 1.8; min-height: 120px"
            >
              {{ letter.content }}
            </div>
            <div v-else class="text-muted py-4 text-center">등록된 본문 요약 내용이 없습니다.</div>
          </CCardBody>
        </CCard>

        <!-- 공문서 원본 스캔본 (PDF Preview) -->
        <CCard class="mb-4">
          <CCardHeader
            class="bg-light fw-semibold d-flex justify-content-between align-items-center"
          >
            <div>
              <v-icon
                :icon="
                  isScanPdf
                    ? 'mdi-file-pdf-box'
                    : isScanHwp
                      ? 'mdi-file-document-outline'
                      : isScanImage
                        ? 'mdi-file-image'
                        : 'mdi-file-document'
                "
                :class="isScanPdf ? 'text-danger' : isScanHwp ? 'text-primary' : 'text-secondary'"
                class="me-1"
              />
              공문서 원본 파일
              <CBadge v-if="scanFileExt" color="info" class="ms-1 text-uppercase">
                {{ scanFileExt }}
              </CBadge>
            </div>
            <a
              v-if="letter.scan_file"
              :href="letter.scan_file"
              target="_blank"
              download
              class="btn btn-sm btn-outline-primary"
            >
              <v-icon icon="mdi-download" size="small" class="me-1" />
              원본 파일 다운로드
            </a>
          </CCardHeader>
          <CCardBody class="p-0">
            <!-- 1. PDF 파일: 인라인 뷰어 -->
            <div v-if="letter.scan_file && isScanPdf" style="height: 680px; width: 100%">
              <iframe
                :src="`${letter.scan_file}#toolbar=1&navpanes=0`"
                width="100%"
                height="100%"
                style="border: none"
              />
            </div>

            <!-- 2. 한글 파일 (HWP / HWPX): 관공서 공문 배너 및 바로 열기/다운로드 안내 -->
            <div
              v-else-if="letter.scan_file && isScanHwp"
              class="py-5 px-4 text-center bg-light d-flex flex-column align-items-center justify-content-center"
              style="min-height: 400px"
            >
              <v-icon icon="mdi-file-document-outline" size="64" class="text-primary mb-3" />
              <h5 class="fw-bold mb-1">한글 공문서 원본 파일 (.{{ scanFileExt }})</h5>
              <p class="text-muted small mb-3 text-truncate" style="max-width: 480px">
                {{ scanFileName }}
              </p>
              <CAlert color="info" class="text-start small py-2 px-3 mb-4" style="max-width: 520px">
                <v-icon icon="mdi-information-outline" class="me-1" />
                관공서 및 공공기관의 한글(HWP/HWPX) 공문서 원본입니다. 보안 및 수정제한이 걸려 있을
                수 있으므로 다운로드 후 한컴오피스 또는 공공서식 한글 뷰어로 열람하세요.
              </CAlert>
              <div class="d-flex gap-2">
                <a :href="letter.scan_file" target="_blank" download class="btn btn-primary px-4">
                  <v-icon icon="mdi-download" class="me-1" />
                  한글 파일 다운로드 / 열기
                </a>
              </div>
            </div>

            <!-- 3. 이미지 파일 (JPG/PNG 등): 인라인 이미지 뷰어 -->
            <div
              v-else-if="letter.scan_file && isScanImage"
              class="p-3 text-center bg-light overflow-auto"
              style="max-height: 680px"
            >
              <img
                :src="letter.scan_file"
                alt="공문서 원본 이미지"
                class="img-fluid border shadow-sm rounded"
                style="max-width: 100%"
              />
            </div>

            <!-- 4. 기타 파일 형식 -->
            <div
              v-else-if="letter.scan_file"
              class="py-5 px-4 text-center bg-light d-flex flex-column align-items-center justify-content-center"
              style="min-height: 350px"
            >
              <v-icon icon="mdi-file-document" size="64" class="text-secondary mb-3" />
              <h5 class="fw-bold mb-1">
                공문서 원본 파일 ({{ scanFileExt ? '.' + scanFileExt : '등록됨' }})
              </h5>
              <p class="text-muted small mb-3 text-truncate" style="max-width: 480px">
                {{ scanFileName }}
              </p>
              <a
                :href="letter.scan_file"
                target="_blank"
                download
                class="btn btn-outline-primary px-4"
              >
                <v-icon icon="mdi-download" class="me-1" />
                파일 다운로드
              </a>
            </div>

            <!-- 5. 파일 미등록 시 -->
            <div v-else class="py-5 text-center text-muted">
              <v-icon
                icon="mdi-file-document-outline"
                size="48"
                class="opacity-25 mb-2 text-primary"
              />
              <div>등록된 공문서 원본 파일이 없습니다.</div>
              <small>공문서 원본 파일(PDF, HWP, HWPX, 이미지 등)을 등록할 수 있습니다.</small>
            </div>
          </CCardBody>
        </CCard>
      </CCol>

      <!-- Right: 첨부파일 & 후속조치 패널 -->
      <CCol lg="4">
        <!-- 붙임 및 동봉 첨부파일 -->
        <CCard class="mb-4">
          <CCardHeader class="bg-light fw-semibold">
            <v-icon icon="mdi-paperclip" size="small" class="me-1" />
            동봉 / 붙임 첨부파일 ({{ letter.attachments?.length || 0 }})
          </CCardHeader>
          <CCardBody class="p-0">
            <ul
              v-if="letter.attachments && letter.attachments.length > 0"
              class="list-group list-group-flush"
            >
              <li
                v-for="att in letter.attachments"
                :key="att.pk"
                class="list-group-item d-flex justify-content-between align-items-center py-2 px-3"
              >
                <div class="text-truncate me-2">
                  <div class="small fw-semibold text-truncate">
                    {{ att.name || att.file_name }}
                  </div>
                  <small class="text-muted">
                    {{ att.quantity }}
                    <span v-if="att.file_size" class="ms-1">
                      ({{ (att.file_size / 1024).toFixed(1) }} KB)
                    </span>
                  </small>
                </div>
                <a
                  :href="att.file as string"
                  target="_blank"
                  download
                  class="btn btn-sm btn-ghost-primary"
                >
                  <v-icon icon="mdi-download" size="small" />
                </a>
              </li>
            </ul>
            <div v-else class="text-center text-muted py-4 small">동봉된 첨부파일이 없습니다.</div>
          </CCardBody>
        </CCard>

        <!-- 처리 상태 간편 전환 패널 -->
        <CCard class="mb-4">
          <CCardHeader class="bg-light fw-semibold">
            <v-icon icon="mdi-progress-check" size="small" class="me-1" />
            상태 간편 변경
          </CCardHeader>
          <CCardBody>
            <div class="d-grid gap-2">
              <CButton
                color="info"
                :variant="letter.status === 'received' ? undefined : 'outline'"
                size="sm"
                class="text-start"
                @click="updateStatus('received')"
              >
                <v-icon icon="mdi-inbox-arrow-down" size="small" class="me-1" />
                1. 접수 (초기 등록)
              </CButton>
              <CButton
                color="warning"
                :variant="letter.status === 'in_progress' ? undefined : 'outline'"
                size="sm"
                class="text-start"
                @click="updateStatus('in_progress')"
              >
                <v-icon icon="mdi-clock-outline" size="small" class="me-1" />
                2. 처리중 (검토 / 품의 진행)
              </CButton>
              <CButton
                color="primary"
                :variant="letter.status === 'replied' ? undefined : 'outline'"
                size="sm"
                class="text-start"
                @click="updateStatus('replied')"
              >
                <v-icon icon="mdi-reply" size="small" class="me-1" />
                3. 회신완료 (대외 답변 발송)
              </CButton>
              <CButton
                color="secondary"
                :variant="letter.status === 'closed' ? undefined : 'outline'"
                size="sm"
                class="text-start"
                @click="updateStatus('closed')"
              >
                <v-icon icon="mdi-check-circle-outline" size="small" class="me-1" />
                4. 종결 (처리 완료 / 보관)
              </CButton>
            </div>
          </CCardBody>
        </CCard>

        <!-- 연동 전자결재 품의 정보 -->
        <CCard v-if="letter.approval_document_detail" class="mb-4 border-success">
          <CCardHeader class="bg-success text-white fw-semibold">
            <v-icon icon="mdi-check-decagram" size="small" class="me-1" />
            연동 전자결재 품의
          </CCardHeader>
          <CCardBody class="small">
            <div class="mb-1 fw-bold text-truncate">
              {{ letter.approval_document_detail.title }}
            </div>
            <div class="text-muted mb-2">
              문서번호: {{ letter.approval_document_detail.doc_number || '-' }}
            </div>
            <div class="d-flex justify-content-between align-items-center">
              <span class="badge bg-light text-dark border">
                {{ letter.approval_document_detail.status_desc }}
              </span>
              <router-link
                :to="{
                  name: '전체 문서함 - 보기',
                  params: { docId: letter.approval_document_detail.pk },
                }"
                class="btn btn-sm btn-outline-success"
              >
                품의서 열기
              </router-link>
            </div>
          </CCardBody>
        </CCard>

        <!-- 연동 발송(회신) 공문 정보 -->
        <CCard
          v-if="letter.reply_letters && letter.reply_letters.length > 0"
          class="mb-4 border-primary"
        >
          <CCardHeader class="bg-primary text-white fw-semibold">
            <v-icon icon="mdi-reply-all" size="small" class="me-1" />
            연동 발송(회신) 공문 ({{ letter.reply_letters.length }})
          </CCardHeader>
          <CCardBody class="p-0 small">
            <ul class="list-group list-group-flush">
              <li
                v-for="reply in letter.reply_letters"
                :key="reply.pk"
                class="list-group-item d-flex justify-content-between align-items-center py-2 px-3"
              >
                <div class="text-truncate me-2">
                  <div class="fw-semibold text-truncate">{{ reply.title }}</div>
                  <small class="text-muted">
                    {{ reply.document_number || '문서번호 미발번' }}
                    <span v-if="reply.dispatched_at" class="ms-1 text-success">
                      • 발송완료 ({{ formatDate(reply.dispatched_at) }})
                    </span>
                    <span v-else class="ms-1 text-secondary">
                      • {{ reply.approval_status_desc || '결재 미완료' }}
                    </span>
                  </small>
                </div>
                <router-link
                  :to="{ name: '발송 공문 관리 - 보기', params: { letterId: reply.pk } }"
                  class="btn btn-sm btn-outline-primary"
                >
                  보기
                </router-link>
              </li>
            </ul>
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>

    <!-- Bottom Action Bar -->
    <div class="d-flex justify-content-end mt-4">
      <CButton color="secondary" @click="goToList">
        <v-icon icon="mdi-format-list-bulleted" size="small" class="me-1" />
        목록으로
      </CButton>
    </div>

    <!-- Delete Confirm Modal -->
    <ConfirmModal
      v-model="showDeleteModal"
      title="수신 공문 삭제"
      message="이 수신 공문 데이터를 삭제하시겠습니까? 첨부된 파일과 스캔본도 함께 삭제됩니다."
      @confirm="handleDeleteConfirm"
    />
  </div>
</template>

<style scoped>
.inbound-view {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
