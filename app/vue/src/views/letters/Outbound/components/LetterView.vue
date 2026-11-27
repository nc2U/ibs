<script setup lang="ts">
import { type ComponentPublicInstance, computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { downloadFile, markdownRender, sanitizeExternalUrl } from '@/utils/helper.ts'
import { type AddressData, callAddress } from '@/components/DaumPostcode/address'
import type { OfficialLetter } from '@/store/types/docs'
import type { LetterFilter } from '@/store/pinia/docs.ts'
import { useDocs } from '@/store/pinia/docs.ts'
import { useApproval } from '@/store/pinia/approval'
import LetterA4Preview from './LetterA4Preview.vue'
import DaumPostcode from '@/components/DaumPostcode/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import {
  composeAddress,
  formatDateTimeStr,
  formatShortDate,
  getLocalTodayStr,
  parseRepresentatives,
  resolveApproverDutyTitle,
  resolveFinalApproverName,
  resolveRepresentativeName,
  resolveSenderContact,
  splitStoredAddress,
  stripDrafterTitles,
  useLetterPerms,
} from '@/views/letters/utils/letterMeta'

const props = withDefaults(
  defineProps<{
    letter: OfficialLetter | null
    viewRoute: string
    letterFilter: LetterFilter
    pdfLoading?: boolean
  }>(),
  {
    pdfLoading: false,
  },
)

const emit = defineEmits<{
  (e: 'onDelete', pk: number): void
  (e: 'generatePdf', pk: number): void
}>()

const { accStore, comStore, hasPerm, PERM } = useLetterPerms()
const canDocsCreate = computed(() => hasPerm(PERM.DOCS_CREATE))
const canDocsUpdate = computed(() => hasPerm(PERM.DOCS_UPDATE))
const canDocsDelete = computed(() => hasPerm(PERM.DOCS_DELETE))

const router = useRouter()
const docStore = useDocs()
const appStore = useApproval()

const currentCompany = computed(() => comStore.company)
const sealList = computed(() => comStore.sealList)

const representativesList = computed(() =>
  parseRepresentatives(currentCompany.value?.ceo, props.letter?.sender_display_type === 'co_rep'),
)

const representativeName = computed(() =>
  resolveRepresentativeName(currentCompany.value, representativesList.value),
)

const selectedSeal = computed(() => {
  if (!props.letter?.seal) return null
  return (
    sealList.value.find(item => item.pk === props.letter?.seal) || props.letter?.seal_detail || null
  )
})
const selectedSealImage = computed(() => {
  return props.letter?.seal_detail?.seal_image || selectedSeal.value?.seal_image || null
})

const selectedCoSeal = computed(() => {
  if (!props.letter?.co_seal) return null
  return (
    sealList.value.find(item => item.pk === props.letter?.co_seal) ||
    props.letter?.co_seal_detail ||
    null
  )
})
const selectedCoSealImage = computed(() => {
  return props.letter?.co_seal_detail?.seal_image || selectedCoSeal.value?.seal_image || null
})

const approverDutyTitle = computed(() =>
  resolveApproverDutyTitle(props.letter?.sender_duty_title, selectedSeal.value),
)

const cleanDrafterName = computed(() => stripDrafterTitles(props.letter?.drafter_name))

const finalApproverName = computed(() =>
  resolveFinalApproverName({
    senderName: props.letter?.sender_name,
    seal: selectedSeal.value,
    dutyTitle: approverDutyTitle.value,
    cleanDrafter: cleanDrafterName.value,
    representativeName: representativeName.value,
  }),
)

const senderContact = computed(() =>
  resolveSenderContact({
    company: currentCompany.value,
    letter: props.letter,
  }),
)

const refConfirmModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)
const confirmAction = ref<'delete' | 'replaceScan' | 'cancelApproval' | null>(null)
const pendingScanFile = ref<File | null>(null)

const scanUploadLoading = ref(false)
const scanFileInputRef = ref<HTMLInputElement | null>(null)
const approvalLoading = ref(false)
const cancelLoading = ref(false)

const isDispatched = computed(() => !!props.letter?.dispatched_at)
const isApproved = computed(() => props.letter?.approval_status === 'approved')
const isPending = computed(() => props.letter?.approval_status === 'pending')

const hasApprovalDoc = computed(() => {
  return (
    props.letter?.approval_mode === 'approval' ||
    !!props.letter?.approval_document ||
    (!!props.letter?.approval_status && props.letter.approval_status !== 'none')
  )
})

const isManager = computed(
  () => !!accStore.superAuth || (!!accStore.workManager && canDocsUpdate.value),
)

const canRegeneratePdf = computed(() => {
  if (isDispatched.value) return false
  if (!canDocsCreate.value) return false
  if (isApproved.value) return isManager.value
  return true
})

const canUploadScan = computed(() => {
  if (!canDocsCreate.value) return false
  if (isDispatched.value) return isManager.value
  return true
})

const canEditLetter = computed(() => {
  if (isDispatched.value) return false
  if (isPending.value) return false
  if (isApproved.value) return false
  return canDocsUpdate.value
})

const canDeleteLetter = computed(() => {
  if (isDispatched.value) return false
  if (isPending.value) return false
  if (isApproved.value) return false
  return canDocsDelete.value
})

const canCancelApproval = computed(() => {
  if (!props.letter?.approval_document || !isPending.value) return false
  return (
    !!accStore.superAuth ||
    (canDocsUpdate.value && accStore.userInfo?.pk === props.letter.creator?.pk)
  )
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
  confirmAction.value = 'delete'
  refConfirmModal.value?.callModal(
    '공문 삭제 확인',
    `문서번호: ${props.letter?.document_number || ''}\n제목: ${props.letter?.title || ''}\n\n이 공문을 삭제하시겠습니까?`,
    'mdi-alert-circle-outline',
    'red-lighten-3',
    '삭제',
    'red-lighten-2',
  )
}

const onGeneratePdf = () => {
  if (!props.letter?.pk || props.pdfLoading) return
  if (isDispatched.value) {
    refAlertModal.value?.callModal(
      'PDF 재생성 제한',
      '이미 대외 발송이 완료된 공문서는 자료 유실 및 변조 방지를 위해 PDF 재생성이 금지됩니다.',
    )
    return
  }
  if (isApproved.value && !isManager.value) {
    refAlertModal.value?.callModal(
      '권한 제한',
      '최종 결재 승인된 공문서는 관리자만 재생성할 수 있습니다.',
    )
    return
  }
  emit('generatePdf', props.letter.pk)
}

const uploadSelectedScanFile = async (file: File) => {
  if (!props.letter?.pk) return
  scanUploadLoading.value = true
  try {
    await docStore.uploadLetterPdf(props.letter.pk, file)
  } finally {
    scanUploadLoading.value = false
    pendingScanFile.value = null
  }
}

const onScanFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''
  if (!file || !props.letter?.pk) return

  if (isDispatched.value && !isManager.value) {
    refAlertModal.value?.callModal(
      '권한 제한',
      '이미 발송 완료된 공문의 스캔 파일 교체는 관리자만 가능합니다.',
    )
    return
  }

  if (!file.name.toLowerCase().endsWith('.pdf')) {
    refAlertModal.value?.callModal('파일 형식 오류', 'PDF 파일(.pdf)만 등록 가능합니다.')
    return
  }

  if (isDispatched.value) {
    pendingScanFile.value = file
    confirmAction.value = 'replaceScan'
    refConfirmModal.value?.callModal(
      '스캔본 교체 확인',
      '이미 발송 완료된 공문서입니다. 등록 시 기존 최종 발송본 파일이 대체됩니다. 계속하시겠습니까?',
      'mdi-alert-circle-outline',
      'warning',
      '교체 등록',
      'warning',
    )
    return
  }

  await uploadSelectedScanFile(file)
}

const downloadPdf = async () => {
  if (!props.letter?.pk) return
  const safeTitle = (props.letter.title || '공문').substring(0, 30).replace(/[\\/\s]+/g, '_')
  const fileName = `${props.letter.document_number || props.letter.pk}_${safeTitle}.pdf`
  await downloadFile(`/api/v1/official-letter/${props.letter.pk}/download_pdf/`, fileName)
}

const onSubmitApproval = async () => {
  if (!props.letter?.pk || !canDocsCreate.value) return
  approvalLoading.value = true
  try {
    await docStore.submitApproval(props.letter.pk)
  } finally {
    approvalLoading.value = false
  }
}

const onCancelApproval = () => {
  if (!props.letter?.approval_document || !canCancelApproval.value) return
  confirmAction.value = 'cancelApproval'
  refConfirmModal.value?.callModal(
    '전자결재 기안 회수',
    '전자결재 기안을 회수하시겠습니까?\n회수 시 결재 진행이 취소되고 문서를 수정하여 다시 상신할 수 있습니다.',
    'mdi-undo-variant',
    'warning',
    '기안 회수',
    'warning',
  )
}

const handleConfirmAction = async () => {
  const action = confirmAction.value
  confirmAction.value = null
  refConfirmModal.value?.close()

  if (action === 'delete' && props.letter?.pk) {
    emit('onDelete', props.letter.pk)
  } else if (action === 'replaceScan' && pendingScanFile.value) {
    await uploadSelectedScanFile(pendingScanFile.value)
  } else if (action === 'cancelApproval' && props.letter?.approval_document) {
    cancelLoading.value = true
    try {
      await appStore.cancelDocument(props.letter.approval_document)
      if (props.letter?.pk) {
        await docStore.fetchLetter(props.letter.pk)
      }
    } finally {
      cancelLoading.value = false
    }
  }
}

const handleModalClose = () => {
  if (confirmAction.value === 'replaceScan') {
    pendingScanFile.value = null
  }
  confirmAction.value = null
}

const goToApprovalDetail = (docId: number) => {
  router.push({ name: '결재 문서함 - 보기', params: { docId } })
}

// ── 발송 및 대장 관리 메타 정보 수정 모달 상태 ────────────────
const showDispatchModal = ref(false)
const dispatchSaving = ref(false)
const refDispatchPostCode = ref<{ initiate: (num: number) => void } | null>(null)
const recipientDetailInputRef = ref<ComponentPublicInstance | HTMLInputElement | null>(null)
const recipientAddress1 = ref('')
const recipientAddress3 = ref('')
const recipientAddressDetail = ref('')

const dispatchForm = ref({
  dispatch_method: 'email',
  tracking_number: '',
  dispatched_at: null as string | null,
  recipient_address: '',
  recipient_contact: '',
})

const updateRecipientAddress = () => {
  dispatchForm.value.recipient_address = composeAddress(
    recipientAddress1.value,
    recipientAddressDetail.value,
    recipientAddress3.value,
  )
}

const focusDetailInput = () => {
  const el = recipientDetailInputRef.value
  if (!el) return
  if ('$el' in el && el.$el instanceof HTMLElement) {
    el.$el.querySelector('input')?.focus()
    return
  }
  if ('focus' in el && typeof el.focus === 'function') {
    el.focus()
  }
}

const postCodeCallback = (data: AddressData) => {
  const { address1, address3 } = callAddress(data)
  recipientAddress1.value = address1.trim()
  recipientAddress3.value = address3.trim()
  recipientAddressDetail.value = ''
  updateRecipientAddress()
  setTimeout(focusDetailInput, 100)
}

const openDispatchModal = () => {
  if (!props.letter) return
  dispatchForm.value = {
    dispatch_method: props.letter.dispatch_method || 'email',
    tracking_number: props.letter.tracking_number || '',
    dispatched_at: props.letter.dispatched_at ? props.letter.dispatched_at.substring(0, 10) : null,
    recipient_address: props.letter.recipient_address || '',
    recipient_contact: props.letter.recipient_contact || '',
  }
  const parsed = splitStoredAddress(props.letter.recipient_address)
  recipientAddress1.value = parsed.base
  recipientAddressDetail.value = parsed.detail
  recipientAddress3.value = parsed.ref
  showDispatchModal.value = true
}

const setTodayDispatched = () => {
  dispatchForm.value.dispatched_at = getLocalTodayStr()
}

const clearDispatchedDate = () => {
  dispatchForm.value.dispatched_at = null
}

const saveDispatchMeta = async () => {
  if (!props.letter?.pk) return
  dispatchSaving.value = true
  try {
    let dispatchedAtPayload: string | null = null
    if (dispatchForm.value.dispatched_at) {
      const orig = props.letter.dispatched_at
      dispatchedAtPayload =
        orig && orig.substring(0, 10) === dispatchForm.value.dispatched_at
          ? orig
          : `${dispatchForm.value.dispatched_at}T00:00:00`
    }
    const payload = {
      pk: props.letter.pk,
      dispatch_method: dispatchForm.value.dispatch_method,
      tracking_number: dispatchForm.value.tracking_number,
      dispatched_at: dispatchedAtPayload,
      recipient_address: dispatchForm.value.recipient_address,
      recipient_contact: dispatchForm.value.recipient_contact,
    }
    const updated = await docStore.patchLetter(props.letter.pk, payload)
    if (updated) {
      showDispatchModal.value = false
    }
  } finally {
    dispatchSaving.value = false
  }
}
</script>

<template>
  <div v-if="letter">
    <!-- Navigation -->
    <CRow class="mb-3">
      <CCol class="d-flex justify-content-between align-items-center">
        <v-btn color="secondary" variant="outlined" size="small" @click="goToList">
          <v-icon icon="mdi-format-list-bulleted" size="small" class="me-1" />
          목록
        </v-btn>
        <div>
          <v-btn color="light" size="small" class="me-1" :disabled="!prevPk" @click="goToPrev">
            <v-icon icon="mdi-chevron-left" size="small" />
            이전
          </v-btn>
          <v-btn color="light" size="small" :disabled="!nextPk" @click="goToNext">
            다음
            <v-icon icon="mdi-chevron-right" size="small" />
          </v-btn>
        </div>
      </CCol>
    </CRow>

    <!-- Status Banner: 발송완료 / 전자결재 연동 / 단독발송 구분 -->
    <CCard
      class="mb-4"
      :class="
        isDispatched ? 'border-success' : hasApprovalDoc ? 'border-primary' : 'border-secondary'
      "
    >
      <CCardBody
        class="d-flex flex-wrap justify-content-between align-items-center py-2 px-3 gap-2"
      >
        <template v-if="isDispatched">
          <div class="d-flex align-items-center">
            <v-icon icon="mdi-truck-check" size="large" class="text-success me-2" />
            <div>
              <strong class="text-success">대외 발송 완료 공문: </strong>
              <span class="text-muted ms-1">
                {{ formatDateTimeStr(letter.dispatched_at, true) }} 발송 완료 (증빙 보관 및
                수정/삭제 불가)
              </span>
              <v-chip
                v-if="letter.approval_document_detail"
                color="info"
                variant="flat"
                size="x-small"
                class="ms-2"
              >
                결재승인 ({{ letter.approval_document_detail.doc_number }})
              </v-chip>
            </div>
          </div>
          <div v-if="letter.approval_document">
            <v-btn
              color="info"
              variant="outlined"
              size="small"
              @click="goToApprovalDetail(letter.approval_document)"
            >
              <v-icon icon="mdi-open-in-new" size="small" class="me-1" />
              연동 결재문서 보기
            </v-btn>
          </div>
        </template>

        <template v-else-if="hasApprovalDoc">
          <div class="d-flex align-items-center">
            <v-icon icon="mdi-shield-check" size="large" class="text-primary me-2" />
            <div>
              <strong>전자결재 연동 상태: </strong>
              <v-chip
                v-if="letter.approval_status === 'approved'"
                color="success"
                variant="flat"
                size="x-small"
                class="ms-1"
              >
                결재 승인완료 ({{ letter.approval_document_detail?.doc_number || '공문' }})
              </v-chip>
              <v-chip
                v-else-if="letter.approval_status === 'pending'"
                color="warning"
                variant="flat"
                size="x-small"
                class="ms-1"
              >
                결재 진행중
              </v-chip>
              <v-chip
                v-else-if="letter.approval_status === 'rejected'"
                color="danger"
                variant="flat"
                size="x-small"
                class="ms-1"
              >
                결재 반려
              </v-chip>
              <v-chip v-else color="secondary" variant="flat" size="x-small" class="ms-1">
                미상신 (임시/초안)
              </v-chip>
            </div>
          </div>
          <div>
            <v-btn
              v-if="letter.approval_document"
              color="info"
              variant="outlined"
              size="small"
              class="me-2"
              @click="goToApprovalDetail(letter.approval_document)"
            >
              <v-icon icon="mdi-open-in-new" size="small" class="me-1" />
              결재 문서 보기
            </v-btn>
            <v-btn
              v-if="canCancelApproval"
              color="warning"
              variant="outlined"
              size="small"
              class="me-2"
              :disabled="cancelLoading"
              @click="onCancelApproval"
            >
              <CSpinner v-if="cancelLoading" size="sm" class="me-1" />
              <v-icon v-else icon="mdi-undo-variant" size="small" class="me-1" />
              기안 회수
            </v-btn>
            <v-btn
              v-if="
                canDocsCreate &&
                (letter.approval_status === 'none' || letter.approval_status === 'rejected')
              "
              color="primary"
              size="small"
              :disabled="approvalLoading"
              @click="onSubmitApproval"
            >
              <CSpinner v-if="approvalLoading" size="sm" class="me-1" />
              <v-icon v-else icon="mdi-send" size="small" class="me-1" />
              {{ letter.approval_status === 'rejected' ? '전자결재 재상신' : '전자결재 상신하기' }}
            </v-btn>
          </div>
        </template>

        <template v-else>
          <div class="d-flex align-items-center">
            <v-icon icon="mdi-file-sign" size="large" class="text-secondary me-2" />
            <div>
              <strong class="text-body">단독 / 직접 발송 공문: </strong>
              <span class="text-muted ms-1" style="font-size: 0.85rem">
                (사내 전자결재 생략 문서 • 직인 실물/전자날인 후 직접 시행·발송)
              </span>
            </div>
          </div>
          <div v-if="canDocsCreate" class="d-flex align-items-center">
            <v-btn
              color="secondary"
              variant="text"
              size="small"
              :disabled="approvalLoading"
              class="text-none"
              title="필요 시 전자결재 문서로 전환하여 품의합니다"
              @click="onSubmitApproval"
            >
              <CSpinner v-if="approvalLoading" size="sm" class="me-1" />
              <v-icon v-else icon="mdi-arrow-right-top" size="small" class="me-1" />
              전자결재로 전환 상신
            </v-btn>
          </div>
        </template>
      </CCardBody>
    </CCard>

    <!-- Main Content & A4 Preview -->
    <CRow>
      <CCol lg="6" xl="7">
        <!-- Letter Header -->
        <CCard class="mb-4">
          <CCardHeader class="d-flex justify-content-between align-items-center">
            <div>
              <v-chip color="info" variant="flat" size="x-small" class="me-2">
                {{ letter.document_number }}
              </v-chip>
              <strong>{{ letter.title }}</strong>
            </div>
            <div>
              <small class="text-muted">
                작성자: {{ letter.creator?.username || '-' }} | 작성일:
                {{ formatDateTimeStr(letter.created, true) }}
              </small>
            </div>
          </CCardHeader>
        </CCard>

        <!-- Letter Info -->
        <CRow>
          <CCol md="6">
            <CCard class="mb-4">
              <CCardHeader>
                <v-icon icon="mdi-card-account-mail" size="small" class="me-1" />
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
                        <v-chip
                          :color="
                            letter.disclosure_type === '3'
                              ? 'danger'
                              : letter.disclosure_type === '2'
                                ? 'warning'
                                : 'success'
                          "
                          variant="flat"
                          size="x-small"
                        >
                          {{
                            letter.disclosure_type_desc ||
                            (letter.disclosure_type === '3'
                              ? '비공개'
                              : letter.disclosure_type === '2'
                                ? '부분공개'
                                : '공개')
                          }}
                        </v-chip>
                      </td>
                    </tr>
                    <tr>
                      <th>시행(발신)일</th>
                      <td>
                        <span v-if="letter.dispatched_at" class="fw-bold text-success">
                          {{ formatShortDate(letter.effective_issue_date || letter.dispatched_at) }}
                          <v-chip color="success" variant="flat" size="x-small" class="ms-1">
                            발송완료
                          </v-chip>
                        </span>
                        <span
                          v-else-if="letter.approval_status === 'approved'"
                          class="fw-bold text-primary"
                        >
                          {{ formatShortDate(letter.effective_issue_date || letter.issue_date) }}
                          <v-chip color="primary" variant="flat" size="x-small" class="ms-1">
                            승인확정
                          </v-chip>
                        </span>
                        <span v-else class="text-secondary">
                          {{ formatShortDate(letter.issue_date) }}
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
                <v-icon icon="mdi-draw-pen" size="small" class="me-1" />
                <strong>발신 및 날인 정보</strong>
              </CCardHeader>
              <CCardBody>
                <table class="table table-borderless mb-0">
                  <tbody>
                    <tr>
                      <th style="width: 100px">날인 인감</th>
                      <td>
                        <div v-if="letter.seal_detail" class="d-flex align-items-center">
                          <span class="me-2">
                            {{ letter.seal_detail.name }} ({{ letter.seal_detail.seal_type_desc }})
                          </span>
                          <img
                            v-if="letter.seal_detail.seal_image"
                            :src="sanitizeExternalUrl(letter.seal_detail.seal_image)"
                            alt="인장"
                            style="width: 28px; height: 28px; object-fit: contain"
                            class="border rounded p-1 bg-more-white"
                          />
                        </div>
                        <span v-else class="text-muted">(직인생략 또는 미선택)</span>
                      </td>
                    </tr>
                    <tr>
                      <th>기안/담당자</th>
                      <td>
                        <span>
                          {{ letter.drafter_name }}
                          {{ letter.drafter_position ? `(${letter.drafter_position})` : '' }}
                        </span>
                        <v-chip
                          v-if="letter.is_solo_approval"
                          color="info"
                          variant="flat"
                          size="x-small"
                          class="ms-1"
                        >
                          승인권자 직접기안
                        </v-chip>
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
            <v-icon icon="mdi-file-document-outline" size="small" class="me-1" />
            <strong>공문 본문</strong>
          </CCardHeader>
          <CCardBody>
            <div
              class="letter-content bg-more-light markdown-content text-body"
              v-html="markdownRender(letter.content)"
            />
          </CCardBody>
        </CCard>

        <!-- Attachment Section -->
        <CCard class="mb-4">
          <CCardHeader>
            <v-icon icon="mdi-paperclip" size="small" class="me-1" />
            <strong>붙임 (첨부 서류 및 파일)</strong>
          </CCardHeader>
          <CCardBody>
            <div v-if="letter.attachment_text" class="mb-3 p-3 bg-more-light rounded border">
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
                    <v-icon icon="mdi-file-outline" size="small" class="me-2 text-primary" />
                    <strong>{{ att.name || att.file_name }}</strong>
                    <span class="text-muted ms-2">({{ att.quantity || '1부' }})</span>
                  </div>
                  <v-btn
                    v-if="typeof att.file === 'string'"
                    color="primary"
                    variant="outlined"
                    size="x-small"
                    @click="
                      downloadFile(
                        sanitizeExternalUrl(att.file),
                        att.file_name || att.name || 'attachment',
                      )
                    "
                  >
                    <v-icon icon="mdi-cloud-download" size="small" class="me-1" /> 다운로드
                  </v-btn>
                </li>
              </ul>
            </div>
            <div v-else-if="!letter.attachment_text" class="text-muted">
              등록된 붙임 서류나 첨부파일이 없습니다.
            </div>
          </CCardBody>
        </CCard>

        <!-- Dispatch Meta Section -->
        <CCard class="mb-4 border-secondary">
          <CCardHeader class="bg-more-light d-flex justify-content-between align-items-center">
            <div>
              <v-icon icon="mdi-truck-delivery-outline" size="small" class="me-1 text-secondary" />
              <strong>발송 및 대장 관리 메타 정보</strong>
            </div>
            <div>
              <v-btn
                v-if="canDocsUpdate"
                color="success"
                variant="flat"
                size="small"
                @click="openDispatchModal"
              >
                <v-icon icon="mdi-pencil-box-outline" size="small" class="me-1" />
                발송 대장 정보 등록/수정
              </v-btn>
            </div>
          </CCardHeader>
          <CCardBody>
            <CRow>
              <CCol md="6">
                <table class="table table-borderless mb-0">
                  <tbody>
                    <tr>
                      <th style="width: 120px">발송 방법</th>
                      <td>
                        <v-chip color="blue-grey-darken-2" variant="flat" size="x-small">
                          {{ letter.dispatch_method_desc || letter.dispatch_method || '이메일' }}
                        </v-chip>
                      </td>
                    </tr>
                    <tr>
                      <th>등기/송장 번호</th>
                      <td>{{ letter.tracking_number || '-' }}</td>
                    </tr>
                    <tr>
                      <th>발송 완료일시</th>
                      <td>{{ formatDateTimeStr(letter.dispatched_at, true) }}</td>
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

        <!-- PDF Section -->
        <CCard class="mb-4">
          <CCardHeader class="d-flex justify-content-between align-items-center">
            <strong>
              <v-icon icon="mdi-file-pdf-box" size="small" class="me-1 text-danger" />
              공문 PDF 파일 (최종 발송/보관본)
            </strong>
            <div>
              <v-chip v-if="isDispatched" color="blue-grey-darken-3" variant="flat" size="x-small">
                대외 발송완료 (재생성 금지)
              </v-chip>
              <v-chip v-else-if="isApproved" color="secondary" variant="flat" size="x-small">
                결재승인완료 (재생성 제한)
              </v-chip>
            </div>
          </CCardHeader>
          <CCardBody>
            <div
              v-if="letter.pdf_file"
              class="d-flex flex-wrap align-items-center justify-content-between gap-3"
            >
              <div class="d-flex flex-wrap align-items-center gap-2">
                <v-chip color="success" class="p-2 me-1">
                  <v-icon icon="mdi-check-circle" size="small" class="me-1" />
                  최종 PDF 등록됨
                </v-chip>

                <template v-if="canUploadScan">
                  <input
                    ref="scanFileInputRef"
                    type="file"
                    accept=".pdf"
                    class="d-none"
                    @change="onScanFileSelect"
                  />
                  <v-btn
                    color="success"
                    variant="flat"
                    size="small"
                    :disabled="scanUploadLoading"
                    @click="scanFileInputRef?.click()"
                  >
                    <CSpinner v-if="scanUploadLoading" size="sm" class="me-1" />
                    <v-icon v-else icon="mdi-cloud-upload" size="small" class="me-1" />
                    실물날인 스캔본(PDF) 업로드/교체
                  </v-btn>
                </template>
                <small v-else-if="isDispatched" class="text-muted">
                  (발송 완료된 공문의 스캔본 교체는 관리자만 가능)
                </small>

                <v-btn
                  v-if="canRegeneratePdf"
                  color="warning"
                  variant="flat"
                  size="small"
                  :disabled="pdfLoading"
                  @click="onGeneratePdf"
                >
                  <CSpinner v-if="pdfLoading" size="sm" class="me-1" />
                  <v-icon v-else icon="mdi-refresh" size="small" class="me-1" />
                  시스템 PDF 재생성
                </v-btn>
                <small v-else-if="isDispatched" class="text-muted ms-1">
                  (발송 완료되어 증빙 보호를 위해 PDF 재생성 불가)
                </small>
                <small v-else-if="isApproved" class="text-muted ms-1">
                  (최종 결재 승인되어 관리자만 시스템 PDF 재생성 가능)
                </small>
              </div>

              <div>
                <v-btn
                  color="light"
                  variant="flat"
                  size="default"
                  class="fw-medium"
                  elevation="1"
                  @click="downloadPdf"
                >
                  <v-icon icon="mdi-cloud-download" color="danger" size="small" class="me-2" />
                  PDF 다운로드
                </v-btn>
              </div>
            </div>

            <div v-else class="d-flex flex-wrap align-items-center justify-content-between gap-3">
              <span class="text-muted">PDF 파일이 아직 생성되거나 등록되지 않았습니다.</span>
              <div class="d-flex align-items-center gap-2">
                <input
                  ref="scanFileInputRef"
                  type="file"
                  accept=".pdf"
                  class="d-none"
                  @change="onScanFileSelect"
                />
                <v-btn
                  v-if="canDocsCreate"
                  color="secondary"
                  variant="outlined"
                  size="small"
                  :disabled="scanUploadLoading"
                  @click="scanFileInputRef?.click()"
                >
                  <CSpinner v-if="scanUploadLoading" size="sm" class="me-1" />
                  <v-icon v-else icon="mdi-cloud-upload" size="small" class="me-1" />
                  스캔본(PDF) 직접 업로드
                </v-btn>

                <v-btn
                  v-if="canDocsCreate"
                  color="primary"
                  variant="flat"
                  size="small"
                  :disabled="pdfLoading"
                  @click="onGeneratePdf"
                >
                  <CSpinner v-if="pdfLoading" size="sm" class="me-1" />
                  <v-icon v-else icon="mdi-file-pdf-box" size="small" class="me-1" />
                  시스템 양식 PDF 생성
                </v-btn>
              </div>
            </div>
          </CCardBody>
        </CCard>

        <!-- Action Buttons -->
        <CRow class="mb-4">
          <CCol class="d-flex justify-content-between align-items-center">
            <div>
              <v-btn
                v-if="canDeleteLetter"
                color="error"
                variant="outlined"
                size="small"
                @click="confirmDelete"
              >
                <v-icon icon="mdi-trash-can-outline" size="small" class="me-1" />
                삭제
              </v-btn>
            </div>

            <div class="d-flex align-items-center gap-2">
              <small v-if="isDispatched" class="text-muted me-2">
                (대외 발송이 완료되어 수정 및 삭제가 제한된 공문입니다)
              </small>
              <small v-else-if="isPending" class="text-muted me-2">
                (전자결재가 진행 중인 공문입니다. 기안을 회수하거나 반려된 후에 수정/삭제할 수
                있습니다)
              </small>
              <small v-else-if="isApproved" class="text-muted me-2">
                (최종 결재 승인되어 내용 수정이 불가합니다)
              </small>

              <v-btn
                v-if="canEditLetter"
                color="success"
                variant="flat"
                size="default"
                @click="goToEdit"
              >
                <v-icon icon="mdi-pencil" size="small" class="me-1" />
                수정
              </v-btn>

              <v-btn
                color="secondary"
                variant="outlined"
                size="default"
                class="ms-1"
                @click="goToList"
              >
                <v-icon icon="mdi-format-list-bulleted" size="small" class="me-1" />
                목록으로
              </v-btn>
            </div>
          </CCol>
        </CRow>
      </CCol>

      <!-- 우측: A4 인쇄 미리보기 컴포넌트 -->
      <CCol lg="6" xl="5" class="d-none d-lg-block">
        <LetterA4Preview
          :form="letter"
          :current-company="currentCompany"
          :selected-seal="selectedSeal"
          :selected-seal-image="selectedSealImage"
          :selected-co-seal="selectedCoSeal"
          :selected-co-seal-image="selectedCoSealImage"
          :representatives-list="representativesList"
          :representative-name="representativeName"
          :approver-duty-title="approverDutyTitle"
          :final-approver-name="finalApproverName"
          :approval-mode="hasApprovalDoc ? 'approval' : 'manual'"
          :is-solo-approval="!!letter.is_solo_approval"
          :sender-contact="senderContact"
          :clean-drafter-name="cleanDrafterName"
          :next-doc-number="letter.document_number || ''"
          :attachment-input-mode="
            letter.attachments && letter.attachments.length > 0 ? 'file' : 'text'
          "
          :pending-attachments="[]"
          :is-view-mode="true"
        />
      </CCol>
    </CRow>

    <!-- Modals -->
    <ConfirmModal
      ref="refConfirmModal"
      @confirm-func="handleConfirmAction"
      @close="handleModalClose"
    />
    <AlertModal ref="refAlertModal" />

    <!-- 발송 및 대장 관리 메타 정보 수정 모달 -->
    <CModal
      :visible="showDispatchModal"
      size="lg"
      alignment="center"
      backdrop="static"
      @close="showDispatchModal = false"
    >
      <CModalHeader>
        <CModalTitle class="d-flex align-items-center">
          <v-icon icon="mdi-truck-delivery-outline" size="small" class="me-2 text-primary" />
          발송 및 대장 관리 정보 등록/수정
        </CModalTitle>
      </CModalHeader>
      <CModalBody>
        <CAlert color="info" class="py-2 mb-3">
          <small>
            <v-icon icon="mdi-information-outline" size="small" class="me-1" />
            이 정보는 공문서 본문 내용(제목, 내용, 인장 등)에 영향을 주지 않으며, 우편 발송 및 대장
            관리를 위한 메타데이터입니다.
          </small>
        </CAlert>

        <CRow class="mb-3">
          <CCol :xs="12" :md="4">
            <CFormLabel>발송 방법</CFormLabel>
            <CFormSelect v-model="dispatchForm.dispatch_method">
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
              v-model="dispatchForm.tracking_number"
              placeholder="등기번호 또는 택배 송장번호"
            />
          </CCol>
          <CCol :xs="12" :md="4">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <CFormLabel class="mb-0">발송 완료일자</CFormLabel>
              <div class="d-flex gap-1">
                <v-btn
                  variant="text"
                  density="compact"
                  size="x-small"
                  color="primary"
                  @click="setTodayDispatched"
                >
                  오늘
                </v-btn>
                <v-btn
                  v-if="dispatchForm.dispatched_at"
                  variant="text"
                  density="compact"
                  size="x-small"
                  color="secondary"
                  @click="clearDispatchedDate"
                >
                  초기화
                </v-btn>
              </div>
            </div>
            <DatePicker
              :model-value="dispatchForm.dispatched_at || ''"
              placeholder="실제 발송 완료일 선택"
              @update:model-value="dispatchForm.dispatched_at = $event || null"
            />
          </CCol>
        </CRow>

        <CRow class="mb-2">
          <CCol :xs="12" :md="5">
            <CFormLabel>수신처 기본 주소</CFormLabel>
            <CInputGroup>
              <CFormInput
                v-model="recipientAddress1"
                placeholder="주소 검색 또는 직접 입력"
                @input="updateRecipientAddress"
              />
              <CButton
                type="button"
                color="secondary"
                variant="outline"
                @click="refDispatchPostCode?.initiate(2)"
              >
                <v-icon icon="mdi-magnify" size="small" class="me-1" />
                검색
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
          <CCol :xs="12" :md="3">
            <CFormLabel>수신처 연락처/담당</CFormLabel>
            <CFormInput
              v-model="dispatchForm.recipient_contact"
              placeholder="전화번호 또는 담당자"
            />
          </CCol>
        </CRow>

        <DaumPostcode ref="refDispatchPostCode" @address-callback="postCodeCallback" />
      </CModalBody>
      <CModalFooter>
        <v-btn
          color="success"
          variant="flat"
          size="small"
          :disabled="dispatchSaving"
          @click="saveDispatchMeta"
        >
          <CSpinner v-if="dispatchSaving" size="sm" class="me-1" />
          <v-icon v-else icon="mdi-content-save-outline" class="me-1" />
          발송 정보 저장
        </v-btn>
        <v-btn color="light" variant="flat" size="small" @click="showDispatchModal = false">
          취소
        </v-btn>
      </CModalFooter>
    </CModal>
  </div>

  <div v-else class="text-center py-5">
    <CSpinner color="primary" />
    <p class="mt-3 text-muted">공문 정보를 불러오는 중...</p>
  </div>
</template>

<style scoped>
.letter-content {
  min-height: 200px;
  padding: 1.25rem;
  border-radius: 4px;
  line-height: 1.8;
}

:deep(.markdown-content) {
  font-size: 0.95rem;
}

:deep(.markdown-content p) {
  margin-bottom: 0.75rem;
}

:deep(.markdown-content p.empty-line) {
  margin-bottom: 0.75rem;
  line-height: 1.8;
}

:deep(.markdown-content table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  white-space: normal;
}

:deep(.markdown-content th),
:deep(.markdown-content td) {
  border: 1px solid var(--cui-border-color, #dee2e6);
  padding: 0.5rem 0.75rem;
  text-align: left;
}

:deep(.markdown-content th) {
  background-color: rgba(128, 128, 128, 0.12);
  font-weight: 600;
}

:deep(.markdown-content ul),
:deep(.markdown-content ol) {
  padding-left: 1.5rem;
  margin-bottom: 0.75rem;
}

:deep(.markdown-content blockquote) {
  border-left: 4px solid #ced4da;
  padding-left: 1rem;
  margin: 0.75rem 0;
  opacity: 0.85;
}
</style>
