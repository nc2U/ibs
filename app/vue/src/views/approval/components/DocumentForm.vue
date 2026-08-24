<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval'
import { useAccount } from '@/store/pinia/account'
import type { DocumentType } from '@/store/types/approval'
import { STATIC_FORM_REGISTRY } from '@/views/approval/forms'

const route = useRoute()
const router = useRouter()
const store = useApproval()
const accStore = useAccount()
const { forDraftDocTypeList, document, myAssignments, routePreview } = storeToRefs(store)
const { usersList } = storeToRefs(accStore)
const {
  fetchDocCategoryList,
  fetchForDraftDocTypeList,
  fetchDocument,
  fetchMyAssignments,
  fetchRoutePreview,
  createDocument,
  updateDocument,
  deleteAttachment,
  submitDocument,
} = store
const { fetchUsersList } = accStore

const isEdit = computed(() => !!route.params.docId)
const saving = ref<'draft' | 'submit' | ''>('')
const validated = ref(false)
const formRef = ref<HTMLFormElement | null>(null)

const form = ref({
  doc_type: '' as number | '',
  drafter_assignment: '' as number | '',
  title: '',
  security_level: '2' as '1' | '2' | '3',
})
const dynamicContent = ref<Record<string, string>>({})
const selectedObservers = ref<number[]>([])
const selectedFiles = ref<File[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)

const availableUsers = computed(() =>
  usersList.value.map(u => ({
    value: u.pk,
    title: u.profile?.name ? `${u.profile.name} (${u.username})` : u.username,
  })),
)

const existingAttachments = computed(() => document.value?.attachments || [])

const formatFileSize = (bytes: number | null | undefined) => {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const onFileSelected = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    for (let i = 0; i < target.files.length; i++) {
      const file = target.files[i]
      // 중복 체크
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

const removeExistingAttachment = async (attachmentId: number) => {
  if (confirm('첨부파일을 삭제하시겠습니까?')) {
    await deleteAttachment(attachmentId, Number(route.params.docId))
  }
}

const selectedDocType = computed<DocumentType | null>(
  () => forDraftDocTypeList.value.find(d => d.id === Number(form.value.doc_type)) ?? null,
)

// 카테고리별로 그룹화된 문서 유형 목록
const groupedDocTypes = computed(() => {
  const groups: Record<string, DocumentType[]> = {}
  forDraftDocTypeList.value.forEach(dt => {
    const catName = dt.category_name || '기타/일반'
    if (!groups[catName]) groups[catName] = []
    groups[catName].push(dt)
  })
  return groups
})

const onDocTypeChange = () => {
  dynamicContent.value = {}
  if (selectedDocType.value && selectedDocType.value.default_security_level) {
    form.value.security_level = selectedDocType.value.default_security_level
  }
  updateRoutePreview()
}

const onAssignmentChange = async () => {
  await fetchForDraftDocTypeList(
    form.value.drafter_assignment ? Number(form.value.drafter_assignment) : undefined,
  )
  if (!forDraftDocTypeList.value.some(d => d.id === Number(form.value.doc_type))) {
    form.value.doc_type = ''
    dynamicContent.value = {}
  }
  updateRoutePreview()
}

// dynamicContent에서 금액 값 추출
const currentAmount = computed<number | null>(() => {
  const c = dynamicContent.value
  if (!c) return null
  if (c.amount !== undefined && c.amount !== null && c.amount !== '') return Number(c.amount)
  if (c.contract_amount !== undefined && c.contract_amount !== '') return Number(c.contract_amount)
  if (c.advance_amount !== undefined && c.advance_amount !== '') return Number(c.advance_amount)
  if (c.total_cost !== undefined && c.total_cost !== '') return Number(c.total_cost)
  if (c.total_budget !== undefined && c.total_budget !== '') return Number(c.total_budget)
  if (c.settlement_amount !== undefined && c.settlement_amount !== '')
    return Number(c.settlement_amount)
  return null
})

// 금액 또는 양식 데이터 변경 시 실시간 결재선 미리보기 갱신 (디바운스)
watch(
  () => currentAmount.value,
  () => {
    updateRoutePreview()
  },
)

watch(
  () => form.value.doc_type,
  newVal => {
    if (newVal) {
      const dt = forDraftDocTypeList.value.find(d => d.id === Number(newVal))
      if (dt?.default_security_level && !isEdit.value) {
        form.value.security_level = dt.default_security_level
      }
      updateRoutePreview(true)
    }
  },
)

let previewTimer: ReturnType<typeof setTimeout> | null = null
const updateRoutePreview = (immediate = false) => {
  if (!form.value.doc_type) return
  if (previewTimer) clearTimeout(previewTimer)

  const execute = () => {
    fetchRoutePreview(
      Number(form.value.doc_type),
      form.value.drafter_assignment ? Number(form.value.drafter_assignment) : undefined,
      currentAmount.value,
    )
  }

  if (immediate) {
    execute()
  } else {
    previewTimer = setTimeout(execute, 200)
  }
}

const buildFormData = () => {
  const fd = new FormData()
  fd.append('doc_type', String(form.value.doc_type))
  if (form.value.drafter_assignment) {
    fd.append('drafter_assignment', String(form.value.drafter_assignment))
  }
  fd.append('title', form.value.title)
  fd.append('security_level', form.value.security_level)
  fd.append('content', JSON.stringify(dynamicContent.value))

  // 참조자 추가
  for (const obsId of selectedObservers.value) {
    fd.append('observer_ids', String(obsId))
  }

  // 첨부파일 추가
  for (const file of selectedFiles.value) {
    fd.append('files', file)
  }
  return fd
}

const onSubmit = async () => {
  saving.value = 'draft'
  const formData = buildFormData()
  if (isEdit.value) {
    await updateDocument(Number(route.params.docId), formData)
    selectedFiles.value = []
  } else {
    const created = await createDocument(formData)
    if (created) await router.push({ name: '기안 문서함 - 수정', params: { docId: created.id } })
  }
  saving.value = ''
}

const onSubmitAndSend = async () => {
  saving.value = 'submit'
  const formData = buildFormData()
  let docId: number | undefined
  if (isEdit.value) {
    await updateDocument(Number(route.params.docId), formData)
    docId = Number(route.params.docId)
  } else {
    const created = await createDocument(formData)
    docId = created?.id
  }
  if (docId) {
    await submitDocument(docId)
    await router.push({ name: '기안 문서함' })
  }
  saving.value = ''
}

const getFormElement = (e?: Event): HTMLFormElement | null => {
  if (formRef.value) {
    if (formRef.value instanceof HTMLFormElement) return formRef.value
    if ((formRef.value as any).$el instanceof HTMLFormElement) return (formRef.value as any).$el
  }
  if (e?.target && (e.target as HTMLElement).closest) {
    return (e.target as HTMLElement).closest('form')
  }
  return window.document.querySelector('form.needs-validation')
}

const handleSubmit = async (e: Event, type: 'draft' | 'submit') => {
  const formEl = getFormElement(e)
  if (formEl && typeof formEl.checkValidity === 'function' && !formEl.checkValidity()) {
    e.preventDefault()
    e.stopPropagation()
    validated.value = true
    return
  }

  validated.value = true

  if (type === 'draft') {
    await onSubmit()
  } else if (type === 'submit') {
    await onSubmitAndSend()
  }
}

onMounted(async () => {
  await Promise.all([fetchDocCategoryList(), fetchMyAssignments(), fetchUsersList()])

  // 기본 주보직 선택
  const primary = myAssignments.value.find(a => a.is_primary) ?? myAssignments.value[0]
  if (primary) {
    form.value.drafter_assignment = primary.pk
  }

  // 보직에 따른 기안 가능 문서 유형 조회
  await fetchForDraftDocTypeList(
    form.value.drafter_assignment ? Number(form.value.drafter_assignment) : undefined,
  )

  if (isEdit.value) {
    await fetchDocument(Number(route.params.docId))
    if (document.value) {
      form.value.doc_type = document.value.doc_type
      form.value.drafter_assignment = document.value.drafter_assignment ?? ''
      form.value.title = document.value.title
      form.value.security_level = (document.value.security_level as '1' | '2' | '3') || '2'
      dynamicContent.value = { ...(document.value.content as Record<string, string>) }
      selectedObservers.value = (document.value.observers || []).map(o => o.id)
      await updateRoutePreview()
    }
  }
})
</script>

<template>
  <CRow class="">
    <CCol lg="8" xl="7">
      <CCardHeader class="d-flex align-items-center justify-content-between">
        <span class="fw-semibold">
          <CIcon name="cilPencil" class="me-2" />
          {{ isEdit ? '결재문서 수정' : '새 기안 작성' }}
        </span>
        <CButton color="secondary" variant="ghost" size="sm" @click="router.back()"> 취소 </CButton>
      </CCardHeader>

      <CCardBody>
        <CForm
          ref="formRef"
          class="needs-validation"
          novalidate
          :validated="validated"
          @submit.prevent="handleSubmit($event, 'draft')"
        >
          <!-- 기안 부서 / 보직 선택 (보직이 있는 경우) -->
          <CRow v-if="myAssignments.length > 0" class="mb-3">
            <CFormLabel class="col-sm-3 col-form-label"> 기안 부서/직책 </CFormLabel>
            <CCol sm="9">
              <CFormSelect
                v-model="form.drafter_assignment"
                :disabled="isEdit"
                @change="onAssignmentChange"
              >
                <option v-for="asgn in myAssignments" :key="asgn.pk" :value="asgn.pk">
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
                  <option v-for="dt in types" :key="dt.id" :value="dt.id">
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
              :is="
                STATIC_FORM_REGISTRY[
                  selectedDocType.form_template_key || selectedDocType.code || ''
                ]
              "
              v-if="
                (selectedDocType.form_template_key || selectedDocType.code) &&
                STATIC_FORM_REGISTRY[selectedDocType.form_template_key || selectedDocType.code]
              "
              v-model="dynamicContent"
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
                      :href="att.file_url"
                      target="_blank"
                      class="text-decoration-none text-body fw-medium me-2"
                    >
                      {{ att.file_name }}
                    </a>
                    <span class="badge bg-light text-muted border">
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
                  class="list-group-item d-flex justify-content-between align-items-center py-2 px-3 bg-light"
                >
                  <div class="d-flex align-items-center">
                    <CIcon name="cilCloudUpload" class="me-2 text-success" />
                    <span class="fw-medium me-2">{{ file.name }}</span>
                    <span class="badge bg-white text-muted border">
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
                <CBadge
                  v-if="selectedDocType?.policy_rules?.length && currentAmount !== null"
                  color="warning"
                  size="sm"
                >
                  금액 조건 반영 ({{ currentAmount.toLocaleString() }}원)
                </CBadge>
                <CBadge
                  v-if="selectedDocType?.route_type === 'organization'"
                  color="info"
                  size="sm"
                >
                  조직도 기반 자동 생성
                </CBadge>
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
                    {{ step.approvers.map(a => a.full_name).join(', ') }}
                  </div>
                  <CBadge
                    :color="step.condition === 'AND' ? 'primary' : 'info'"
                    style="font-size: 0.65rem"
                  >
                    {{ step.condition === 'AND' ? '전원승인' : '1인승인' }}
                  </CBadge>
                </div>
                <!-- 화살표 연결 (마지막 제외) -->
                <div v-if="idx < routePreview.length - 1" class="route-arrow">→</div>
              </template>
            </div>
          </template>

          <!-- 하단 버튼 -->
          <div class="d-flex justify-content-end gap-2 mt-4 pt-3 border-top">
            <v-btn type="submit" color="blue-grey-lighten-2" :disabled="!!saving" flat>
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
            <v-btn color="light" @click="router.push({ name: '기안 문서함' })" flat>
              목록으로
            </v-btn>
          </div>
        </CForm>
      </CCardBody>
    </CCol>
  </CRow>
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
