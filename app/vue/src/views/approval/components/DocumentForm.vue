<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval'
import { useAccount } from '@/store/pinia/account'
import type { ApprovalContent, DocumentType, SecurityLevel } from '@/store/types/approval'
import api from '@/api'
import { message } from '@/utils/helper'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import { DynamicSchemaForm, STATIC_FORM_REGISTRY } from '@/views/approval/forms'
import { FORM_GUIDES, DEFAULT_GUIDE, type FormGuide } from '../data/formGuides'
import {
  asOptNum,
  asStr,
  extractApprovalAmount,
  filterStaffUserOptions,
  formatFileSize,
  getSafeExternalUrl,
  getUserDisplayName,
  resolveRegistryEntry,
} from '../utils/approvalMeta'

const route = useRoute()
const router = useRouter()
const store = useApproval()
const accStore = useAccount()
const { forDraftDocTypeList, document, myAssignments, routePreview } = storeToRefs(store)
const { usersList, userInfo } = storeToRefs(accStore)
const {
  fetchDocCategoryList,
  fetchForDraftDocTypeList,
  fetchDocument,
  clearDocument,
  fetchMyAssignments,
  fetchRoutePreview,
  clearRoutePreview,
  createDocument,
  updateDocument,
  deleteAttachment,
  submitDocument,
} = store
const { fetchUsersList } = accStore

const isEdit = computed(() => !!route.params.docId)
const saving = ref<'draft' | 'submit' | ''>('')
const validated = ref(false)
const formRef = ref<HTMLFormElement | { $el?: HTMLFormElement } | null>(null)

const refConfirmModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const pendingConfirmType = ref<'delete-attachment' | 'apply-example' | null>(null)
const pendingAttachmentId = ref<number | null>(null)
const pendingExampleTitle = ref('')

const form = ref({
  doc_type: '',
  drafter_assignment: '',
  title: '',
  security_level: '2' as SecurityLevel,
})
const relatedInboundLetterId = ref<number | null>(null)
const dynamicContent = ref<ApprovalContent>({})
const selectedObservers = ref<number[]>([])
const selectedFiles = ref<File[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)

const availableUsers = computed(() => filterStaffUserOptions(usersList.value))

const existingAttachments = computed(() => document.value?.attachments || [])

const onFileSelected = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    for (let i = 0; i < target.files.length; i++) {
      const file = target.files[i]
      if (!selectedFiles.value.some(f => f.name === file.name && f.size === file.size)) {
        selectedFiles.value.push(file)
      }
    }
    target.value = ''
  }
}

const removeSelectedFile = (idx: number) => {
  selectedFiles.value.splice(idx, 1)
}

const removeExistingAttachment = (attachmentId: number) => {
  pendingConfirmType.value = 'delete-attachment'
  pendingAttachmentId.value = attachmentId
  refConfirmModal.value?.callModal(
    '첨부파일 삭제 확인',
    '첨부파일을 삭제하시겠습니까?',
    'mdi-trash-can-outline',
    'red-lighten-3',
    '삭제',
    'error',
  )
}

const selectedDocType = computed<DocumentType | null>(() => {
  const docTypeId = Number(form.value.doc_type)
  if (!docTypeId) return null
  return (
    forDraftDocTypeList.value.find(d => d.id === docTypeId) ??
    (document.value?.doc_type === docTypeId ? (document.value.doc_type_detail ?? null) : null)
  )
})

const currentGuide = computed<FormGuide>(() => {
  return resolveRegistryEntry(FORM_GUIDES, selectedDocType.value) ?? DEFAULT_GUIDE
})

const activeFormComponent = computed(() =>
  resolveRegistryEntry(STATIC_FORM_REGISTRY, selectedDocType.value),
)

const hasFallbackAssignment = computed(
  () =>
    isEdit.value &&
    !!form.value.drafter_assignment &&
    !myAssignments.value.some(a => String(a.pk) === form.value.drafter_assignment),
)

// 카테고리별로 그룹화된 문서 유형 목록 (수정 모드에서 제한/비활성 서식이 목록에 없으면 보조 포함)
const groupedDocTypes = computed(() => {
  const groups: Record<string, DocumentType[]> = {}
  const list = [...forDraftDocTypeList.value]
  if (
    isEdit.value &&
    document.value?.doc_type_detail &&
    !list.some(d => d.id === document.value?.doc_type_detail?.id)
  ) {
    list.push(document.value.doc_type_detail)
  }
  list.forEach(dt => {
    const catName = dt.category_name || '기타/일반'
    if (!groups[catName]) groups[catName] = []
    groups[catName].push(dt)
  })
  return groups
})

// 자주 쓰는 4대 양식 빠른 필터/선택
const quickDocTypes = computed(() => {
  const items = [
    {
      label: '🏖️ 휴가 / 연차',
      matcher: (dt: DocumentType) =>
        (dt.form_template_key || '').toUpperCase().includes('LEAVE') ||
        dt.name.includes('휴가') ||
        (dt.code || '').toUpperCase().includes('VACATION'),
    },
    {
      label: '💳 지출결의서',
      matcher: (dt: DocumentType) =>
        (dt.form_template_key || '').toUpperCase() === 'EXPENSE' ||
        (dt.form_template_key || '').toUpperCase() === 'EXPENSE_REPORT' ||
        dt.name.includes('지출'),
    },
    {
      label: '💼 일반 업무품의',
      matcher: (dt: DocumentType) => {
        const key = (dt.form_template_key || '').toUpperCase()
        return (
          key === 'GENERAL' ||
          key === 'GENERAL_PROPOSAL' ||
          key === 'BIZ_APPROVAL' ||
          key === 'PROPOSAL' ||
          key === 'GENERAL_DRAFT' ||
          dt.name === '업무품의서' ||
          (dt.name.includes('일반') && dt.name.includes('품의'))
        )
      },
    },
    {
      label: '🚗 출장신청서',
      matcher: (dt: DocumentType) =>
        (dt.form_template_key || '').toUpperCase().includes('TRIP') || dt.name.includes('출장'),
    },
  ]

  return items
    .map(item => {
      const matched = forDraftDocTypeList.value.find(item.matcher)
      return matched ? { label: item.label, docType: matched } : null
    })
    .filter(Boolean) as { label: string; docType: DocumentType }[]
})

const selectQuickDocType = (dt: DocumentType) => {
  if (isEdit.value) return
  if (Number(form.value.doc_type) === dt.id) return
  form.value.doc_type = String(dt.id)
  onDocTypeChange()
}

const onDocTypeChange = () => {
  dynamicContent.value = {}
  if (selectedDocType.value?.default_security_level) {
    form.value.security_level = selectedDocType.value.default_security_level
  }
}

const onAssignmentChange = async () => {
  await fetchForDraftDocTypeList(
    form.value.drafter_assignment ? Number(form.value.drafter_assignment) : undefined,
  )
  if (!forDraftDocTypeList.value.some(d => d.id === Number(form.value.doc_type))) {
    form.value.doc_type = ''
    dynamicContent.value = {}
    clearRoutePreview()
    return
  }
  updateRoutePreview(true)
}

// dynamicContent에서 금액 값 추출
const currentAmount = computed<number | null>(() => extractApprovalAmount(dynamicContent.value))

const currentSealId = computed<number | null>(() => asOptNum(dynamicContent.value?.seal_id))

let previewTimer: ReturnType<typeof setTimeout> | null = null
const isInitializing = ref(true)

const updateRoutePreview = (immediate = false) => {
  if (previewTimer) {
    clearTimeout(previewTimer)
    previewTimer = null
  }
  if (!form.value.doc_type) {
    clearRoutePreview()
    return
  }

  const execute = () => {
    previewTimer = null
    if (!form.value.doc_type) return
    fetchRoutePreview(
      Number(form.value.doc_type),
      form.value.drafter_assignment ? Number(form.value.drafter_assignment) : undefined,
      currentAmount.value,
      currentSealId.value,
    )
  }

  if (immediate) {
    execute()
  } else {
    previewTimer = setTimeout(execute, 200)
  }
}

watch(
  () => [currentAmount.value, currentSealId.value] as const,
  () => {
    if (isInitializing.value) return
    updateRoutePreview()
  },
)

watch(
  () => form.value.doc_type,
  newVal => {
    if (isInitializing.value) return
    if (newVal) {
      const dt = forDraftDocTypeList.value.find(d => d.id === Number(newVal))
      if (dt?.default_security_level && !isEdit.value) {
        form.value.security_level = dt.default_security_level
      }
      updateRoutePreview(true)
    } else {
      clearRoutePreview()
    }
  },
)

const buildFormData = () => {
  const fd = new FormData()
  fd.append('doc_type', String(form.value.doc_type))
  if (form.value.drafter_assignment) {
    fd.append('drafter_assignment', String(form.value.drafter_assignment))
  }
  fd.append('title', form.value.title)
  fd.append('security_level', form.value.security_level)
  fd.append('content', JSON.stringify(dynamicContent.value))

  // 빈 배열([]) 포함 항상 명시 전송해 수정 시 참조자 전원 해제 반영
  fd.append('observer_ids', JSON.stringify(selectedObservers.value))

  for (const file of selectedFiles.value) {
    fd.append('files', file)
  }

  if (relatedInboundLetterId.value) {
    fd.append('related_inbound_letter', String(relatedInboundLetterId.value))
  }

  return fd
}

const DATE_RANGE_RULES: ReadonlyArray<{
  startKey: string
  endKey: string
  title: string
  detail: string
}> = [
  {
    startKey: 'start_date',
    endKey: 'end_date',
    title: '기간 확인',
    detail: '종료일은 시작일과 같거나 이후여야 합니다.',
  },
  {
    startKey: 'start_date',
    endKey: 'completion_date',
    title: '사업 일정 확인',
    detail: '준공(완료)일은 착공일과 같거나 이후여야 합니다.',
  },
  {
    startKey: 'contract_start_date',
    endKey: 'contract_end_date',
    title: '계약 기간 확인',
    detail: '계약 종료일은 계약 시작일과 같거나 이후여야 합니다.',
  },
  {
    startKey: 'leave_start_date',
    endKey: 'leave_end_date',
    title: '휴직 기간 확인',
    detail: '휴직 종료일은 휴직 시작일과 같거나 이후여야 합니다.',
  },
  {
    startKey: 'payment_due_date',
    endKey: 'settlement_due_date',
    title: '정산 일정 확인',
    detail: '정산 예정일은 지급 요청일과 같거나 이후여야 합니다.',
  },
]

const validateBusinessRules = (): boolean => {
  const c = dynamicContent.value
  for (const rule of DATE_RANGE_RULES) {
    const startVal = asStr(c[rule.startKey])
    const endVal = asStr(c[rule.endKey])
    if (startVal && endVal && startVal > endVal) {
      message('warning', rule.title, rule.detail)
      return false
    }
  }
  return true
}

const onSubmit = async () => {
  saving.value = 'draft'
  try {
    const formData = buildFormData()
    if (isEdit.value) {
      const updated = await updateDocument(Number(route.params.docId), formData)
      if (updated) selectedFiles.value = []
    } else {
      const created = await createDocument(formData)
      if (created) {
        selectedFiles.value = []
        await router.push({ name: '기안 문서함 - 수정', params: { docId: created.id } })
      }
    }
  } finally {
    saving.value = ''
  }
}

const onSubmitAndSend = async () => {
  saving.value = 'submit'
  try {
    const formData = buildFormData()
    const saved = isEdit.value
      ? await updateDocument(Number(route.params.docId), formData)
      : await createDocument(formData)

    if (!saved) return
    selectedFiles.value = []

    const submitted = await submitDocument(saved.id)
    if (submitted) {
      await router.push({ name: '기안 문서함' })
    }
  } finally {
    saving.value = ''
  }
}

const getFormElement = (e?: Event): HTMLFormElement | null => {
  if (formRef.value) {
    if (formRef.value instanceof HTMLFormElement) return formRef.value
    if ('$el' in formRef.value && formRef.value.$el instanceof HTMLFormElement) {
      return formRef.value.$el
    }
  }
  if (e?.target && (e.target as HTMLElement).closest) {
    return (e.target as HTMLElement).closest('form')
  }
  return window.document.querySelector('form.needs-validation')
}

const handleSubmit = async (e: Event, type: 'draft' | 'submit') => {
  const formEl = getFormElement(e)

  if (type === 'draft') {
    if (!form.value.doc_type || !form.value.title.trim()) {
      validated.value = true
      const targetSelector = !form.value.doc_type ? 'select[required]' : 'input[required]'
      const focusTarget = formEl?.querySelector<HTMLElement>(targetSelector)
      focusTarget?.focus?.()
      focusTarget?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
      message(
        'warning',
        '필수 입력 확인',
        !form.value.doc_type ? '문서 유형을 선택해 주세요.' : '문서 제목을 입력해 주세요.',
      )
      return
    }
    if (!validateBusinessRules()) return
    await onSubmit()
    return
  }

  if (formEl && typeof formEl.checkValidity === 'function' && !formEl.checkValidity()) {
    e.preventDefault()
    e.stopPropagation()
    validated.value = true
    const firstInvalid = formEl.querySelector<HTMLElement>(':invalid')
    firstInvalid?.focus?.()
    firstInvalid?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
    message('warning', '입력 확인', '필수 항목 또는 입력 형식(기간/금액)을 확인해 주세요.')
    return
  }

  if (!form.value.title.trim()) {
    validated.value = true
    const titleInput = formEl?.querySelector<HTMLElement>('input[required]')
    titleInput?.focus?.()
    titleInput?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
    message('warning', '필수 입력 확인', '문서 제목을 입력해 주세요.')
    return
  }

  validated.value = true
  if (!validateBusinessRules()) return

  await onSubmitAndSend()
}

const onCancel = () => {
  if (isEdit.value && route.params.docId) {
    router.push({ name: '기안 문서함 - 보기', params: { docId: route.params.docId } })
  } else {
    router.push({ name: '기안 문서함' })
  }
}

onMounted(async () => {
  clearDocument()
  clearRoutePreview()

  try {
    await Promise.all([fetchDocCategoryList(), fetchMyAssignments(), fetchUsersList()])

    const primary = myAssignments.value.find(a => a.is_primary) ?? myAssignments.value[0]

    if (isEdit.value) {
      const doc = await fetchDocument(Number(route.params.docId))
      if (doc && !userInfo.value?.is_superuser) {
        const isEditableStatus = !doc.status || doc.status === 'draft' || doc.status === 'rejected'
        const isOwner =
          !doc.drafter?.id || !userInfo.value?.pk || doc.drafter.id === userInfo.value.pk
        if (!isEditableStatus || !isOwner) {
          message(
            'warning',
            '수정 불가',
            !isEditableStatus
              ? '임시저장 또는 반려 상태의 문서만 수정할 수 있습니다.'
              : '기안자 본인만 문서를 수정할 수 있습니다.',
          )
          await router.replace({ name: '기안 문서함 - 보기', params: { docId: doc.id } })
          return
        }
      }
      const assignmentId = doc?.drafter_assignment ?? primary?.pk ?? null
      form.value.drafter_assignment = assignmentId ? String(assignmentId) : ''
      await fetchForDraftDocTypeList(assignmentId ? Number(assignmentId) : undefined)

      if (doc) {
        form.value.doc_type = doc.doc_type ? String(doc.doc_type) : ''
        form.value.title = doc.title
        form.value.security_level = (doc.security_level as SecurityLevel) || '2'
        dynamicContent.value = { ...(doc.content as ApprovalContent) }
        selectedObservers.value = (doc.observers || []).map(o => o.id)
        if (doc.related_inbound_letter) {
          relatedInboundLetterId.value = doc.related_inbound_letter
        }
      }
      isInitializing.value = false
      updateRoutePreview(true)
      return
    }

    if (primary) {
      form.value.drafter_assignment = String(primary.pk)
    }
    await fetchForDraftDocTypeList(
      form.value.drafter_assignment ? Number(form.value.drafter_assignment) : undefined,
    )

    if (route.query) {
      if (route.query.title) {
        form.value.title = String(route.query.title)
      }
      if (route.query.inbound_letter) {
        const inboundId = Number(route.query.inbound_letter)
        relatedInboundLetterId.value = inboundId

        // 수신 공문 정보 선조회 후 doc_type 설정 (자식 폼 마운트 시 덮어쓰기 방지)
        try {
          const { data: letter } = await api.get(`/inbound-letter/${inboundId}/`)
          if (letter) {
            dynamicContent.value = {
              inbound_letter_id: letter.pk,
              sender_name: letter.sender_name || '',
              document_number: letter.document_number || '',
              receipt_number: letter.receipt_number || '',
              received_date: letter.received_date || '',
              reply_due_date: letter.reply_due_date || '',
              action_type: 'REPLY_LETTER',
              urgency: 'NORMAL',
              letter_subject: letter.title || '',
              letter_summary: letter.content || '',
              review_opinion: '',
            }
          }
        } catch (err) {
          console.error('Failed to prefetch inbound letter:', err)
        }

        const inboundDocType = forDraftDocTypeList.value.find(d => {
          const templateKey = (d.form_template_key || '').trim().toUpperCase()
          const codeKey = (d.code || '').trim().toUpperCase()
          return (
            templateKey === 'INBOUND_REPORT' ||
            codeKey === 'INBOUND_REPORT' ||
            codeKey === 'IR'
          )
        })
        if (inboundDocType) {
          form.value.doc_type = String(inboundDocType.id)
          if (inboundDocType.default_security_level) {
            form.value.security_level = inboundDocType.default_security_level
          }
        }
      }
    }
  } finally {
    isInitializing.value = false
  }

  if (form.value.doc_type) {
    updateRoutePreview(true)
  }
})

onBeforeUnmount(() => {
  if (previewTimer) clearTimeout(previewTimer)
  clearRoutePreview()
  clearDocument()
})

const applyExampleTitle = (title: string) => {
  if (!form.value.title) {
    form.value.title = title
    return
  }
  pendingConfirmType.value = 'apply-example'
  pendingExampleTitle.value = title
  refConfirmModal.value?.callModal(
    '예시 제목 적용',
    '입력된 제목을 추천 예시 제목으로 변경하시겠습니까?',
    'mdi-lightbulb-on-outline',
    'primary',
    '적용',
    'primary',
  )
}

const handleModalConfirm = async () => {
  const confirmType = pendingConfirmType.value
  refConfirmModal.value?.close()
  pendingConfirmType.value = null

  if (confirmType === 'delete-attachment' && pendingAttachmentId.value) {
    const attId = pendingAttachmentId.value
    pendingAttachmentId.value = null
    await deleteAttachment(attId, Number(route.params.docId))
  } else if (confirmType === 'apply-example' && pendingExampleTitle.value) {
    form.value.title = pendingExampleTitle.value
    pendingExampleTitle.value = ''
  }
}
</script>

<template>
  <CRow>
    <CCol lg="8" xl="7">
      <CCardHeader class="d-flex align-items-center justify-content-between border-top">
        <span class="fw-semibold">
          <CIcon name="cilPencil" class="me-2" />
          {{ isEdit ? '결재문서 수정' : '새 기안 작성' }}
        </span>
        <CButton color="secondary" variant="ghost" size="sm" @click="onCancel"> 취소 </CButton>
      </CCardHeader>

      <CCardBody>
        <CForm
          ref="formRef"
          class="needs-validation"
          novalidate
          :validated="validated"
          @submit.prevent
        >
          <!-- 수신 공문 연동 안내 배너 -->
          <CAlert
            v-if="relatedInboundLetterId"
            color="info"
            class="d-flex align-items-center mb-4 shadow-sm"
          >
            <v-icon icon="mdi-inbox-arrow-down" size="large" class="me-3 text-primary" />
            <div>
              <strong>수신 공문 연동 기안:</strong>
              접수된 수신 공문(ID: {{ relatedInboundLetterId }})의 처리 보고 및 대응 품의
              문서입니다.
            </div>
          </CAlert>

          <!-- 기안 부서 / 보직 선택 (보직이 있거나 수정 모드 기존 보직이 있는 경우) -->
          <CRow v-if="myAssignments.length > 0 || hasFallbackAssignment" class="mb-3">
            <CFormLabel class="col-sm-3 col-form-label"> 기안 부서/직책 </CFormLabel>
            <CCol sm="9">
              <CFormSelect
                v-model="form.drafter_assignment"
                :disabled="isEdit"
                @change="onAssignmentChange"
              >
                <option v-if="hasFallbackAssignment" :value="form.drafter_assignment">
                  {{
                    document?.drafter_assignment_desc ||
                    document?.department_name ||
                    '기존 기안 보직'
                  }}
                </option>
                <option v-for="asgn in myAssignments" :key="asgn.pk" :value="String(asgn.pk)">
                  [{{ asgn.is_primary ? '주보직' : '겸직' }}] {{ asgn.department_name }}
                  <template v-if="asgn.duty_name">({{ asgn.duty_name }})</template>
                  <template v-else-if="asgn.position_name">({{ asgn.position_name }})</template>
                  <template v-if="asgn.assigned_tasks"> - {{ asgn.assigned_tasks }}</template>
                </option>
              </CFormSelect>
              <div class="form-text text-muted">
                선택한 부서 및 직책의 상급 결재선으로 자동 결재선이 구성됩니다.
              </div>
            </CCol>
          </CRow>

          <!-- 문서 유형 선택 (카테고리별 optgroup) -->
          <CRow class="mb-3">
            <CFormLabel class="col-sm-3 col-form-label">
              문서 유형 <span class="text-danger">*</span>
            </CFormLabel>
            <CCol sm="9">
              <!-- 자주 쓰는 4대 양식 빠른 선택 칩 -->
              <div
                v-if="quickDocTypes.length && !isEdit"
                class="d-flex flex-wrap align-items-center gap-1 mb-2"
              >
                <span class="small text-muted me-1">자주 쓰는 양식:</span>
                <CButton
                  v-for="q in quickDocTypes"
                  :key="q.docType.id"
                  size="sm"
                  :color="Number(form.doc_type) === q.docType.id ? 'primary' : 'secondary'"
                  :variant="Number(form.doc_type) === q.docType.id ? undefined : 'ghost'"
                  :class="[
                    'border py-0 px-2 rounded-pill small',
                    Number(form.doc_type) === q.docType.id
                      ? 'text-white'
                      : 'text-body bg-more-light',
                  ]"
                  style="font-size: 0.78rem"
                  @click="selectQuickDocType(q.docType)"
                >
                  {{ q.label }}
                </CButton>
              </div>

              <CFormSelect
                v-model="form.doc_type"
                :disabled="isEdit"
                required
                @change="onDocTypeChange"
              >
                <option value="">-- 유형을 선택하세요 --</option>
                <optgroup
                  v-for="(types, catName) in groupedDocTypes"
                  :key="catName"
                  :label="catName"
                >
                  <option v-for="dt in types" :key="dt.id" :value="String(dt.id)">
                    {{ dt.name }}
                    <template v-if="dt.policy_rules?.length"> [금액별 전결]</template>
                    <template v-else-if="dt.final_approval_duty_name">
                      [{{ dt.final_approval_duty_name }} 전결]</template
                    >
                  </option>
                </optgroup>
              </CFormSelect>
              <div v-if="selectedDocType?.description" class="form-text text-muted">
                {{ selectedDocType.description }}
              </div>

              <!-- 모바일/태블릿 전용 접이식 작성 가이드 (d-lg-none) -->
              <div v-if="selectedDocType" class="d-lg-none mt-2 p-2 border rounded bg-more-light">
                <div class="d-flex align-items-center justify-content-between mb-1">
                  <span class="fw-semibold text-primary small d-flex align-items-center">
                    <v-icon
                      icon="mdi-lightbulb-on-outline"
                      size="small"
                      class="me-1 text-warning"
                    />
                    {{ currentGuide.title }} 작성 가이드
                  </span>
                  <v-chip color="info" size="x-small" variant="elevated">
                    {{ currentGuide.category }}
                  </v-chip>
                </div>
                <div class="small text-muted mb-2">{{ currentGuide.summary }}</div>
                <div class="small mb-1">
                  <span class="fw-bold text-body">• 필수 첨부:</span>
                  <span class="text-secondary ms-1">{{
                    currentGuide.requiredAttachments.join(', ')
                  }}</span>
                </div>
                <div
                  v-if="currentGuide.example"
                  class="d-flex justify-content-between align-items-center pt-1 border-top mt-1"
                >
                  <span class="text-muted text-truncate me-2 small" style="font-size: 0.75rem">
                    예: {{ currentGuide.example.title }}
                  </span>
                  <CButton
                    size="sm"
                    color="primary"
                    variant="ghost"
                    class="py-0 px-2 small flex-shrink-0"
                    style="font-size: 0.75rem"
                    @click="applyExampleTitle(currentGuide.example.title)"
                  >
                    [제목 적용]
                  </CButton>
                </div>
              </div>
            </CCol>
          </CRow>

          <!-- 제목 -->
          <CRow class="mb-3">
            <CFormLabel class="col-sm-3 col-form-label">
              제목 <span class="text-danger">*</span>
            </CFormLabel>
            <CCol sm="9">
              <CFormInput
                v-model="form.title"
                placeholder="결재 문서 제목을 입력하세요."
                required
              />
            </CCol>
          </CRow>

          <!-- 공개 등급 (보안 레벨) -->
          <CRow class="mb-3">
            <CFormLabel class="col-sm-3 col-form-label">
              공개 등급 <span class="text-danger">*</span>
            </CFormLabel>
            <CCol sm="9">
              <v-radio-group
                v-model="form.security_level"
                inline
                hide-details
                density="compact"
                class="pt-0"
              >
                <v-radio
                  value="1"
                  color="error"
                  label="🔒 1등급 (비공개: 기안자/결재선/참조자)"
                  class="me-3"
                />
                <v-radio
                  value="2"
                  color="primary"
                  label="👥 2등급 (부서공개: 소속 부서 공유)"
                  class="me-3"
                />
                <v-radio value="3" color="success" label="🌐 3등급 (전사공개: 회사 전체 공유)" />
              </v-radio-group>
              <div class="form-text text-muted mt-1">
                문서 유형별 기본 등급이 자동 지정되며, 필요 시 기안자가 등급을 변경할 수 있습니다.
              </div>
            </CCol>
          </CRow>

          <!-- 참조자 (공람) -->
          <CRow class="mb-3">
            <CFormLabel class="col-sm-3 col-form-label">
              참조자 <span class="text-muted small">(공람)</span>
            </CFormLabel>
            <CCol sm="9">
              <v-autocomplete
                v-model="selectedObservers"
                :items="availableUsers"
                item-value="value"
                item-title="title"
                multiple
                chips
                closable-chips
                clearable
                density="compact"
                variant="outlined"
                placeholder="결재 완료 시 공람할 참조자를 검색/선택하세요."
                hide-details
              />
              <div class="form-text text-muted">
                지정된 참조자는 결재가 최종 승인되었을 때 공람 알림을 받고 문서를 열람할 수
                있습니다.
              </div>
            </CCol>
          </CRow>

          <hr class="my-3" />

          <!-- 양식 필드 (전용 폼 컴포넌트) -->
          <template v-if="selectedDocType">
            <component
              :is="activeFormComponent"
              v-if="activeFormComponent"
              :key="selectedDocType.id"
              v-model="dynamicContent"
            />

            <DynamicSchemaForm
              v-else-if="selectedDocType.form_schema?.length"
              :key="selectedDocType.id"
              v-model="dynamicContent"
              :schema="selectedDocType.form_schema"
            />

            <div v-else class="text-center text-muted py-3 border rounded bg-more-light mb-3">
              별도의 추가 양식 필드가 없는 일반 기안 문서입니다.
            </div>
          </template>

          <div
            v-else-if="!form.doc_type"
            class="text-center text-muted py-4 border rounded bg-more-light mb-3"
          >
            문서 유형을 선택하면 작성 양식이 표시됩니다.
          </div>

          <!-- 첨부파일 섹션 -->
          <hr class="my-3" />
          <div class="mb-3">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <CFormLabel class="fw-semibold mb-0">
                <CIcon name="cilPaperclip" class="me-1" />
                첨부파일
              </CFormLabel>
              <v-btn
                color="secondary"
                variant="outlined"
                size="small"
                @click="fileInputRef?.click()"
              >
                <CIcon name="cilPlus" class="me-1" />파일 추가
              </v-btn>
              <input
                ref="fileInputRef"
                type="file"
                multiple
                class="d-none"
                @change="onFileSelected"
              />
            </div>

            <!-- 1. 기존 업로드된 첨부파일 목록 (수정 모드) -->
            <div v-if="existingAttachments.length" class="mb-2">
              <div class="small text-muted mb-1">등록된 첨부파일</div>
              <ul class="list-group list-group-flush border rounded">
                <li
                  v-for="att in existingAttachments"
                  :key="att.id"
                  class="list-group-item d-flex justify-content-between align-items-center py-2 px-3"
                >
                  <div class="d-flex align-items-center">
                    <CIcon name="cilFile" class="me-2 text-primary" />
                    <a
                      v-if="getSafeExternalUrl(att.file_url)"
                      :href="getSafeExternalUrl(att.file_url)"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="text-decoration-none text-body fw-medium me-2"
                    >
                      {{ att.file_name }}
                    </a>
                    <span v-else class="text-body fw-medium me-2">{{ att.file_name }}</span>
                    <span class="badge bg-more-light text-muted border">
                      {{ formatFileSize(att.file_size) }}
                    </span>
                  </div>
                  <CButton
                    color="danger"
                    variant="ghost"
                    size="sm"
                    @click="removeExistingAttachment(att.id)"
                  >
                    <CIcon name="cilTrash" size="sm" />
                  </CButton>
                </li>
              </ul>
            </div>

            <!-- 2. 신규 추가할 파일 목록 -->
            <div v-if="selectedFiles.length" class="mb-2">
              <div class="small text-muted mb-1">신규 업로드 예정 파일</div>
              <ul class="list-group list-group-flush border rounded">
                <li
                  v-for="(file, idx) in selectedFiles"
                  :key="idx"
                  class="list-group-item d-flex justify-content-between align-items-center py-2 px-3 bg-more-light"
                >
                  <div class="d-flex align-items-center">
                    <CIcon name="cilCloudUpload" class="me-2 text-success" />
                    <span class="fw-medium me-2">{{ file.name }}</span>
                    <span class="badge bg-more-white text-muted border">
                      {{ formatFileSize(file.size) }}
                    </span>
                  </div>
                  <CButton
                    color="danger"
                    variant="ghost"
                    size="sm"
                    @click="removeSelectedFile(idx)"
                  >
                    <CIcon name="cilX" size="sm" />
                  </CButton>
                </li>
              </ul>
            </div>

            <!-- 빈 상태 안내 -->
            <div
              v-if="!existingAttachments.length && !selectedFiles.length"
              class="text-center text-muted py-3 border border-dashed rounded bg-more-light"
              style="cursor: pointer"
              @click="fileInputRef?.click()"
            >
              <CIcon name="cilCloudUpload" size="lg" class="mb-1 text-muted" />
              <div class="small">
                클릭하여 관련 증빙 서류나 첨부파일을 추가하세요. (여러 개 선택 가능)
              </div>
            </div>
          </div>

          <!-- 동적 결재선 미리보기 (routePreview) -->
          <template v-if="routePreview.length">
            <hr class="my-3" />
            <div class="d-flex align-items-center justify-content-between mb-2">
              <p class="text-medium-emphasis small fw-semibold mb-0">
                <CIcon name="cilPeople" class="me-1" />
                결재선 미리보기
              </p>
              <div class="d-flex gap-1">
                <v-chip
                  v-if="selectedDocType?.policy_rules?.length && currentAmount !== null"
                  color="warning"
                  size="x-small"
                  variant="elevated"
                >
                  금액 조건 반영 ({{ currentAmount.toLocaleString() }}원)
                </v-chip>
                <v-chip
                  v-if="selectedDocType?.route_type === 'organization'"
                  color="info"
                  size="x-small"
                  variant="elevated"
                >
                  조직도 기반 자동 생성
                </v-chip>
              </div>
            </div>
            <div class="d-flex align-items-start flex-wrap gap-0">
              <template v-for="(step, idx) in routePreview" :key="step.step_order">
                <div class="route-step-card text-center">
                  <div class="text-muted mb-1" style="font-size: 0.72rem">
                    {{ step.step_order }}단계
                  </div>
                  <div class="fw-semibold small mb-1">{{ step.role_label }}</div>
                  <div class="text-muted mb-1" style="font-size: 0.72rem">
                    {{ step.approvers.map(a => getUserDisplayName(a)).join(', ') }}
                  </div>
                  <v-chip
                    :color="step.condition === 'AND' ? 'primary' : 'info'"
                    size="x-small"
                    variant="elevated"
                  >
                    {{ step.condition === 'AND' ? '전원승인' : '1인승인' }}
                  </v-chip>
                </div>
                <!-- 화살표 연결 (마지막 제외) -->
                <div v-if="idx < routePreview.length - 1" class="route-arrow">→</div>
              </template>
            </div>
          </template>

          <!-- 하단 버튼 -->
          <div class="d-flex justify-content-end gap-2 mt-4 pt-3 border-top">
            <v-btn
              type="button"
              color="blue-grey-lighten-2"
              :disabled="!!saving"
              flat
              @click="handleSubmit($event, 'draft')"
            >
              <CSpinner v-if="saving === 'draft'" size="sm" class="me-1" />
              임시저장
            </v-btn>
            <v-btn
              type="button"
              color="primary"
              :disabled="!!saving"
              @click="handleSubmit($event, 'submit')"
            >
              <CSpinner v-if="saving === 'submit'" size="sm" class="me-1" />
              저장 후 상신
            </v-btn>
            <v-btn color="light" flat @click="router.push({ name: '기안 문서함' })">
              목록으로
            </v-btn>
          </div>
        </CForm>
      </CCardBody>
    </CCol>

    <!-- 우측: PC 전용 작성 가이드 & 팁 (lg 이상에서만 표시) -->
    <CCol lg="4" xl="5" class="d-none d-lg-block">
      <div class="sticky-top" style="top: 80px; z-index: 10">
        <CCard class="shadow-sm border-light">
          <CCardHeader class="bg-more-light d-flex align-items-center justify-content-between py-2">
            <div class="fw-semibold text-primary d-flex align-items-center">
              <v-icon icon="mdi-lightbulb-on-outline" size="small" class="me-1 text-warning" />
              {{ currentGuide.title }} 작성 가이드
            </div>
            <v-chip color="info" size="x-small" variant="elevated">
              {{ currentGuide.category }}
            </v-chip>
          </CCardHeader>
          <CCardBody class="p-3">
            <!-- 1. 양식 요약 -->
            <p class="small text-muted mb-3 border-bottom pb-2">
              {{ currentGuide.summary }}
            </p>

            <!-- 2. 핵심 요령 (Tips) -->
            <div class="mb-3">
              <div class="small fw-bold text-body mb-2 d-flex align-items-center">
                <v-icon icon="mdi-check-circle-outline" size="x-small" class="me-1 text-success" />
                핵심 작성 요령 (Tips)
              </div>
              <ul class="list-unstyled mb-0 small text-secondary ps-1">
                <li v-for="(tip, idx) in currentGuide.tips" :key="idx" class="mb-1 d-flex">
                  <span class="text-primary me-2">•</span>
                  <span>{{ tip }}</span>
                </li>
              </ul>
            </div>

            <!-- 3. 필수 첨부 체크리스트 -->
            <div class="mb-3">
              <div class="small fw-bold text-body mb-2 d-flex align-items-center">
                <v-icon icon="mdi-paperclip" size="x-small" class="me-1 text-info" />
                필수 첨부 서류 (Checklist)
              </div>
              <div class="bg-more-light p-2 rounded small border">
                <div
                  v-for="(att, idx) in currentGuide.requiredAttachments"
                  :key="idx"
                  class="mb-1 d-flex align-items-start"
                >
                  <v-icon
                    icon="mdi-checkbox-marked-outline"
                    size="x-small"
                    class="me-1 text-primary mt-1 flex-shrink-0"
                  />
                  <span>{{ att }}</span>
                </div>
              </div>
            </div>

            <!-- 4. 모범 작성 예시 -->
            <div v-if="currentGuide.example" class="mt-3 pt-2 border-top">
              <div
                class="small fw-bold text-body mb-2 d-flex align-items-center justify-content-between"
              >
                <div class="d-flex align-items-center">
                  <v-icon
                    icon="mdi-text-box-search-outline"
                    size="x-small"
                    class="me-1 text-secondary"
                  />
                  모범 작성 예시
                </div>
                <CButton
                  size="sm"
                  color="primary"
                  variant="ghost"
                  class="p-0 text-decoration-none small"
                  style="font-size: 0.75rem"
                  @click="applyExampleTitle(currentGuide.example.title)"
                >
                  [제목 예시 적용]
                </CButton>
              </div>
              <div class="bg-more-light p-2 rounded small border">
                <div class="fw-semibold text-primary mb-1" style="font-size: 0.82rem">
                  [제목] {{ currentGuide.example.title }}
                </div>
                <div
                  class="text-muted"
                  style="white-space: pre-wrap; font-size: 0.78rem; line-height: 1.5"
                >
                  {{ currentGuide.example.content }}
                </div>
              </div>
            </div>
          </CCardBody>
        </CCard>
      </div>
    </CCol>
  </CRow>

  <ConfirmModal ref="refConfirmModal" @confirm-func="handleModalConfirm" />
</template>

<style scoped>
.route-step-card {
  border: 1px solid var(--cui-border-color);
  border-radius: 0.4rem;
  padding: 0.5rem 0.75rem;
  min-width: 110px;
  max-width: 140px;
  background: var(--cui-body-bg);
}

.route-arrow {
  display: flex;
  align-items: center;
  padding: 0 0.25rem;
  color: var(--cui-secondary);
  font-size: 1.25rem;
  line-height: 1;
  margin-top: 0.5rem;
}
</style>
