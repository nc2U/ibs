<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { markdownRender } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useDocs } from '@/store/pinia/docs'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company'
import type { OfficialLetter } from '@/store/types/docs'
import MdEditor from '@/components/MdEditor/Index.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import DaumPostcode from '@/components/DaumPostcode/index.vue'
import { type AddressData, callAddress } from '@/components/DaumPostcode/address'
import LetterA4Preview from './LetterA4Preview.vue'

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

// 대표이사 정보 분석 (단독 / 공동대표)
const representativesList = computed(() => {
  if (!currentCompany.value?.ceo) return []
  const parts = currentCompany.value.ceo
    .replace(/;/g, ',')
    .split(',')
    .map((p: string) => p.trim())
    .filter(Boolean)
  const isJoint = parts.length > 1 || form.value.sender_display_type === 'co_rep'
  return parts.map((name: string) => ({
    title: isJoint ? '공동대표이사' : '대표이사',
    name,
  }))
})

const representativeName = computed(() => {
  return (
    representativesList.value[0]?.name ||
    currentCompany.value?.representative_name ||
    currentCompany.value?.ceo?.split(',')?.[0]?.trim() ||
    ''
  )
})

// 모드별 선택 가능한 인장 목록 필터링:
// 전자결재 모드(approval)인 경우 부서/현장 직인(DEPT_SEAL)은 연동 결재선(route_template)이 있거나 책임자/전결직책이 완비된 인장만 허용
const availableSealList = computed(() => {
  return sealList.value.filter(s => {
    if (approvalMode.value === 'approval' && s.seal_type === 'DEPT_SEAL') {
      // 부서장 직인은 연동 결재선 템플릿이 있거나 전결 직책이 있는 경우에만 전자결재 노출
      return !!s.route_template || !!s.final_approval_duty
    }
    return true
  })
})

const selectedSeal = computed(() => {
  if (!form.value.seal) return null
  return sealList.value.find(item => item.pk === form.value.seal) || null
})
const selectedSealImage = computed(() => selectedSeal.value?.seal_image || null)

// 공동대표 보조 인장
const selectedCoSeal = computed(() => {
  if (!form.value.co_seal) return null
  return sealList.value.find(item => item.pk === form.value.co_seal) || null
})
const selectedCoSealImage = computed(() => selectedCoSeal.value?.seal_image || null)

// 최종 승인(전결)권자의 직위/직책 명칭 (예: '대표이사', '현장소장', '본부장' 등)
const approverDutyTitle = computed(() => {
  if (form.value.sender_duty_title) return form.value.sender_duty_title
  if (selectedSeal.value?.internal_manager_duty) return selectedSeal.value.internal_manager_duty
  return selectedSeal.value?.final_approval_duty_name || '대표이사'
})

// 최종 승인(전결)권자 성명
const finalApproverName = computed(() => {
  if (form.value.sender_name) return form.value.sender_name
  // 1순위: 선택된 인장의 사내 총괄 관리책임자 성명
  if (selectedSeal.value?.internal_manager_name) {
    return selectedSeal.value.internal_manager_name
  }
  // 2순위: 전결 직책이 있는 인장인 경우
  if (['현장소장', '소장', '본부장', '팀장'].includes(approverDutyTitle.value)) {
    return (
      cleanDrafterName.value || form.value.drafter_name || representativeName.value || '전결권자'
    )
  }
  // 3순위: 기본 대표이사 성명
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
  co_seal: null,
  sender_display_type: 'company_only',
  sender_duty_title: '',
  sender_name: '',
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
// 경유/참조 필드 펼침 상태 (입력된 값이 있으면 기본 오픈)
const showViaRef = ref(false)
// 발신지 주소 직접 입력(현장/지사) 펼침 상태 (입력된 값이 있으면 기본 오픈)
const showCustomAddress = ref(false)
// DaumPostcode 컴포넌트 ref
const refPostCode = ref()

// 주소 상세 입력을 위한 분리 상태 및 DOM ref
// DaumPostcode에서 반환된 기본 도로명/지번 주소(address1)와 참고항목(address3: 법정동, 공동주택명 등)
const senderAddress1 = ref('')
const senderAddress3 = ref('')
const senderAddressDetail = ref('')
const senderDetailInputRef = ref<any>(null)

const recipientAddress1 = ref('')
const recipientAddress3 = ref('')
const recipientAddressDetail = ref('')
const recipientDetailInputRef = ref<any>(null)

// 화면 노출용 기본 주소 표기 (예: 인천 연수구 능허대로 287)
const senderAddressBase = computed(() => {
  return senderAddress1.value
})

const recipientAddressBase = computed(() => {
  return recipientAddress1.value
})

// 표준 주소 조합 함수: [기본주소] [상세주소] [(법정동/참고항목)]
// 예: 인천 연수구 능허대로 287 대성빌딩 4층 (동춘동)
const composeAddress = (addr1: string, detail: string, addr3: string) => {
  const parts: string[] = []
  if (addr1.trim()) parts.push(addr1.trim())
  if (detail.trim()) parts.push(detail.trim())
  if (addr3.trim()) {
    const cleanRef = addr3.trim()
    const formattedRef = cleanRef.startsWith('(') ? cleanRef : `(${cleanRef})`
    parts.push(formattedRef)
  }
  return parts.join(' ')
}

// 상세주소 입력 시 form 필드와 동기화
const updateSenderAddress = () => {
  form.value.sender_address = composeAddress(
    senderAddress1.value,
    senderAddressDetail.value,
    senderAddress3.value,
  )
}

const updateRecipientAddress = () => {
  form.value.recipient_address = composeAddress(
    recipientAddress1.value,
    recipientAddressDetail.value,
    recipientAddress3.value,
  )
}

const addressCallback = (data: AddressData) => {
  const { formNum, zipcode, address1, address3 } = callAddress(data)

  if (formNum === 1) {
    // 1: 발신지(현장/지사) 주소
    form.value.sender_zipcode = zipcode
    senderAddress1.value = address1.trim()
    senderAddress3.value = address3.trim()
    senderAddressDetail.value = ''
    updateSenderAddress()
    // 상세주소 입력창으로 포커스 이동
    setTimeout(() => {
      senderDetailInputRef.value?.$el?.querySelector?.('input')?.focus() ||
        senderDetailInputRef.value?.focus?.()
    }, 100)
  } else if (formNum === 2) {
    // 2: 수신처(발송지) 주소
    recipientAddress1.value = address1.trim()
    recipientAddress3.value = address3.trim()
    recipientAddressDetail.value = ''
    updateRecipientAddress()
    // 상세주소 입력창으로 포커스 이동
    setTimeout(() => {
      recipientDetailInputRef.value?.$el?.querySelector?.('input')?.focus() ||
        recipientDetailInputRef.value?.focus?.()
    }, 100)
  }
}

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
        sender_display_type: letter.sender_display_type || 'company_only',
        sender_duty_title: letter.sender_duty_title || '',
        sender_name: letter.sender_name || '',
        co_seal: letter.co_seal || null,
        is_solo_approval: !!letter.is_solo_approval,
        dispatch_method: letter.dispatch_method || 'email',
        tracking_number: letter.tracking_number || '',
      }
      senderAddress1.value = letter.sender_address || ''
      senderAddress3.value = ''
      senderAddressDetail.value = ''
      recipientAddress1.value = letter.recipient_address || ''
      recipientAddress3.value = ''
      recipientAddressDetail.value = ''
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

      // 경유나 참조 값이 있으면 펼침 상태로 유지
      if (letter.via || letter.recipient_reference) {
        showViaRef.value = true
      }
      // 발신지 주소 입력값이 있으면 펼침 상태로 유지
      if (letter.sender_address || letter.sender_zipcode) {
        showCustomAddress.value = true
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

    <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
      <CRow>
        <!-- 좌측: 공문서 작성/수정 폼 (lg: 6, xl: 7) -->
        <CCol lg="6" xl="7">
          <!-- 1. 공문서 서식 영역 (PDF 템플릿과 동일 순서) -->
          <CCard class="mb-4 shadow-sm border">
            <CCardHeader
              class="py-3 bg-transparent border-bottom d-flex justify-content-between align-items-center"
            >
              <div class="d-flex align-items-center">
                <v-icon
                  icon="mdi-file-document-outline"
                  size="small"
                  :color="isEdit ? 'success' : 'primary'"
                  class="me-2"
                />
                <strong class="text-body" style="font-size: 0.95rem">
                  공문서 서식 (PDF 인쇄 영역)
                </strong>
              </div>
              <CBadge
                :color="isEdit ? 'success' : 'primary'"
                shape="rounded-pill"
                class="px-2 py-1 font-monospace"
                style="font-size: 0.72rem"
              >
                {{ isEdit ? '수정 모드' : '신규 작성' }}
              </CBadge>
            </CCardHeader>
            <CCardBody>
              <!-- 수신 / (경유) / 참조 / 제목 (정돈된 공문서 서식 레이아웃) -->
              <div class="letter-meta-box p-3 rounded mb-4 border bg-light">
                <div
                  class="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom"
                >
                  <div class="d-flex align-items-center">
                    <v-icon
                      icon="mdi-card-account-mail"
                      color="primary"
                      size="small"
                      class="me-2"
                    />
                    <strong class="text-primary" style="font-size: 0.95rem">
                      수신 및 제목 정보
                    </strong>
                  </div>
                  <!-- 경유/참조 토글 버튼 -->
                  <v-btn
                    variant="text"
                    density="compact"
                    size="small"
                    color="info"
                    class="px-2 text-none"
                    @click="showViaRef = !showViaRef"
                  >
                    <v-icon
                      :icon="showViaRef ? 'mdi-chevron-up' : 'mdi-plus-circle-outline'"
                      size="small"
                      class="me-1"
                    />
                    {{ showViaRef ? '경유·참조 접기' : '경유·참조 추가' }}
                  </v-btn>
                </div>

                <!-- 1행: 수신처(메인) & 발신 요청/예정일 -->
                <CRow class="mb-3 align-items-start">
                  <CCol md="6">
                    <CRow>
                      <CFormLabel class="col-md-2 col-form-label required"> 수신 </CFormLabel>
                      <CCol>
                        <CFormInput
                          v-model="form.recipient_name"
                          placeholder="수신처 명칭 (예: 주식회사 한국건설, 서초구청장 등)"
                          required
                          :feedback-invalid="'수신처명을 입력해주세요.'"
                        />
                      </CCol>
                    </CRow>
                  </CCol>
                  <CCol md="6">
                    <CRow>
                      <CFormLabel class="col-md-2 col-form-label required">
                        발신 요청(예정)일
                      </CFormLabel>
                      <CCol>
                        <div
                          :class="{
                            'is-invalid-wrapper': validated && !form.issue_date,
                            'is-valid-wrapper': validated && !!form.issue_date,
                          }"
                        >
                          <DatePicker
                            v-model="form.issue_date"
                            placeholder="발신 요청일 선택"
                            required
                          />
                        </div>
                        <div v-if="validated && !form.issue_date" class="text-danger small mt-1">
                          발신 요청(예정)일을 선택해주세요.
                        </div>
                      </CCol>
                    </CRow>
                  </CCol>
                </CRow>

                <!-- 2행: 경유 & 참조 (토글 펼침 또는 값이 있을 때 노출) -->
                <CRow
                  v-if="showViaRef"
                  class="mb-3 pt-2 pb-1 border border-light-subtle rounded mx-0"
                >
                  <CCol md="6" class="py-1">
                    <CRow>
                      <CFormLabel class="col-2 col-form-label">경유</CFormLabel>
                      <CCol>
                        <CFormInput
                          v-model="form.via"
                          placeholder="경유 기관 또는 부서 (예: 총무과, 감리단 등)"
                        />
                      </CCol>
                    </CRow>
                  </CCol>
                  <CCol md="6" class="py-1">
                    <CRow>
                      <CFormLabel class="col-2 col-form-label">참조</CFormLabel>
                      <CCol>
                        <CFormInput
                          v-model="form.recipient_reference"
                          placeholder="참조 부서 또는 직위 (예: 대표이사 귀하, 회계팀)"
                        />
                      </CCol>
                    </CRow>
                  </CCol>
                </CRow>

                <!-- 3행: 제목 (시각적 위계 강화 - 굵은 글씨 및 또렷한 서식) -->
                <CRow class="mt-2">
                  <CCol md="12">
                    <CRow>
                      <CFormLabel class="col-md-1 col-form-label required"> 제목 </CFormLabel>
                      <CCol>
                        <CFormInput
                          v-model="form.title"
                          placeholder="공문 제목을 명확하고 간결하게 입력하세요"
                          class="fw-semibold title-input"
                          required
                          :feedback-invalid="'공문 제목을 입력해주세요.'"
                        />
                      </CCol>
                    </CRow>
                  </CCol>
                </CRow>
              </div>

              <!-- 본문 내용 -->
              <div class="mb-4">
                <CFormLabel class="fw-bold">
                  본문 내용 <span class="text-danger">*</span>
                </CFormLabel>
                <div
                  class="md-editor-validation-wrapper"
                  :class="{
                    'is-invalid-editor': validated && !form.content,
                    'is-valid-editor': validated && !!form.content,
                  }"
                >
                  <MdEditor
                    v-model="form.content"
                    placeholder="공문 본문 내용을 입력하세요. (상단 툴바를 이용해 표, 굵게, 글머리 기호 등을 자유롭게 작성할 수 있습니다.)"
                    :height="360"
                    :preview="false"
                  />
                </div>
                <div v-if="validated && !form.content" class="text-danger small mt-1">
                  공문 본문 내용을 입력해주세요.
                </div>
                <CFormText class="text-muted">
                  마크다운 서식(표, 글머리 기호, 굵은 글씨 등)은 공문 인쇄 및 PDF 생성 시 표준
                  서식으로 자동 반영됩니다.
                </CFormText>
              </div>

              <!-- 붙임(첨부) 목록 -->
              <div class="mb-4 p-3 bg-light rounded border">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <CFormLabel class="fw-bold mb-0"> 붙임 (첨부 서류 목록) </CFormLabel>
                  <!-- 붙임 방식 토글 (Vuetify 세그먼트 컨트롤) -->
                  <v-btn-toggle
                    v-model="attachmentInputMode"
                    mandatory
                    density="compact"
                    color="blue-grey-darken-1"
                  >
                    <v-btn value="file" size="small" class="px-3 text-none">
                      <v-icon icon="mdi-paperclip" size="small" class="me-1" />
                      파일 첨부 (권장)
                    </v-btn>
                    <v-btn value="text" size="small" class="px-3 text-none">
                      <v-icon icon="mdi-format-list-bulleted" size="small" class="me-1" />
                      텍스트 직접 입력
                    </v-btn>
                  </v-btn-toggle>
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
                      class="p-2 mb-2 bg-more-white rounded border d-flex justify-content-between align-items-center"
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
                      class="p-3 mb-2 bg-more-white rounded border position-relative"
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
                            <span class="text-muted fw-normal">
                              (공문서 본문에 인쇄될 공식 명칭)
                            </span>
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
                  <v-btn color="info" size="small" @click="fileInputRef?.click()">
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
                <!-- 1. 발송 유형 및 발신 명의 표기 형태 (상단 핵심 컨트롤) -->
                <div
                  class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3 pb-2 border-bottom"
                >
                  <div class="d-flex align-items-center">
                    <v-icon icon="mdi-draw-pen" color="primary" size="small" class="me-2" />
                    <strong class="text-primary" style="font-size: 0.95rem">
                      발신 명의 및 직인 설정
                    </strong>
                  </div>

                  <!-- 발송 방식 토글 (전자결재 vs 단독/직접) -->
                  <v-btn-toggle
                    v-model="approvalMode"
                    mandatory
                    density="compact"
                    color="blue-grey-darken-1"
                  >
                    <v-btn value="approval" size="small" class="px-3 text-none">
                      <v-icon icon="mdi-shield-check" size="small" class="me-1" />
                      전자결재 상신 발송
                    </v-btn>
                    <v-btn value="manual" size="small" class="px-3 text-none">
                      <v-icon icon="mdi-pencil" size="small" class="me-1" />
                      단독 / 직접 발송
                    </v-btn>
                  </v-btn-toggle>
                </div>

                <!-- 1. 발신 명의 및 날인 직인 일체형 설정 카드 -->
                <div class="mb-3 p-3 bg-more-white rounded border">
                  <!-- 발신 명의 표기 형태 선택 (회사명만 / 회사명+직책성명 / 공동대표 병기) -->
                  <div
                    class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2"
                  >
                    <span class="small fw-semibold text-secondary">
                      <v-icon icon="mdi-format-title" size="small" class="me-1 text-primary" />
                      하단 발신 명의 형태
                    </span>
                    <v-btn-toggle
                      v-model="form.sender_display_type"
                      mandatory
                      density="compact"
                      color="blue-grey-lighten-1"
                      @update:model-value="(val: any) => (form.sender_display_type = val)"
                    >
                      <v-btn value="company_only" size="small" class="px-3 text-none">
                        회사명 + 인장 표기
                      </v-btn>
                      <v-btn value="company_rep" size="small" class="px-3 text-none">
                        회사명 + 발송 승인자 직책·성명
                      </v-btn>
                      <v-btn value="co_rep" size="small" class="px-3 text-none">
                        공동대표 병기 (각각 날인)
                      </v-btn>
                    </v-btn-toggle>
                  </div>
                  <small class="text-muted d-block mb-3" style="font-size: 0.76rem">
                    <template v-if="form.sender_display_type === 'company_only'">
                      • 일반 대외 공문 기본형: '{{ currentCompany?.name || '회사명' }} [직인]'
                      형태로 날인됩니다.
                    </template>
                    <template v-else-if="form.sender_display_type === 'company_rep'">
                      • 격식/계약성 공문형: '{{ currentCompany?.name || '회사명' }}
                      {{ approverDutyTitle }} {{ finalApproverName }} [직인]' 형태로 날인됩니다.
                    </template>
                    <template v-else>
                      • 공동대표 체제 전용: 2인의 공동대표이사 직함·성명 및 인장 2개가 좌우 나란히
                      날인됩니다.
                    </template>
                  </small>

                  <hr class="my-2 border-light" />

                  <!-- 날인 인감 선택 (인장 1 & 공동대표 인장 2) -->
                  <CRow class="g-2 align-items-start">
                    <!-- 제1 날인 인감 -->
                    <CCol md="6">
                      <CFormLabel class="small fw-semibold mb-1">
                        <v-icon icon="mdi-seal" size="small" class="me-1 text-secondary" />
                        {{
                          form.sender_display_type === 'co_rep'
                            ? '공동대표 인장 1'
                            : '날인 인감 (직인)'
                        }}
                      </CFormLabel>
                      <CFormSelect
                        :value="form.seal || ''"
                        @change="
                          form.seal = Number(($event.target as HTMLSelectElement).value) || null
                        "
                      >
                        <option value="">인장 미선택 / (직인생략 / 출력 후 실물날인)</option>
                        <option v-for="s in availableSealList" :key="s.pk" :value="s.pk">
                          {{ s.name }} ({{ s.seal_type_desc || s.seal_type }}){{
                            s.purpose ? ` [${s.purpose}]` : ''
                          }}{{ s.custody_type === 'external' ? ' (외부교부)' : '' }} - 전자날인
                        </option>
                      </CFormSelect>

                      <!-- 인장 뱃지 및 메타 정보 -->
                      <div
                        v-if="selectedSeal"
                        class="d-flex align-items-center gap-2 mt-2 p-2 bg-light rounded border"
                      >
                        <img
                          v-if="selectedSealImage"
                          :src="selectedSealImage"
                          alt="인장1"
                          style="width: 36px; height: 36px; object-fit: contain"
                          class="border rounded p-1 bg-more-white"
                        />
                        <div class="flex-grow-1">
                          <div class="d-flex flex-wrap gap-1 align-items-center">
                            <CBadge color="success" class="me-1">
                              <v-icon icon="mdi-check-circle" size="x-small" class="me-1" />
                              PDF 전자날인
                            </CBadge>
                            <CBadge v-if="selectedSeal.purpose" color="info">
                              용도: {{ selectedSeal.purpose }}
                            </CBadge>
                            <CBadge v-if="selectedSeal.internal_manager_name" color="secondary">
                              책임자: {{ selectedSeal.internal_manager_duty }}
                              {{ selectedSeal.internal_manager_name }}
                            </CBadge>
                            <CBadge
                              v-if="approvalMode === 'approval' && selectedSeal.route_template_name"
                              color="primary"
                            >
                              결재선: {{ selectedSeal.route_template_name }}
                            </CBadge>
                            <CBadge
                              v-else-if="
                                approvalMode === 'approval' && selectedSeal.final_approval_duty_name
                              "
                              color="primary"
                            >
                              {{ selectedSeal.final_approval_duty_name }} 전결
                            </CBadge>
                          </div>
                        </div>
                      </div>
                    </CCol>

                    <!-- 제2 날인 인감 (공동대표 병기 모드일 때만 활성화) -->
                    <CCol v-if="form.sender_display_type === 'co_rep'" md="6">
                      <CFormLabel class="small fw-semibold mb-1">
                        <v-icon icon="mdi-seal" size="small" class="me-1 text-secondary" />
                        공동대표 인장 2 (보조 직인)
                      </CFormLabel>
                      <CFormSelect
                        :value="form.co_seal || ''"
                        @change="
                          form.co_seal = Number(($event.target as HTMLSelectElement).value) || null
                        "
                      >
                        <option value="">보조 인장 미선택 / (직인생략 / 실물날인)</option>
                        <option v-for="s in availableSealList" :key="s.pk" :value="s.pk">
                          {{ s.name }} ({{ s.seal_type_desc || s.seal_type }}){{
                            s.purpose ? ` [${s.purpose}]` : ''
                          }}{{ s.custody_type === 'external' ? ' (외부교부)' : '' }} - 전자날인
                        </option>
                      </CFormSelect>

                      <div
                        v-if="selectedCoSeal"
                        class="d-flex align-items-center gap-2 mt-2 p-2 bg-light rounded border"
                      >
                        <img
                          v-if="selectedCoSealImage"
                          :src="selectedCoSealImage"
                          alt="인장2"
                          style="width: 36px; height: 36px; object-fit: contain"
                          class="border rounded p-1 bg-more-white"
                        />
                        <div class="flex-grow-1">
                          <div class="d-flex flex-wrap gap-1 align-items-center">
                            <CBadge color="success" class="me-1">
                              <v-icon icon="mdi-check-circle" size="x-small" class="me-1" />
                              대표 2 전자날인
                            </CBadge>
                            <CBadge v-if="selectedCoSeal.purpose" color="info">
                              용도: {{ selectedCoSeal.purpose }}
                            </CBadge>
                            <CBadge v-if="selectedCoSeal.internal_manager_name" color="secondary">
                              책임자: {{ selectedCoSeal.internal_manager_duty }}
                              {{ selectedCoSeal.internal_manager_name }}
                            </CBadge>
                          </div>
                        </div>
                      </div>
                    </CCol>
                  </CRow>

                  <!-- 단독/직접 발송 시: 발송 승인자 직접 지정 (회사명 + 직책·성명 선택 시) -->
                  <CRow
                    v-if="approvalMode === 'manual' && form.sender_display_type === 'company_rep'"
                    class="mb-3 p-2 bg-light rounded border align-items-center g-2"
                  >
                    <CCol md="6">
                      <CFormLabel class="small fw-semibold text-primary mb-1">
                        <v-icon icon="mdi-badge-account" size="small" class="me-1" />
                        발송 승인자 직책
                      </CFormLabel>
                      <CFormInput
                        v-model="form.sender_duty_title"
                        size="sm"
                        :placeholder="`직책을 입력하세요. (기본값: ${selectedSeal?.internal_manager_duty || approverDutyTitle})`"
                      />
                    </CCol>
                    <CCol md="6">
                      <CFormLabel class="small fw-semibold text-primary mb-1">
                        <v-icon icon="mdi-account" size="small" class="me-1" />
                        발송 승인자 성명
                      </CFormLabel>
                      <CFormInput
                        v-model="form.sender_name"
                        size="sm"
                        :placeholder="`이름을 입력하세요. (기본값: ${selectedSeal?.internal_manager_name || representativeName})`"
                      />
                    </CCol>
                    <CCol md="12">
                      <small class="text-muted" style="font-size: 0.74rem">
                        * 비워두면 인장의 전결/책임자 기준({{
                          selectedSeal?.internal_manager_duty || approverDutyTitle
                        }}
                        {{ selectedSeal?.internal_manager_name || representativeName }})이 자동
                        적용됩니다.
                      </small>
                    </CCol>
                  </CRow>
                </div>

                <!-- 4. 수동 발송 모드 시 기안자 및 단독결재 설정 -->
                <div v-if="approvalMode === 'manual'" class="mb-3 p-2 bg-more-white rounded border">
                  <div class="d-flex flex-wrap align-items-center justify-content-between gap-3">
                    <!-- 좌측: 일반적인 기안/담당자 정보 입력 (단독 기안 아닐 때) -->
                    <div
                      v-if="!form.is_solo_approval"
                      class="d-flex flex-wrap align-items-center gap-2 flex-grow-1"
                    >
                      <div style="min-width: 160px; max-width: 220px" class="flex-grow-1">
                        <CFormLabel class="small fw-semibold mb-1">
                          기안/담당자명 <span class="text-danger">*</span>
                        </CFormLabel>
                        <CFormInput
                          v-model="form.drafter_name"
                          size="sm"
                          placeholder="예: 홍길동"
                          required
                          :feedback-invalid="'기안/담당자명을 입력해주세요.'"
                        />
                      </div>
                      <div style="min-width: 140px; max-width: 180px" class="flex-grow-1">
                        <CFormLabel class="small fw-semibold mb-1">담당 직책</CFormLabel>
                        <CFormInput
                          v-model="form.drafter_position"
                          size="sm"
                          placeholder="예: 팀장, 소장, 본부장"
                        />
                      </div>
                    </div>
                    <!-- 단독 기안일 때 좌측 안내 문구 -->
                    <div v-else class="text-muted small py-2 flex-grow-1">
                      <v-icon
                        icon="mdi-information-outline"
                        size="small"
                        class="me-1 text-primary"
                      />
                      승인권자({{ approverDutyTitle }}) 직접 기안으로 하단 담당자란이 생략됩니다.
                    </div>

                    <!-- 우측 끝 항상 고정 정렬: 승인권자 직접 기안(단독결재) 체크박스 -->
                    <div class="text-end ms-auto ps-2 border-start">
                      <CFormCheck
                        id="is_solo_approval_check"
                        v-model="form.is_solo_approval"
                        :label="`승인권자(${approverDutyTitle}) 직접 기안`"
                        class="small fw-semibold justify-content-end mb-1"
                      />
                      <small class="text-muted d-block text-end" style="font-size: 0.73rem">
                        (예외: 담당자란 생략 단독 승인/시행)
                      </small>
                    </div>
                  </div>
                </div>

                <hr class="my-2 text-muted" />

                <!-- 5. 하단 부가 설정 (발신지 주소 토글 & 공개 구분) -->
                <div class="d-flex flex-wrap justify-content-between align-items-center gap-2">
                  <!-- 좌측: 발신지 주소 직접 지정 (현장/지사) 토글 -->
                  <div>
                    <v-btn
                      variant="text"
                      density="compact"
                      size="small"
                      color="secondary"
                      class="px-1 text-none"
                      @click="showCustomAddress = !showCustomAddress"
                    >
                      <v-icon
                        :icon="showCustomAddress ? 'mdi-chevron-up' : 'mdi-map-marker-plus-outline'"
                        size="small"
                        class="me-1"
                      />
                      {{
                        showCustomAddress ? '발신지 주소 접기' : '발신 주소 변경 (현장/지사 발송)'
                      }}
                    </v-btn>
                    <small
                      v-if="!showCustomAddress"
                      class="text-muted ms-2"
                      style="font-size: 0.75rem"
                    >
                      (기본: {{ currentCompany?.name || '본사' }} 기본 주소 인쇄)
                    </small>
                  </div>

                  <!-- 우측: 공개 구분 선택 (컴팩트 인라인 배치) -->
                  <div class="d-flex align-items-center gap-2">
                    <span class="small fw-semibold text-secondary text-nowrap">
                      공개 구분 <span class="text-danger">*</span>
                    </span>
                    <CFormSelect v-model="form.disclosure_type" size="sm" style="width: 140px">
                      <option value="1">공개</option>
                      <option value="2">부분공개</option>
                      <option value="3">비공개 (대외비)</option>
                    </CFormSelect>
                  </div>
                </div>

                <!-- 6. 발신 주소 펼침 영역 -->
                <div v-if="showCustomAddress" class="mt-2 p-2 bg-more-white rounded border">
                  <CRow class="g-2">
                    <CCol :xs="12" :md="4">
                      <CFormLabel class="small mb-1">발신 우편번호</CFormLabel>
                      <CInputGroup size="sm">
                        <CFormInput
                          v-model="form.sender_zipcode"
                          size="sm"
                          placeholder="우편번호"
                          readonly
                          style="cursor: pointer"
                          @click="refPostCode?.initiate(1)"
                        />
                        <CButton
                          type="button"
                          color="secondary"
                          variant="outline"
                          size="sm"
                          @click="refPostCode?.initiate(1)"
                        >
                          <v-icon icon="mdi-magnify" size="small" class="me-1" />
                          검색
                        </CButton>
                      </CInputGroup>
                    </CCol>
                    <CCol :xs="12" :md="4">
                      <CFormLabel class="small mb-1">기본 도로명 주소</CFormLabel>
                      <CFormInput
                        v-model="senderAddressBase"
                        size="sm"
                        placeholder="주소 검색 시 자동 입력"
                        readonly
                        style="cursor: pointer"
                        @click="refPostCode?.initiate(1)"
                      />
                    </CCol>
                    <CCol :xs="12" :md="4">
                      <CFormLabel class="small mb-1">상세 주소 (현장 사무실 등)</CFormLabel>
                      <CFormInput
                        ref="senderDetailInputRef"
                        v-model="senderAddressDetail"
                        size="sm"
                        placeholder="동·호수, 상세 사무소명"
                        @input="updateSenderAddress"
                      />
                    </CCol>
                  </CRow>
                </div>
              </div>
            </CCardBody>
          </CCard>

          <!-- 2. 발송 및 대장 관리 메타 영역 (공문서에는 인쇄되지 않는 업무 관리 데이터) -->
          <CCard class="mb-4 shadow-sm border">
            <CCardHeader class="py-3 bg-transparent border-bottom d-flex align-items-center">
              <v-icon icon="mdi-folder-open-outline" size="small" color="secondary" class="me-2" />
              <strong class="text-body" style="font-size: 0.95rem"> 발송 및 대장 관리 정보 </strong>
              <small class="text-muted ms-2">(시스템 관리용 메타데이터)</small>
            </CCardHeader>
            <CCardBody>
              <CAlert color="success" class="py-2 mb-3">
                <small>
                  <v-icon icon="mdi-information-outline" size="small" class="me-1" />
                  아래 정보는 공문서 본문에는 인쇄되지 않으며, 우편 라벨 출력, 등기번호 추적 및 발송
                  대장 이력 관리에 사용됩니다.
                </small>
              </CAlert>

              <CRow class="mb-3">
                <CCol :xs="12" :md="4">
                  <CFormLabel>수신처 기본 주소</CFormLabel>
                  <CInputGroup>
                    <CFormInput
                      v-model="recipientAddressBase"
                      placeholder="주소 검색 시 자동 입력"
                      readonly
                      style="cursor: pointer"
                      @click="refPostCode?.initiate(2)"
                    />
                    <CButton
                      type="button"
                      color="secondary"
                      variant="outline"
                      @click="refPostCode?.initiate(2)"
                    >
                      <v-icon icon="mdi-magnify" size="small" class="me-1" />
                      주소 검색
                    </CButton>
                  </CInputGroup>
                </CCol>
                <CCol :xs="12" :md="4">
                  <CFormLabel>상세 주소</CFormLabel>
                  <CFormInput
                    ref="recipientDetailInputRef"
                    v-model="recipientAddressDetail"
                    placeholder="층·호수·부서명"
                    @input="updateRecipientAddress"
                  />
                </CCol>
                <CCol :xs="12" :md="4">
                  <CFormLabel>수신처 연락처/담당자</CFormLabel>
                  <CFormInput
                    v-model="form.recipient_contact"
                    placeholder="수신처 담당자 전화번호, 휴대폰 등"
                  />
                </CCol>
              </CRow>

              <CRow class="mb-2">
                <CCol :xs="12" :md="4">
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
                <CCol :xs="12" :md="4">
                  <CFormLabel>등기 / 송장 번호</CFormLabel>
                  <CFormInput
                    v-model="form.tracking_number"
                    placeholder="13자리 등기번호 또는 택배 송장번호"
                  />
                </CCol>
                <CCol :xs="12" :md="4">
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
          <LetterA4Preview
            :form="form"
            :current-company="currentCompany"
            :selected-seal="selectedSeal"
            :selected-seal-image="selectedSealImage"
            :selected-co-seal="selectedCoSeal"
            :selected-co-seal-image="selectedCoSealImage"
            :representatives-list="representativesList"
            :representative-name="representativeName"
            :approver-duty-title="approverDutyTitle"
            :final-approver-name="finalApproverName"
            :approval-mode="approvalMode"
            :is-solo-approval="isSoloApproval"
            :sender-contact="senderContact"
            :clean-drafter-name="cleanDrafterName"
            :next-doc-number="nextDocNumber"
            :attachment-input-mode="attachmentInputMode"
            :pending-attachments="pendingAttachments"
          />
        </CCol>
      </CRow>
    </CForm>

    <!-- 우편번호 및 도로명 주소 검색 레이어 모달 -->
    <DaumPostcode ref="refPostCode" @address-callback="addressCallback" />
  </div>
</template>

<style scoped>
.title-input {
  font-size: 1.02rem;
  font-weight: 600;
  letter-spacing: -0.2px;
}

.letter-meta-box {
  background-color: #f8fafc;
  border-color: #e2e8f0 !important;
}

/* DatePicker 유효성 검사 테두리 스타일 */
.is-invalid-wrapper :deep(.dp__input) {
  border-color: var(--cui-form-invalid-border-color, #e55353) !important;
  box-shadow: 0 0 0 0.25rem rgba(229, 83, 83, 0.25);
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' width='12' height='12' fill='none' stroke='%23e55353'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath stroke-linejoin='round' d='M5.8 3.6h.4L6 6.5z'/%3e%3ccircle cx='6' cy='8.2' r='.6' fill='%23e55353' stroke='none'/%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right calc(0.375em + 0.1875rem) center;
  background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
}

.is-valid-wrapper :deep(.dp__input) {
  border-color: var(--cui-form-valid-border-color, #2eb85c) !important;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3e%3cpath fill='%232eb85c' d='M2.3 6.73.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z'/%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right calc(0.375em + 0.1875rem) center;
  background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
}

/* MdEditor 유효성 검사 테두리 스타일 */
.md-editor-validation-wrapper {
  border-radius: 6px;
  transition:
    border-color 0.15s ease-in-out,
    box-shadow 0.15s ease-in-out;
}

.is-invalid-editor :deep(.md-editor) {
  border: 1.5px solid var(--cui-form-invalid-border-color, #e55353) !important;
  border-radius: 6px;
}

.is-valid-editor :deep(.md-editor) {
  border: 1.5px solid var(--cui-form-valid-border-color, #2eb85c) !important;
  border-radius: 6px;
}
</style>
