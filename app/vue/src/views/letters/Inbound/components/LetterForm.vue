<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDocs } from '@/store/pinia/docs'
import type { InboundLetter } from '@/store/types/docs'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps<{
  company: number
  letter?: InboundLetter
  viewRoute: string
  departments: { value: number; label: string }[]
  staffs: { value: number; label: string }[]
}>()

export interface LocalAttachmentItem {
  file: File
  name: string
  quantity: string
}

const emit = defineEmits<{
  onSubmit: [payload: FormData, attachmentsToUpload?: LocalAttachmentItem[], pk?: number]
}>()

const router = useRouter()
const docStore = useDocs()

const form = ref<{
  receipt_number: string
  document_number: string
  sender_name: string
  sender_contact: string
  received_date: string
  reply_due_date: string
  title: string
  content: string
  recipient_dept: number | null
  recipient_manager: number | null
  status: 'received' | 'in_progress' | 'replied' | 'closed'
}>({
  receipt_number: '',
  document_number: '',
  sender_name: '',
  sender_contact: '',
  received_date: new Date().toISOString().substring(0, 10),
  reply_due_date: '',
  title: '',
  content: '',
  recipient_dept: null,
  recipient_manager: null,
  status: 'received',
})

const scanFile = ref<File | null>(null)
const scanFileName = ref('')
const existingScanFile = ref<string | null>(null)

// 첨부파일 관리
const existingAttachments = ref<any[]>([])
const newAttachments = ref<LocalAttachmentItem[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const scanFileInput = ref<HTMLInputElement | null>(null)

// 확인 모달
const showConfirmModal = ref(false)
const confirmMessage = ref('')
const confirmCallback = ref<(() => void) | null>(null)

const isEdit = computed(() => !!props.letter?.pk)

// 다음 접수번호 자동 조회 (신규 등록 시)
const fetchNextReceiptNumber = async () => {
  if (!isEdit.value && props.company) {
    try {
      const nextNum = await docStore.getNextReceiptNumber(props.company)
      if (nextNum) {
        form.value.receipt_number = nextNum
      }
    } catch {
      // ignore
    }
  }
}

watch(
  () => props.letter,
  letter => {
    if (letter) {
      form.value = {
        receipt_number: letter.receipt_number || '',
        document_number: letter.document_number || '',
        sender_name: letter.sender_name || '',
        sender_contact: letter.sender_contact || '',
        received_date: letter.received_date || new Date().toISOString().substring(0, 10),
        reply_due_date: letter.reply_due_date || '',
        title: letter.title || '',
        content: letter.content || '',
        recipient_dept: letter.recipient_dept || null,
        recipient_manager: letter.recipient_manager || null,
        status: letter.status || 'received',
      }
      existingScanFile.value = letter.scan_file || null
      existingAttachments.value = letter.attachments ? [...letter.attachments] : []
    } else {
      fetchNextReceiptNumber()
    }
  },
  { immediate: true },
)

onMounted(() => {
  if (!isEdit.value) {
    fetchNextReceiptNumber()
  }
})

const onScanFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) {
    const file = target.files[0]
    scanFile.value = file
    scanFileName.value = file.name
  }
}

const removeScanFile = () => {
  scanFile.value = null
  scanFileName.value = ''
  if (scanFileInput.value) scanFileInput.value.value = ''
}

const onAttachmentAdd = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    for (let i = 0; i < target.files.length; i++) {
      const file = target.files[i]
      newAttachments.value.push({
        file,
        name: file.name,
        quantity: '1부',
      })
    }
    if (fileInput.value) fileInput.value.value = ''
  }
}

const removeNewAttachment = (index: number) => {
  newAttachments.value.splice(index, 1)
}

const removeExistingAttachment = async (pk: number) => {
  confirmMessage.value = '이 첨부파일을 삭제하시겠습니까?'
  confirmCallback.value = async () => {
    if (props.letter?.pk) {
      await docStore.deleteInboundAttachment(pk, props.letter.pk)
      existingAttachments.value = existingAttachments.value.filter(a => a.pk !== pk)
    }
  }
  showConfirmModal.value = true
}

const handleConfirm = () => {
  if (confirmCallback.value) confirmCallback.value()
  showConfirmModal.value = false
}

const goBack = () => {
  if (props.letter?.pk) {
    router.push({ name: `${props.viewRoute} - 보기`, params: { letterId: props.letter.pk } })
  } else {
    router.push({ name: props.viewRoute })
  }
}

const isSubmitting = ref(false)

const handleSubmit = () => {
  if (!form.value.document_number.trim()) {
    alert('발신처 문서번호를 입력해주세요.')
    return
  }
  if (!form.value.sender_name.trim()) {
    alert('발신처(기관/업체명)를 입력해주세요.')
    return
  }
  if (!form.value.title.trim()) {
    alert('수신 공문 제목을 입력해주세요.')
    return
  }
  if (!form.value.received_date) {
    alert('접수일자를 선택해주세요.')
    return
  }

  const formData = new FormData()
  formData.append('company', String(props.company))
  if (form.value.receipt_number) formData.append('receipt_number', form.value.receipt_number)
  formData.append('document_number', form.value.document_number)
  formData.append('sender_name', form.value.sender_name)
  formData.append('sender_contact', form.value.sender_contact || '')
  formData.append('received_date', form.value.received_date)
  if (form.value.reply_due_date) formData.append('reply_due_date', form.value.reply_due_date)
  formData.append('title', form.value.title)
  formData.append('content', form.value.content || '')
  if (form.value.recipient_dept)
    formData.append('recipient_dept', String(form.value.recipient_dept))
  if (form.value.recipient_manager)
    formData.append('recipient_manager', String(form.value.recipient_manager))
  formData.append('status', form.value.status)

  if (scanFile.value) {
    formData.append('scan_file', scanFile.value)
  }

  isSubmitting.value = true
  emit('onSubmit', formData, newAttachments.value, props.letter?.pk)
}
</script>

<template>
  <div class="letter-form">
    <!-- Action Bar -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h4 class="mb-1 font-weight-bold">
          {{ isEdit ? '수신 공문 수정' : '수신 공문 접수 등록' }}
        </h4>
        <span class="text-muted small">
          대외 기관 및 거래처로부터 접수된 공문서의 대장 정보와 원본 스캔본을 등록합니다.
        </span>
      </div>
      <div class="d-flex gap-2">
        <CButton color="secondary" variant="ghost" @click="goBack"> 취소 </CButton>
        <CButton color="primary" :disabled="isSubmitting" @click="handleSubmit">
          <v-icon icon="mdi-content-save" size="small" class="me-1" />
          {{ isEdit ? '수정 저장' : '접수 등록' }}
        </CButton>
      </div>
    </div>

    <!-- Main Form Grid -->
    <CRow>
      <CCol lg="8">
        <!-- 기본 접수 정보 -->
        <CCard class="mb-4">
          <CCardHeader class="bg-light fw-semibold">
            <CIcon name="cilEnvelopeClosed" class="me-1" />
            공문 기본 정보
          </CCardHeader>
          <CCardBody>
            <CRow class="mb-3">
              <CCol md="6">
                <CFormLabel>사내 접수번호</CFormLabel>
                <CFormInput
                  v-model="form.receipt_number"
                  placeholder="자동 생성 ([회사약칭]-접수-YYYY-NNN)"
                />
                <CFormText class="text-muted small">
                  직접 수정하거나 비워두시면 자동 생성 규칙에 따라 발번됩니다.
                </CFormText>
              </CCol>
              <CCol md="6">
                <CFormLabel>발신처 문서번호 <span class="text-danger">*</span></CFormLabel>
                <CFormInput
                  v-model="form.document_number"
                  placeholder="예: 서울시 제2026-1234호, 감리-26-05"
                  required
                />
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CCol md="6">
                <CFormLabel>발신처 (기관 / 업체명) <span class="text-danger">*</span></CFormLabel>
                <CFormInput
                  v-model="form.sender_name"
                  placeholder="예: 강남구청 건축과, (주)대한건설"
                  required
                />
              </CCol>
              <CCol md="6">
                <CFormLabel>발신처 연락처 / 담당자</CFormLabel>
                <CFormInput
                  v-model="form.sender_contact"
                  placeholder="예: 02-3423-1234 (주무관 홍길동)"
                />
              </CCol>
            </CRow>

            <CRow class="mb-3">
              <CCol md="6">
                <CFormLabel>접수일자 <span class="text-danger">*</span></CFormLabel>
                <DatePicker v-model="form.received_date" placeholder="접수일자 선택" />
              </CCol>
              <CCol md="6">
                <CFormLabel>회신기한 (답변 마감일)</CFormLabel>
                <DatePicker v-model="form.reply_due_date" placeholder="회신기한 선택 (선택)" />
                <CFormText class="text-muted small">
                  회신이 요구되는 공문인 경우 기한을 입력하면 D-Day 마감 알림이 연동됩니다.
                </CFormText>
              </CCol>
            </CRow>

            <div class="mb-3">
              <CFormLabel>수신 공문 제목 <span class="text-danger">*</span></CFormLabel>
              <CFormInput
                v-model="form.title"
                placeholder="공문서 상단 제목을 정확히 기재하세요"
                required
              />
            </div>

            <div class="mb-0">
              <CFormLabel>주요 요약 및 세부 내용</CFormLabel>
              <CFormTextarea
                v-model="form.content"
                rows="6"
                placeholder="수신된 공문의 핵심 요구사항, 배경 및 지시 내용을 요약 정리하세요."
              />
            </div>
          </CCardBody>
        </CCard>

        <!-- 원본 스캔본 & 첨부파일 업로드 -->
        <CCard class="mb-4">
          <CCardHeader class="bg-light fw-semibold">
            <v-icon icon="mdi-paperclip" size="small" class="me-1" />
            공문 원본 스캔 및 붙임 파일
          </CCardHeader>
          <CCardBody>
            <!-- 공문서 원본 파일 (PDF, HWP, HWPX, 이미지) -->
            <div class="mb-4 p-3 border rounded bg-light">
              <label class="form-label fw-bold d-block mb-1">
                <v-icon icon="mdi-file-document-outline" class="text-primary me-1" />
                공문서 원본 파일 (PDF, HWP, HWPX, 이미지 등)
              </label>
              <p class="text-muted small mb-2">
                실물 또는 전자 수신된 공식 공문서 원본 파일(PDF, 한글 HWP/HWPX, 스캔 이미지 등)을 등록하세요.
              </p>

              <div
                v-if="existingScanFile && !scanFile"
                class="d-flex align-items-center gap-2 mb-2"
              >
                <CBadge color="success">현재 등록됨</CBadge>
                <a
                  :href="existingScanFile"
                  target="_blank"
                  class="text-decoration-none small text-truncate"
                  style="max-width: 300px"
                >
                  원본 공문 파일 다운로드 / 열기
                </a>
              </div>

              <div class="d-flex gap-2 align-items-center">
                <input
                  ref="scanFileInput"
                  type="file"
                  accept=".pdf,.hwp,.hwpx,.jpg,.jpeg,.png,.tif,.tiff,application/pdf,application/x-hwp,application/haansofthwp,application/vnd.hancom.hwp,application/vnd.hancom.hwpx,image/*"
                  class="form-control"
                  @change="onScanFileChange"
                />
                <CButton
                  v-if="scanFile"
                  color="danger"
                  variant="outline"
                  size="sm"
                  @click="removeScanFile"
                >
                  취소
                </CButton>
              </div>
              <small v-if="scanFileName" class="text-primary mt-1 d-block">
                선택된 파일: {{ scanFileName }}
              </small>
            </div>

            <!-- 붙임 및 동봉 첨부파일 -->
            <div>
              <div class="d-flex justify-content-between align-items-center mb-2">
                <label class="form-label fw-bold mb-0">동봉 / 붙임 첨부파일</label>
                <div>
                  <input
                    ref="fileInput"
                    type="file"
                    multiple
                    class="d-none"
                    @change="onAttachmentAdd"
                  />
                  <CButton
                    color="secondary"
                    variant="outline"
                    size="sm"
                    @click="fileInput?.click()"
                  >
                    <v-icon icon="mdi-plus" size="small" class="me-1" />
                    파일 추가
                  </CButton>
                </div>
              </div>

              <!-- 기존 첨부 목록 -->
              <div v-if="existingAttachments.length > 0" class="mb-3">
                <small class="text-muted d-block mb-1">기존 등록 첨부:</small>
                <ul class="list-group">
                  <li
                    v-for="att in existingAttachments"
                    :key="att.pk"
                    class="list-group-item d-flex justify-content-between align-items-center py-2"
                  >
                    <div class="d-flex align-items-center gap-2">
                      <v-icon icon="mdi-file-outline" size="small" class="text-muted" />
                      <span class="small font-weight-medium">{{ att.name || att.file_name }}</span>
                      <span class="badge bg-light text-muted">{{ att.quantity }}</span>
                    </div>
                    <CButton
                      color="danger"
                      variant="ghost"
                      size="sm"
                      @click="removeExistingAttachment(att.pk)"
                    >
                      <v-icon icon="mdi-delete" size="small" />
                    </CButton>
                  </li>
                </ul>
              </div>

              <!-- 신규 추가 대기 첨부 목록 -->
              <div v-if="newAttachments.length > 0">
                <small class="text-muted d-block mb-1">새로 추가할 첨부:</small>
                <div
                  v-for="(att, idx) in newAttachments"
                  :key="idx"
                  class="d-flex gap-2 align-items-center mb-2"
                >
                  <CFormInput
                    v-model="att.name"
                    placeholder="붙임 명칭 (예: 사업계획서)"
                    size="sm"
                    style="flex: 2"
                  />
                  <CFormInput
                    v-model="att.quantity"
                    placeholder="수량 (예: 1부)"
                    size="sm"
                    style="flex: 1; max-width: 100px"
                  />
                  <span class="text-muted small text-truncate" style="flex: 2">
                    {{ att.file.name }}
                  </span>
                  <CButton
                    color="danger"
                    variant="ghost"
                    size="sm"
                    @click="removeNewAttachment(idx)"
                  >
                    <v-icon icon="mdi-close" size="small" />
                  </CButton>
                </div>
              </div>

              <div
                v-if="existingAttachments.length === 0 && newAttachments.length === 0"
                class="text-center text-muted py-3 border border-dashed rounded"
              >
                동봉된 붙임 서류가 없습니다.
              </div>
            </div>
          </CCardBody>
        </CCard>
      </CCol>

      <!-- 사이드 관리 패널 (배부 부서 / 담당자 / 상태) -->
      <CCol lg="4">
        <CCard class="mb-4">
          <CCardHeader class="bg-light fw-semibold">
            <v-icon icon="mdi-account-cog" size="small" class="me-1" />
            사내 배부 및 처리 관리
          </CCardHeader>
          <CCardBody>
            <div class="mb-3">
              <CFormLabel>배부 / 주관 부서</CFormLabel>
              <CFormSelect v-model="form.recipient_dept">
                <option :value="null">부서 미지정</option>
                <option v-for="d in departments" :key="d.value" :value="d.value">
                  {{ d.label }}
                </option>
              </CFormSelect>
              <CFormText class="text-muted small">
                수신 공문을 처리할 사내 주관 부서를 지정합니다.
              </CFormText>
            </div>

            <div class="mb-3">
              <CFormLabel>처리 담당자</CFormLabel>
              <CFormSelect v-model="form.recipient_manager">
                <option :value="null">담당자 미지정</option>
                <option v-for="s in staffs" :key="s.value" :value="s.value">
                  {{ s.label }}
                </option>
              </CFormSelect>
              <CFormText class="text-muted small">
                공문 실무 처리를 담당할 직원을 지정합니다.
              </CFormText>
            </div>

            <div class="mb-0">
              <CFormLabel>처리 상태</CFormLabel>
              <CFormSelect v-model="form.status">
                <option value="received">접수 (미처리)</option>
                <option value="in_progress">처리중 (품의/검토)</option>
                <option value="replied">회신완료</option>
                <option value="closed">종결 (참조/보관)</option>
              </CFormSelect>
            </div>
          </CCardBody>
        </CCard>

        <!-- 처리 안내 카드 -->
        <CCard class="bg-light border-0">
          <CCardBody class="p-3 text-muted small" style="line-height: 1.7">
            <div class="fw-bold text-dark mb-1">
              <v-icon icon="mdi-information-outline" size="small" class="me-1 text-primary" />
              수신 공문 처리 프로세스
            </div>
            1. 접수 등록 후 상세 화면에서 <strong>[처리품의 상신]</strong>을 통해 전자결재와 즉시
            연계할 수 있습니다.<br />
            2. 회신 공문이 필요한 경우 해당 품의 승인 후 <strong>[발송 공문]</strong>으로 연계
            작성할 수 있습니다.
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>

    <ConfirmModal
      v-model="showConfirmModal"
      title="확인"
      :message="confirmMessage"
      @confirm="handleConfirm"
    />
  </div>
</template>

<style scoped>
.letter-form {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
