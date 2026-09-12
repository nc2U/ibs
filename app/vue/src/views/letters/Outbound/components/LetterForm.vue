<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useDocs } from '@/store/pinia/docs'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company'
import type { OfficialLetter } from '@/store/types/docs'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import MdEditor from '@/components/MdEditor/Index.vue'
import { markdownRender } from '@/utils/helper.ts'

const props = defineProps<{
  company: number
  letter?: OfficialLetter
  viewRoute: string
}>()

export interface LocalAttachmentItem {
  file: File
  name: string
  quantity: string
}

const emit = defineEmits<{
  onSubmit: [payload: OfficialLetter, attachmentsToUpload?: LocalAttachmentItem[]]
}>()

const { can, PERM } = usePerms()
const accStore = useAccount()
const comStore = useCompany()
const sealList = computed(() => comStore.sealList)
const currentCompany = computed(() => comStore.company)
const representativeName = computed(() => {
  return (
    currentCompany.value?.representative_name ||
    currentCompany.value?.ceo?.split(',')?.[0]?.trim() ||
    ''
  )
})
const selectedSeal = computed(() => {
  if (!form.value.seal) return null
  return sealList.value.find(item => item.pk === form.value.seal) || null
})
const selectedSealImage = computed(() => selectedSeal.value?.seal_image || null)

// 최종 승인(전결)권자의 직위/직책 명칭 (예: '대표이사', '현장소장', '본부장' 등)
const approverDutyTitle = computed(() => {
  return selectedSeal.value?.final_approval_duty_name || '대표이사'
})

// 최종 승인(전결)권자 성명
const finalApproverName = computed(() => {
  // 현장소장/본부장 등 전결인 경우: 기안자 본인이 전결권자 직접 기안 시 기안자 성명이 최종 승인권자
  if (['현장소장', '소장', '본부장', '팀장'].includes(approverDutyTitle.value)) {
    return (
      cleanDrafterName.value || form.value.drafter_name || representativeName.value || '전결권자'
    )
  }
  return representativeName.value || cleanDrafterName.value || '대표이사'
})

const cleanDrafterName = computed(() => {
  const name =
    approvalMode.value === 'approval'
      ? accStore.userInfo?.staff_name ||
        accStore.userInfo?.profile?.name ||
        accStore.userInfo?.username ||
        ''
      : form.value.drafter_name || ''
  return name.replace(/대표이사|대표|사장|소장|본부장|팀장/g, '').trim()
})

// 승인(전결)권자 직접 기안 단독 결재 여부
const isSoloApproval = computed(() => {
  if (form.value.is_solo_approval) return true
  // 수동 발송 모드에서 대표이사 결재 시 기안자명과 대표이사 성명이 일치하면 자동 단독 처리
  if (
    approvalMode.value === 'manual' &&
    !['현장소장', '소장', '본부장', '팀장'].includes(approverDutyTitle.value) &&
    cleanDrafterName.value &&
    representativeName.value &&
    cleanDrafterName.value === representativeName.value
  ) {
    return true
  }
  return false
})

// 발신자 연락처: 기안자 직원(Staff) 직통 연락처 우선, 미등록 시 회사 대표 연락처
const senderContact = computed(() => {
  const phone =
    (approvalMode.value === 'approval' ? accStore.userInfo?.staff_phone : '') ||
    currentCompany.value?.phone ||
    '-'
  const fax =
    (approvalMode.value === 'approval' ? accStore.userInfo?.staff_fax : '') ||
    currentCompany.value?.fax ||
    '-'
  const email =
    (approvalMode.value === 'approval' ? accStore.userInfo?.email : '') ||
    currentCompany.value?.email ||
    ''
  return { phone, fax, email }
})

const isEdit = computed(() => !!props.letter?.pk)
const canOLManage = computed(() => (isEdit.value ? can(PERM.DOCS_UPDATE) : can(PERM.DOCS_CREATE)))

const router = useRouter()
const docStore = useDocs()

const nextDocNumber = ref('')

// 발송 유형 모드: 'approval' (전자결재 상신) | 'manual' (수동/직접 발송)
const approvalMode = ref<'approval' | 'manual'>('approval')

// 붙임(첨부) 입력 모드: 'file' (파일 직접 첨부) | 'text' (텍스트 직접 입력)
const attachmentInputMode = ref<'file' | 'text'>('file')
const pendingAttachments = ref<LocalAttachmentItem[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)

// Form fields
const form = ref<OfficialLetter>({
  company: null,
  title: '',
  recipient_name: '',
  via: '',
  recipient_reference: '',
  content: '',
  attachment_text: '',
  issue_date: new Date().toISOString().substring(0, 10),
  disclosure_type: '1',
  seal: null,
  is_solo_approval: false,
  drafter_name: '',
  drafter_position: '',
  sender_zipcode: '',
  sender_address: '',
  // 발송 관리 메타 정보
  recipient_address: '',
  recipient_contact: '',
  dispatch_method: 'email',
  tracking_number: '',
  dispatched_at: null,
})

const validated = ref(false)

watch(
  () => props.letter,
  letter => {
    if (letter) {
      form.value = {
        ...letter,
        via: letter.via || '',
        attachment_text: letter.attachment_text || '',
        sender_zipcode: letter.sender_zipcode || '',
        sender_address: letter.sender_address || '',
        disclosure_type: letter.disclosure_type || '1',
        is_solo_approval: !!letter.is_solo_approval,
        dispatch_method: letter.dispatch_method || 'email',
        tracking_number: letter.tracking_number || '',
      }
      // 전자결재 연동 여부에 따라 모드 자동 설정
      if (
        letter.approval_document ||
        (letter.approval_status && letter.approval_status !== 'none')
      ) {
        approvalMode.value = 'approval'
      } else {
        approvalMode.value = 'manual'
      }

      // 붙임 입력 모드 자동 설정: 텍스트가 있고 파일이 없으면 텍스트 모드로
      if (letter.attachment_text && (!letter.attachments || letter.attachments.length === 0)) {
        attachmentInputMode.value = 'text'
      } else {
        attachmentInputMode.value = 'file'
      }
      // 신규 작성 시 회사의 공식 장부에 등록된 직원 성명(staff_name)으로 기본 기안자명 준비
      const currentUserName =
        accStore.userInfo?.staff_name ||
        accStore.userInfo?.profile?.name ||
        accStore.userInfo?.username ||
        ''
      if (!form.value.drafter_name && currentUserName) {
        form.value.drafter_name = currentUserName
      }
    }
  },
  { immediate: true },
)

watch(
  () => props.company,
  async newCompany => {
    if (newCompany) {
      await comStore.fetchCompanySealList(newCompany)
      if (!props.letter?.pk) {
        nextDocNumber.value = await docStore.getNextDocumentNumber(newCompany)
      }
    }
  },
  { immediate: true },
)

const onFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    Array.from(target.files).forEach(file => {
      pendingAttachments.value.push({
        file,
        name: file.name,
        quantity: '1부',
      })
    })
  }
  target.value = ''
}

const removePendingAttachment = (index: number) => {
  pendingAttachments.value.splice(index, 1)
}

const deleteExistingAttachment = async (attachmentId: number) => {
  if (props.letter?.pk && confirm('이 첨부파일을 삭제하시겠습니까?')) {
    await docStore.deleteLetterAttachment(attachmentId, props.letter.pk)
  }
}

const onSubmit = () => {
  validated.value = true

  // 전자결재 모드일 때는 기안자명이 비어있을 경우 직원 성명으로 자동 보정
  if (approvalMode.value === 'approval' && !form.value.drafter_name) {
    form.value.drafter_name =
      accStore.userInfo?.staff_name ||
      accStore.userInfo?.profile?.name ||
      accStore.userInfo?.username ||
      '기안'
  }

  // 텍스트 모드가 아닐 때는 attachment_text를 비워 상호 배타적으로 유지
  if (attachmentInputMode.value === 'file') {
    form.value.attachment_text = ''
  }

  // 수동 발송 모드에서 승인(전결)권자 직접 기안 시 기안자명이 비어있으면 최종 승인권자 명의로 자동 설정
  if (approvalMode.value === 'manual' && form.value.is_solo_approval && !form.value.drafter_name) {
    form.value.drafter_name = finalApproverName.value || approverDutyTitle.value
  }

  // Validate required fields
  if (
    !form.value.title ||
    !form.value.recipient_name ||
    (approvalMode.value === 'manual' && !form.value.is_solo_approval && !form.value.drafter_name) ||
    !form.value.content ||
    !form.value.issue_date
  ) {
    return
  }

  emit('onSubmit', form.value, pendingAttachments.value)
}

const goBack = () => {
  if (props.letter?.pk) {
    router.push({ name: `${props.viewRoute} - 보기`, params: { letterId: props.letter.pk } })
  } else {
    router.push({ name: props.viewRoute })
  }
}
</script>

<template>
  <div>
    <CRow class="mb-4">
      <CCol>
        <h4 class="mb-0">
          <v-icon icon="mdi-email-outline" size="small" class="me-2" />
          {{ isEdit ? '공문 수정' : '공문 작성' }}
        </h4>
        <small v-if="!isEdit && nextDocNumber" class="text-muted">
          예상 문서번호: {{ nextDocNumber }}
        </small>
      </CCol>
    </CRow>

    <CForm :validated="validated" @submit.prevent="onSubmit">
      <CRow>
        <!-- 좌측: 공문서 작성/수정 폼 (lg: 6, xl: 7) -->
        <CCol lg="6" xl="7">
          <!-- 1. 공문서 서식 영역 (PDF 템플릿과 동일 순서) -->
          <CCard class="mb-4" :class="isEdit ? 'border-success' : 'border-primary'">
            <CCardHeader
              class="text-white d-flex align-items-center"
              :class="isEdit ? 'bg-success' : 'bg-primary'"
            >
              <v-icon icon="mdi-file-document-outline" size="small" class="me-2" />
              <strong>공문서 서식 (PDF 인쇄 영역)</strong>
            </CCardHeader>
            <CCardBody>
              <!-- 수신 / (경유) / 참조 / 제목 (상단 4행 고정 서식) -->
              <div class="p-3 bg-light rounded mb-4 border">
                <h6 class="text-primary mb-3">
                  <v-icon icon="mdi-card-account-mail" size="small" class="me-1" />
                  수신 및 제목 정보
                </h6>
                <CRow class="mb-3">
                  <CCol md="6">
                    <CFormLabel> 수신 <span class="text-danger">*</span></CFormLabel>
                    <CFormInput
                      v-model="form.recipient_name"
                      placeholder="수신처 명칭 (예: OO주식회사, 구청장 등)"
                      required
                      :invalid="validated && !form.recipient_name"
                    />
                    <CFormFeedback invalid>수신처명을 입력해주세요.</CFormFeedback>
                  </CCol>
                  <CCol md="6">
                    <CFormLabel> 발신 요청(예정)일 <span class="text-danger">*</span> </CFormLabel>
                    <DatePicker v-model="form.issue_date" placeholder="발신 요청일 선택" required />
                    <CFormText class="text-muted">
                      {{
                        approvalMode === 'approval'
                          ? '결재권자에게 요청하는 발신 희망일입니다. 실제 공문서 시행일자는 최종 승인일에 자동으로 확정됩니다.'
                          : '발신 예정일자입니다. 실제 대외 발송 처리 시 발송일로 확정됩니다.'
                      }}
                    </CFormText>
                  </CCol>
                </CRow>
                <CRow class="mb-3">
                  <CCol md="6">
                    <CFormLabel>경유</CFormLabel>
                    <CFormInput
                      v-model="form.via"
                      placeholder="경유 기관 또는 부서 (없을 시 빈칸)"
                    />
                  </CCol>
                  <CCol md="6">
                    <CFormLabel>참조</CFormLabel>
                    <CFormInput
                      v-model="form.recipient_reference"
                      placeholder="참조 부서 또는 직위 (예: 대표이사 귀하)"
                    />
                  </CCol>
                </CRow>
                <CRow>
                  <CCol md="12">
                    <CFormLabel> 제목 <span class="text-danger">*</span></CFormLabel>
                    <CFormInput
                      v-model="form.title"
                      placeholder="공문 제목을 입력하세요"
                      required
                      :invalid="validated && !form.title"
                    />
                    <CFormFeedback invalid>제목을 입력해주세요.</CFormFeedback>
                  </CCol>
                </CRow>
              </div>

              <!-- 본문 내용 -->
              <div class="mb-4">
                <CFormLabel class="fw-bold">
                  본문 내용 <span class="text-danger">*</span>
                </CFormLabel>
                <MdEditor
                  v-model="form.content"
                  placeholder="공문 본문 내용을 입력하세요. (상단 툴바를 이용해 표, 굵게, 글머리 기호 등을 자유롭게 작성할 수 있습니다.)"
                  :height="360"
                  :preview="false"
                />
                <div v-if="validated && !form.content" class="text-danger small mt-1">
                  공문 본문 내용을 입력해주세요.
                </div>
                <CFormText class="text-muted mt-1 d-block">
                  마크다운 서식(표, 글머리 기호, 굵은 글씨 등)은 공문 인쇄 및 PDF 생성 시 표준
                  서식으로 자동 반영됩니다.
                </CFormText>
              </div>

              <!-- 붙임(첨부) 목록 -->
              <div class="mb-4 p-3 bg-light rounded border">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <CFormLabel class="fw-bold mb-0"> 붙임 (첨부 서류 목록) </CFormLabel>
                  <!-- 붙임 방식 토글 -->
                  <div class="btn-group btn-group-sm">
                    <button
                      type="button"
                      class="btn"
                      :class="
                        attachmentInputMode === 'file' ? 'btn-primary' : 'btn-outline-primary'
                      "
                      @click="attachmentInputMode = 'file'"
                    >
                      <v-icon icon="mdi-paperclip" size="small" class="me-1" />
                      파일 직접 첨부 (권장)
                    </button>
                    <button
                      type="button"
                      class="btn"
                      :class="
                        attachmentInputMode === 'text' ? 'btn-primary' : 'btn-outline-primary'
                      "
                      @click="attachmentInputMode = 'text'"
                    >
                      <v-icon icon="mdi-format-list-bulleted" size="small" class="me-1" />
                      텍스트 직접 입력
                    </button>
                  </div>
                </div>

                <!-- 파일 직접 첨부 모드 -->
                <div v-if="attachmentInputMode === 'file'">
                  <CAlert color="info" class="py-2 mb-3">
                    <small>
                      <v-icon icon="mdi-information-outline" size="small" class="me-1" />
                      <strong>권장 사항:</strong> 공문서 위변조 방지 및 수신처의 원활한 열람을 위해
                      가급적 <strong>PDF 파일</strong>로 변환하여 첨부하는 것을 권장합니다.
                      (부득이한 경우 한글, 엑셀, 이미지, 압축파일 등도 첨부 가능)
                    </small>
                  </CAlert>

                  <!-- 기존 등록된 첨부파일 (수정 시) -->
                  <div v-if="form.attachments && form.attachments.length > 0" class="mb-3">
                    <div class="fw-bold small text-muted mb-2">
                      <v-icon icon="mdi-check-circle" size="small" class="me-1 text-success" />
                      현재 등록된 첨부파일 ({{ form.attachments.length }}개):
                    </div>
                    <div
                      v-for="(att, idx) in form.attachments"
                      :key="att.pk"
                      class="p-2 mb-2 bg-white rounded border d-flex justify-content-between align-items-center"
                    >
                      <div>
                        <span class="badge bg-secondary me-2">붙임 {{ idx + 1 }}</span>
                        <strong class="text-primary">{{ att.name || att.file_name }}</strong>
                        <span class="text-muted ms-2">({{ att.quantity || '1부' }})</span>
                        <CBadge
                          :color="
                            (att.file_name || '').toLowerCase().endsWith('.pdf')
                              ? 'success'
                              : 'warning'
                          "
                          class="ms-2"
                        >
                          {{
                            (att.file_name || '').toLowerCase().endsWith('.pdf')
                              ? 'PDF'
                              : '일반파일'
                          }}
                        </CBadge>
                        <small class="text-muted ms-2">[{{ att.file_name }}]</small>
                      </div>
                      <v-btn
                        color="error"
                        variant="text"
                        size="small"
                        title="첨부파일 삭제"
                        @click="deleteExistingAttachment(att.pk as number)"
                      >
                        <v-icon icon="mdi-trash-can-outline" size="small" class="me-1" /> 삭제
                      </v-btn>
                    </div>
                  </div>

                  <!-- 새로 추가 대기 중인 파일 목록 -->
                  <div v-if="pendingAttachments.length > 0" class="mb-3">
                    <div class="fw-bold small text-primary mb-2">
                      <v-icon icon="mdi-plus" size="small" class="me-1" />
                      신규 추가할 첨부파일 ({{ pendingAttachments.length }}개):
                    </div>
                    <div
                      v-for="(att, idx) in pendingAttachments"
                      :key="idx"
                      class="p-3 mb-2 bg-white rounded border position-relative"
                    >
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <div>
                          <span class="badge bg-primary me-2">
                            붙임 {{ (form.attachments?.length || 0) + idx + 1 }}
                          </span>
                          <CBadge
                            :color="
                              att.file.name.toLowerCase().endsWith('.pdf') ? 'success' : 'warning'
                            "
                          >
                            {{
                              att.file.name.toLowerCase().endsWith('.pdf')
                                ? 'PDF (권장서식)'
                                : '일반문서'
                            }}
                          </CBadge>
                        </div>
                        <v-btn
                          color="error"
                          variant="text"
                          size="x-small"
                          @click="removePendingAttachment(idx)"
                        >
                          <v-icon icon="mdi-close" size="small" class="me-1" /> 제외
                        </v-btn>
                      </div>

                      <CRow class="g-2 align-items-end mb-2">
                        <CCol md="7">
                          <CFormLabel class="small fw-semibold mb-1">
                            붙임 명칭
                            <span class="text-muted fw-normal"
                              >(공문서 본문에 인쇄될 공식 명칭)</span
                            >
                          </CFormLabel>
                          <CFormInput
                            v-model="att.name"
                            size="sm"
                            placeholder="예: 사업계획서, 설계도면 등 (미입력 시 원본 파일명)"
                          />
                        </CCol>
                        <CCol md="3">
                          <CFormLabel class="small fw-semibold mb-1">수량 / 부수</CFormLabel>
                          <CFormInput
                            v-model="att.quantity"
                            size="sm"
                            placeholder="예: 1부, 2부, 1식"
                          />
                        </CCol>
                        <CCol md="2">
                          <div class="small text-muted text-truncate py-1" :title="att.file.name">
                            <v-icon icon="mdi-file-outline" size="small" class="me-1" />
                            {{ att.file.name }}
                          </div>
                        </CCol>
                      </CRow>

                      <!-- 실시간 공문 인쇄 미리보기 -->
                      <div class="bg-light p-2 rounded border small text-secondary">
                        <span class="fw-bold text-dark">인쇄 미리보기: </span>
                        <span
                          >{{ (form.attachments?.length || 0) + idx + 1 }}.
                          {{ att.name || att.file.name }} {{ att.quantity || '1부' }}.</span
                        >
                      </div>
                    </div>
                  </div>

                  <input
                    ref="fileInputRef"
                    type="file"
                    multiple
                    accept=".pdf,.hwp,.hwpx,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.zip"
                    class="d-none"
                    @change="onFileSelect"
                  />
                  <v-btn
                    color="primary"
                    variant="outlined"
                    size="small"
                    @click="fileInputRef?.click()"
                  >
                    <v-icon icon="mdi-cloud-upload" size="small" class="me-1" />
                    파일 추가하기 (다중 선택 가능)
                  </v-btn>
                </div>

                <!-- 텍스트 직접 입력 모드 -->
                <div v-else>
                  <CFormText class="text-muted d-block mb-2">
                    파일 첨부 없이 인쇄용 붙임 텍스트만 기재할 경우 사용합니다. (예: 1. 사업계획서
                    1부.)
                  </CFormText>
                  <CFormTextarea
                    v-model="form.attachment_text"
                    placeholder="1. 관련 서류 1부.&#10;2. 사업계획서 1부. 끝."
                    rows="3"
                  />
                </div>
              </div>

              <!-- 발신 명의, 날인 및 기안자 정보 -->
              <div class="p-3 bg-light rounded border">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h6 class="text-primary mb-0">
                    <v-icon icon="mdi-draw-pen" size="small" class="me-1" />
                    발신 명의, 직인 날인 및 기안 정보
                  </h6>
                  <!-- 발송 유형 선택 토글 -->
                  <div class="btn-group btn-group-sm">
                    <button
                      type="button"
                      class="btn"
                      :class="approvalMode === 'approval' ? 'btn-primary' : 'btn-outline-primary'"
                      @click="approvalMode = 'approval'"
                    >
                      <v-icon icon="mdi-shield-check" size="small" class="me-1" />
                      전자결재 상신 발송
                    </button>
                    <button
                      type="button"
                      class="btn"
                      :class="approvalMode === 'manual' ? 'btn-primary' : 'btn-outline-primary'"
                      @click="approvalMode = 'manual'"
                    >
                      <v-icon icon="mdi-pencil" size="small" class="me-1" />
                      수동(직접) 발송
                    </button>
                  </div>
                </div>

                <!-- 전자결재 모드 안내 -->
                <CAlert v-if="approvalMode === 'approval'" color="light" class="border py-2 mb-3">
                  <small class="text-primary">
                    <v-icon icon="mdi-information-outline" size="small" class="me-1" />
                    <strong>전자결재 연동 모드:</strong> 결재선 상신 및 최종 승인 시 결재선의
                    기안자, 검토자, 최종 결재권자(대표이사/임원 등)의 직위와 성명이 공문서 하단
                    결재선에 자동으로 표기됩니다.
                  </small>
                </CAlert>

                <!-- 수동 발송 모드 안내 -->
                <CAlert v-else color="warning" class="py-2 mb-3">
                  <small>
                    <v-icon icon="mdi-alert-outline" size="small" class="me-1" />
                    <strong>수동(직접) 발송 모드:</strong> 전자결재를 거치지 않고 직접 발송하는
                    공문입니다. 공문서 하단 결재/담당란에 인쇄될 기안/담당자 정보를 아래에 직접
                    입력해주세요.
                  </small>
                </CAlert>

                <CRow class="mb-3">
                  <CCol :md="approvalMode === 'manual' ? 4 : 6">
                    <CFormLabel>날인 인감 (직인)</CFormLabel>
                    <CFormSelect
                      :value="form.seal || ''"
                      @change="
                        form.seal = Number(($event.target as HTMLSelectElement).value) || null
                      "
                    >
                      <option value="">인장 미선택 / (직인생략 / 출력 후 실물날인)</option>
                      <option v-for="s in sealList" :key="s.pk" :value="s.pk">
                        {{ s.name }} ({{ s.seal_type_desc || s.seal_type }}) - 전자날인
                      </option>
                    </CFormSelect>
                    <div v-if="selectedSealImage" class="mt-2">
                      <div class="d-flex align-items-center mb-1">
                        <img
                          :src="selectedSealImage"
                          alt="인장"
                          style="width: 40px; height: 40px; object-fit: contain"
                          class="border rounded p-1 bg-white me-2"
                        />
                        <div>
                          <small class="text-success fw-semibold d-block">
                            <v-icon icon="mdi-check-circle" size="small" class="me-1" />
                            등록된 직인 이미지가 PDF에 자동 합성 날인됩니다.
                          </small>
                          <small v-if="approvalMode === 'approval'" class="text-primary">
                            <v-icon icon="mdi-shield-check" size="small" class="me-1" />
                            <strong>전결 승인 규정: </strong>
                            <span v-if="selectedSeal?.final_approval_duty_name">
                              {{ selectedSeal.final_approval_duty_name }} 전결 가능
                            </span>
                            <span v-else-if="selectedSeal?.final_dept_level">
                              {{ selectedSeal.final_dept_level }}레벨 부서장 전결 가능
                            </span>
                            <span v-else class="text-danger fw-semibold">
                              대표이사 결재 필수 (전결 불가)
                            </span>
                          </small>
                        </div>
                      </div>
                    </div>
                    <div v-else class="mt-1">
                      <small class="text-muted">
                        * 종이 출력 후 실물 도장을 직접 날인하여 발송할 경우 인장을 선택하지
                        마십시오.
                      </small>
                    </div>
                  </CCol>

                  <!-- 공개 구분 선택 -->
                  <CCol :md="approvalMode === 'manual' ? 4 : 6">
                    <CFormLabel>공개 구분 <span class="text-danger">*</span></CFormLabel>
                    <CFormSelect v-model="form.disclosure_type">
                      <option value="1">공개</option>
                      <option value="2">부분공개</option>
                      <option value="3">비공개 (영업비밀/대외비)</option>
                    </CFormSelect>
                    <div class="mt-1">
                      <small
                        v-if="form.disclosure_type === '3'"
                        class="text-danger d-block fw-semibold"
                      >
                        <v-icon icon="mdi-lock-outline" size="small" class="me-1" />
                        영업비밀·대외비 문서: 외부 유출 및 제3자 정보공개가 전면 제한됩니다.
                      </small>
                      <small
                        v-else-if="form.disclosure_type === '2'"
                        class="text-warning-emphasis d-block fw-semibold"
                      >
                        <v-icon icon="mdi-shield-check" size="small" class="me-1" />
                        부분공개: 개인정보·계약단가 등 특정 비공개 대상 정보 외의 부분만 공개됩니다.
                      </small>
                      <small v-else class="text-secondary d-block">
                        <v-icon icon="mdi-alert-outline" size="small" class="me-1 text-warning" />
                        개인정보(주민번호·연락처 등), 계약단가, 영업비밀 등이 포함된 경우
                        <strong>'부분공개'</strong> 또는 <strong>'비공개'</strong>로 지정하십시오.
                      </small>
                    </div>
                  </CCol>

                  <!-- 수동 발송일 때만 기안자명 노출 -->
                  <CCol v-if="approvalMode === 'manual'" md="4">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                      <CFormLabel class="mb-0">
                        기안/담당자명
                        <span v-if="!form.is_solo_approval" class="text-danger">*</span>
                      </CFormLabel>
                    </div>
                    <CFormInput
                      v-model="form.drafter_name"
                      :placeholder="
                        form.is_solo_approval
                          ? `${approverDutyTitle} 직접 기안 (담당 생략)`
                          : '기안/담당자명 (예: 홍길동)'
                      "
                      :required="!form.is_solo_approval"
                      :invalid="validated && !form.is_solo_approval && !form.drafter_name"
                    />
                    <CFormFeedback invalid>기안/담당자명을 입력해주세요.</CFormFeedback>
                    <CFormText class="text-muted">
                      {{
                        form.is_solo_approval
                          ? `공문서 하단 담당란이 생략되고 '${approverDutyTitle} ${finalApproverName}' 단독 승인/시행으로 표기됩니다.`
                          : "공문서 하단 담당란에 '담당 [성명]'으로 표기됩니다."
                      }}
                    </CFormText>
                  </CCol>
                </CRow>

                <!-- 수동 발송 시: 직무별 승인(전결)권자 직접 기안 토글 및 담당 직위 -->
                <CRow v-if="approvalMode === 'manual'" class="mb-3">
                  <CCol md="6">
                    <CFormLabel>승인(전결)권자 직접 기안 여부</CFormLabel>
                    <div class="border rounded p-2 bg-white d-flex align-items-center">
                      <CFormCheck
                        id="is_solo_approval_check"
                        v-model="form.is_solo_approval"
                        :label="`${approverDutyTitle} 직접 기안 (담당자란 생략)`"
                      />
                    </div>
                    <CFormText class="text-muted">
                      {{ approverDutyTitle }} 등 최종 승인(전결)권자가 직접 기안하여 발송할 경우
                      체크하면 하단 담당란이 생략됩니다.
                    </CFormText>
                  </CCol>
                  <CCol v-if="!form.is_solo_approval" md="6">
                    <CFormLabel>담당 직위/직책</CFormLabel>
                    <CFormInput
                      v-model="form.drafter_position"
                      placeholder="직위/직책 (예: 과장, 대리, 팀장)"
                    />
                    <CFormText class="text-muted">기안 담당자의 직위/직책입니다.</CFormText>
                  </CCol>
                </CRow>

                <CRow>
                  <CCol md="4">
                    <CFormLabel>발신 우편번호 (현장/지사)</CFormLabel>
                    <CFormInput v-model="form.sender_zipcode" placeholder="예: 12345" />
                  </CCol>
                  <CCol md="8">
                    <CFormLabel>발신 도로명 주소 (현장/지사)</CFormLabel>
                    <CFormInput
                      v-model="form.sender_address"
                      placeholder="특정 현장/지사 주소 발송 시 입력 (비워두면 본사 기본주소 자동 적용)"
                    />
                    <CFormText class="text-muted">비워두면 본사 기본 주소가 인쇄됩니다.</CFormText>
                  </CCol>
                </CRow>
              </div>
            </CCardBody>
          </CCard>

          <!-- 2. 발송 및 대장 관리 메타 영역 (공문서에는 인쇄되지 않는 업무 관리 데이터) -->
          <CCard class="mb-4">
            <CCardHeader class="bg-secondary text-white d-flex align-items-center">
              <v-icon icon="mdi-folder-open-outline" class="me-2" />
              <strong>발송 및 대장 관리 정보 (시스템 관리용 메타데이터)</strong>
            </CCardHeader>
            <CCardBody>
              <CAlert color="info" class="py-2 mb-3">
                <small>
                  <v-icon icon="mdi-information-outline" size="small" class="me-1" />
                  아래 정보는 공문서 본문에는 인쇄되지 않으며, 우편 라벨 출력, 등기번호 추적 및 발송
                  대장 이력 관리에 사용됩니다.
                </small>
              </CAlert>

              <CRow class="mb-3">
                <CCol md="6">
                  <CFormLabel>수신처 주소 (우편/등기 발송지)</CFormLabel>
                  <CFormInput
                    v-model="form.recipient_address"
                    placeholder="우편 발송지 주소 (봉투 라벨 인쇄용)"
                  />
                </CCol>
                <CCol md="6">
                  <CFormLabel>수신처 연락처/담당자</CFormLabel>
                  <CFormInput
                    v-model="form.recipient_contact"
                    placeholder="수신처 담당자 전화번호, 휴대폰 등"
                  />
                </CCol>
              </CRow>

              <CRow class="mb-2">
                <CCol md="4">
                  <CFormLabel>발송 방법</CFormLabel>
                  <CFormSelect v-model="form.dispatch_method">
                    <option value="email">이메일</option>
                    <option value="registered_mail">등기우편</option>
                    <option value="direct">인편/직접교부</option>
                    <option value="courier">퀵/택배</option>
                    <option value="fax">팩스</option>
                    <option value="etc">기타</option>
                  </CFormSelect>
                </CCol>
                <CCol md="4">
                  <CFormLabel>등기 / 송장 번호</CFormLabel>
                  <CFormInput
                    v-model="form.tracking_number"
                    placeholder="13자리 등기번호 또는 택배 송장번호"
                  />
                </CCol>
                <CCol md="4">
                  <CFormLabel>발송 완료일자</CFormLabel>
                  <DatePicker
                    :model-value="form.dispatched_at ? form.dispatched_at.substring(0, 10) : ''"
                    placeholder="실제 발송 완료일"
                    @update:model-value="form.dispatched_at = $event ? `${$event}T00:00:00` : null"
                  />
                </CCol>
              </CRow>
            </CCardBody>
          </CCard>

          <!-- Actions -->
          <CRow class="mb-4">
            <CCol class="d-flex justify-content-between">
              <v-btn color="secondary" variant="outlined" @click="goBack">
                <v-icon icon="mdi-arrow-left" class="me-1" />
                취소
              </v-btn>
              <v-btn
                type="submit"
                :color="isEdit ? 'success' : 'primary'"
                :disabled="!accStore.isStaff && canOLManage"
              >
                <v-icon icon="mdi-content-save-outline" class="me-1" />
                {{ isEdit ? '수정 저장' : '공문 저장' }}
              </v-btn>
            </CCol>
          </CRow>
        </CCol>

        <!-- 우측: 실시간 A4 공문서 라이브 프리뷰 (lg: 6, xl: 5 / lg 이상 화면에서 표출) -->
        <CCol lg="6" xl="5" class="d-none d-lg-block">
          <div class="sticky-top" style="top: 20px; z-index: 10">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <span class="fw-bold text-secondary">
                <v-icon icon="mdi-printer-outline" class="me-1" />
                실시간 인쇄 미리보기 (A4 Live Preview)
              </span>
              <CBadge color="info">실시간 반영중</CBadge>
            </div>

            <!-- A4 종이 프리뷰 컨테이너 (A4 비율 210:297 고정) -->
            <div class="a4-preview-wrapper d-flex justify-content-center">
              <div class="a4-preview-sheet shadow border bg-white p-4">
                <!-- 1. 레터헤드 -->
                <div
                  class="preview-letterhead text-center pb-2 mb-2 border-bottom position-relative"
                >
                  <div
                    class="preview-company-name fw-bold"
                    style="font-size: 1.15rem; letter-spacing: 2px"
                  >
                    {{ currentCompany?.name || '회사명' }}
                  </div>
                  <div class="text-muted" style="font-size: 0.72rem; line-height: 1.3">
                    <span v-if="currentCompany?.ceo">대표이사 {{ currentCompany.ceo }} | </span>
                    <span v-if="currentCompany?.tax_number"
                      >사업자등록번호 {{ currentCompany.tax_number }}</span
                    >
                    <br />
                    <span>
                      {{ currentCompany?.address1 }} {{ currentCompany?.address2 || '' }}
                      <span v-if="currentCompany?.zipcode">[{{ currentCompany.zipcode }}]</span>
                    </span>
                  </div>
                  <!-- 영문 그라데이션 띠 -->
                  <div
                    class="preview-en-bar text-center text-white mt-1"
                    style="
                      height: 8px;
                      line-height: 8px;
                      font-size: 6px;
                      background: linear-gradient(to right, #666 0%, #777 30%, #999 70%, #aaa 100%);
                    "
                  >
                    {{ currentCompany?.en_name || '' }}
                  </div>
                </div>

                <!-- 2. 수신처 정보 (4행 고정) -->
                <div class="preview-recipient mb-2">
                  <table class="w-100" style="font-size: 0.8rem; line-height: 1.5">
                    <tbody>
                      <tr>
                        <td style="width: 55px; font-weight: bold; color: #555">수 신</td>
                        <td>{{ form.recipient_name || '(수신처 미입력)' }}</td>
                      </tr>
                      <tr>
                        <td style="font-weight: bold; color: #555">경 유</td>
                        <td>{{ form.via || '' }}</td>
                      </tr>
                      <tr>
                        <td style="font-weight: bold; color: #555">참 조</td>
                        <td>{{ form.recipient_reference || '' }}</td>
                      </tr>
                      <tr class="fw-bold" style="border-bottom: 2px solid #333">
                        <td style="color: #111; padding-bottom: 4px">제 목</td>
                        <td style="padding-bottom: 4px">{{ form.title || '(제목 미입력)' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <!-- 3. 본문 영역 (가변 확장 및 내용 스크롤 지원) -->
                <div
                  class="preview-content markdown-content my-2 p-3"
                  style="
                    flex: 1 1 auto;
                    min-height: 0;
                    overflow-y: auto;
                    font-size: 0.82rem;
                    line-height: 1.7;
                    word-break: break-all;
                    text-align: justify;
                  "
                >
                  <div
                    v-if="form.content"
                    class="preview-markdown-body"
                    v-html="markdownRender(form.content)"
                  />
                  <div v-else class="text-muted">
                    공문 본문 내용이 여기에 실시간으로 표시됩니다.
                  </div>

                  <!-- 붙임 목록 -->
                  <div v-if="attachmentInputMode === 'file'" class="mt-3 pt-2">
                    <div
                      v-if="
                        (form.attachments && form.attachments.length > 0) ||
                        pendingAttachments.length > 0
                      "
                    >
                      <div class="fw-bold mb-1" style="font-size: 0.78rem">붙임:</div>
                      <div
                        v-for="(att, idx) in form.attachments"
                        :key="'ex-' + idx"
                        style="font-size: 0.78rem; padding-left: 10px"
                      >
                        {{ idx + 1 }}. {{ att.name || att.file_name }} {{ att.quantity || '1부' }}.
                      </div>
                      <div
                        v-for="(att, idx) in pendingAttachments"
                        :key="'new-' + idx"
                        style="font-size: 0.78rem; padding-left: 10px"
                      >
                        {{ (form.attachments?.length || 0) + idx + 1 }}.
                        {{ att.name || att.file.name }} {{ att.quantity || '1부' }}.
                      </div>
                    </div>
                  </div>
                  <div v-else-if="form.attachment_text" class="mt-3 pt-2">
                    <div class="fw-bold mb-1" style="font-size: 0.78rem">붙임:</div>
                    <div style="font-size: 0.78rem; padding-left: 10px; white-space: pre-wrap">
                      {{ form.attachment_text }}
                    </div>
                  </div>
                </div>

                <!-- 4 & 5. 바닥 영역 (서명 + 메타정보) -->
                <div class="preview-bottom-wrapper mt-auto">
                  <!-- 4. 하단 서명 / 직인 날인 -->
                  <div class="preview-signature text-center my-2">
                    <div
                      class="fw-bold d-inline-flex align-items-center"
                      style="font-size: 1.05rem"
                    >
                      <span>{{ currentCompany?.name || '회사명' }}</span>
                      <span v-if="selectedSealImage" class="ms-2">
                        <img
                          :src="selectedSealImage"
                          alt="직인"
                          style="width: 36px; height: 36px; object-fit: contain"
                        />
                      </span>
                      <span
                        v-else
                        class="ms-2 text-muted border border-secondary rounded-circle d-inline-flex align-items-center justify-content-center"
                        style="width: 30px; height: 30px; font-size: 0.75rem"
                      >
                        (인)
                      </span>
                    </div>
                  </div>

                  <!-- 5. 결재선 및 시행 메타 -->
                  <div
                    class="preview-bottom pt-2"
                    style="font-size: 0.72rem; line-height: 1.4; border-top: 2px solid #333333"
                  >
                    <!-- 시행/접수/주소/연락처 및 상단 결재선 통합 테이블 (완전 수직 정렬) -->
                    <table
                      class="w-100"
                      style="color: #444; border-collapse: collapse; font-size: 0.72rem"
                    >
                      <tbody>
                        <!-- 1행: 결재선 (시행/우편/전화와 동일한 테이블 1행에 배치하여 좌측선 100% 칼정렬) -->
                        <tr class="border-bottom">
                          <td
                            class="pb-1"
                            style="width: 40px; vertical-align: bottom; padding-left: 0"
                          >
                            <template v-if="!isSoloApproval">
                              <span class="text-secondary">담당</span>
                            </template>
                          </td>
                          <td colspan="2" class="pb-1" style="vertical-align: bottom">
                            <template v-if="!isSoloApproval">
                              <span class="fw-bold text-dark">{{
                                approvalMode === 'approval'
                                  ? accStore.userInfo?.staff_name ||
                                    accStore.userInfo?.profile?.name ||
                                    accStore.userInfo?.username ||
                                    '기안자'
                                  : cleanDrafterName || form.drafter_name || '담당자'
                              }}</span>
                            </template>
                            <span v-else class="text-muted fst-italic"
                              >({{ approverDutyTitle }} 직접 기안)</span
                            >
                          </td>
                          <td colspan="2" class="text-end pb-1" style="vertical-align: bottom">
                            <div class="text-muted" style="font-size: 0.65rem; margin-bottom: 1px">
                              <span v-if="approvalMode === 'approval'" class="badge bg-secondary">
                                결재 승인 시 자동 확정
                              </span>
                              <span v-else>
                                {{
                                  ['현장소장', '소장', '본부장', '팀장'].includes(approverDutyTitle)
                                    ? '전결'
                                    : '시행'
                                }}
                                {{ form.issue_date || '발신일자' }}
                              </span>
                            </div>
                            <div>
                              <span class="me-1 text-secondary">
                                {{ approverDutyTitle }}
                              </span>
                              <span class="fw-bold text-dark">{{ finalApproverName }}</span>
                            </div>
                          </td>
                        </tr>
                        <tr>
                          <td
                            style="
                              width: 40px;
                              font-weight: bold;
                              padding-left: 0;
                              padding-top: 4px;
                            "
                          >
                            시행
                          </td>
                          <td style="width: 140px; padding-top: 4px">
                            {{ form.document_number || nextDocNumber || '자동채번' }}
                          </td>
                          <td style="width: 110px; padding-top: 4px">
                            ({{
                              approvalMode === 'approval'
                                ? form.effective_issue_date || form.issue_date || '승인일 확정'
                                : form.effective_issue_date || form.issue_date || '발신일자'
                            }})
                          </td>
                          <td style="width: 40px; font-weight: bold; padding-top: 4px">접수</td>
                          <td style="padding-top: 4px"></td>
                        </tr>
                        <tr>
                          <td style="font-weight: bold">우편</td>
                          <td colspan="4">
                            <span v-if="form.sender_address">
                              <span v-if="form.sender_zipcode">({{ form.sender_zipcode }}) </span>
                              {{ form.sender_address }}
                            </span>
                            <span v-else>
                              <span v-if="currentCompany?.zipcode"
                                >({{ currentCompany.zipcode }})
                              </span>
                              {{ currentCompany?.address1 }} {{ currentCompany?.address2 || '' }}
                              {{ currentCompany?.address3 || '' }}
                            </span>
                          </td>
                        </tr>
                        <tr>
                          <td style="font-weight: bold">전화</td>
                          <td style="width: 130px">{{ senderContact.phone }}</td>
                          <td style="width: 35px; font-weight: bold">팩스</td>
                          <td style="width: 120px">{{ senderContact.fax }}</td>
                          <td>
                            <div class="d-flex justify-content-between align-items-center">
                              <span>{{ senderContact.email }}</span>
                              <span class="text-end text-dark fw-normal ps-1">
                                <span class="text-secondary me-1">/</span>
                                <span class="fw-semibold">
                                  {{
                                    form.disclosure_type === '2'
                                      ? '부분공개'
                                      : form.disclosure_type === '3'
                                        ? '비공개'
                                        : '공개'
                                  }}
                                </span>
                              </span>
                            </div>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CCol>
      </CRow>
    </CForm>
  </div>
</template>

<style scoped>
.a4-preview-wrapper {
  width: 100%;
}

.a4-preview-sheet {
  width: 100%;
  max-width: 100%;
  max-height: calc(100vh - 110px);
  aspect-ratio: 210 / 297;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  color: #111111;
  font-family: 'Nanum Gothic', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
  border: 1px solid #ced4da;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  border-radius: 4px;
}

:deep(.preview-markdown-body) {
  width: 100%;
}

:deep(.preview-markdown-body p) {
  margin-bottom: 0.5rem;
}

:deep(.preview-markdown-body table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.5rem 0;
  font-size: 0.75rem;
}

:deep(.preview-markdown-body th),
:deep(.preview-markdown-body td) {
  border: 1px solid #ced4da;
  padding: 3px 6px;
  text-align: center;
}

:deep(.preview-markdown-body th) {
  background-color: #f8f9fa;
}

:deep(.preview-markdown-body center) {
  display: block;
  text-align: center;
  margin: 0.5rem 0;
}
</style>
