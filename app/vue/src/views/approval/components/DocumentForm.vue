<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useApproval } from '@/store/pinia/approval.ts'
import type { DocumentType } from '@/store/types/approval.ts'

const route = useRoute()
const router = useRouter()
const store = useApproval()
const { docTypeList, document, myAssignments, routePreview } = storeToRefs(store)
const {
  fetchDocTypeList,
  fetchDocument,
  fetchMyAssignments,
  fetchRoutePreview,
  createDocument,
  updateDocument,
  submitDocument,
} = store

const isEdit = computed(() => !!route.params.docId)
const saving = ref<'draft' | 'submit' | ''>('')

const form = ref({
  doc_type: '' as number | '',
  drafter_assignment: '' as number | '',
  title: '',
})
const dynamicContent = ref<Record<string, string>>({})

const selectedDocType = computed<DocumentType | null>(
  () => docTypeList.value.find(d => d.id === Number(form.value.doc_type)) ?? null,
)

const onDocTypeChange = () => {
  dynamicContent.value = {}
  updateRoutePreview()
}

const onAssignmentChange = () => {
  updateRoutePreview()
}

const updateRoutePreview = async () => {
  if (form.value.doc_type) {
    await fetchRoutePreview(
      Number(form.value.doc_type),
      form.value.drafter_assignment ? Number(form.value.drafter_assignment) : undefined,
    )
  }
}

const buildPayload = () => ({
  doc_type: Number(form.value.doc_type),
  drafter_assignment: form.value.drafter_assignment ? Number(form.value.drafter_assignment) : undefined,
  title: form.value.title,
  content: { ...dynamicContent.value },
})

const onSubmit = async () => {
  saving.value = 'draft'
  if (isEdit.value) {
    await updateDocument(Number(route.params.docId), buildPayload())
  } else {
    const created = await createDocument(buildPayload())
    if (created) await router.push({ name: '기안 문서함 - 수정', params: { docId: created.id } })
  }
  saving.value = ''
}

const onSubmitAndSend = async () => {
  saving.value = 'submit'
  let docId: number | undefined
  if (isEdit.value) {
    await updateDocument(Number(route.params.docId), buildPayload())
    docId = Number(route.params.docId)
  } else {
    const created = await createDocument(buildPayload())
    docId = created?.id
  }
  if (docId) {
    await submitDocument(docId)
    await router.push({ name: '기안 문서함' })
  }
  saving.value = ''
}

onMounted(async () => {
  await Promise.all([fetchDocTypeList(), fetchMyAssignments()])

  if (isEdit.value) {
    await fetchDocument(Number(route.params.docId))
    if (document.value) {
      form.value.doc_type = document.value.doc_type
      form.value.drafter_assignment = document.value.drafter_assignment ?? ''
      form.value.title = document.value.title
      dynamicContent.value = { ...(document.value.content as Record<string, string>) }
      updateRoutePreview()
    }
  } else {
    // 기본 주보직 선택
    const primary = myAssignments.value.find(a => a.is_primary) ?? myAssignments.value[0]
    if (primary) {
      form.value.drafter_assignment = primary.pk
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
        <CForm @submit.prevent="onSubmit">
          <!-- 기안 부서 / 보직 선택 (보직이 있는 경우) -->
          <CRow v-if="myAssignments.length > 0" class="mb-3">
            <CFormLabel class="col-sm-3 col-form-label">
              기안 부서/직책
            </CFormLabel>
            <CCol sm="9">
              <CFormSelect
                v-model="form.drafter_assignment"
                :disabled="isEdit"
                @change="onAssignmentChange"
              >
                <option
                  v-for="asgn in myAssignments"
                  :key="asgn.pk"
                  :value="asgn.pk"
                >
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

          <!-- 문서 유형 선택 -->
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
                <option v-for="dt in docTypeList" :key="dt.id" :value="dt.id">
                  {{ dt.name }}
                  <template v-if="dt.final_approval_duty_name"> [{{ dt.final_approval_duty_name }} 전결]</template>
                </option>
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

          <hr class="my-3" />

          <!-- 동적 양식 필드 (form_schema) -->
          <template v-if="selectedDocType">
            <CRow v-for="field in selectedDocType.form_schema" :key="field.key" class="mb-3">
              <CFormLabel class="col-sm-3 col-form-label">
                {{ field.label }}
                <span v-if="field.required" class="text-danger">*</span>
              </CFormLabel>
              <CCol sm="9">
                <CFormTextarea
                  v-if="field.type === 'textarea'"
                  v-model="dynamicContent[field.key]"
                  :required="field.required"
                  rows="4"
                  :placeholder="`${field.label}을(를) 입력하세요.`"
                />
                <CFormInput
                  v-else
                  v-model="dynamicContent[field.key]"
                  :type="field.type"
                  :required="field.required"
                  :placeholder="`${field.label}을(를) 입력하세요.`"
                />
              </CCol>
            </CRow>
          </template>

          <div
            v-else-if="!form.doc_type"
            class="text-center text-muted py-4 border rounded bg-light"
          >
            문서 유형을 선택하면 작성 양식이 표시됩니다.
          </div>

          <!-- 동적 결재선 미리보기 (routePreview) -->
          <template v-if="routePreview.length">
            <hr class="my-3" />
            <div class="d-flex align-items-center justify-content-between mb-2">
              <p class="text-medium-emphasis small fw-semibold mb-0">
                <CIcon name="cilPeople" class="me-1" />
                결재선 미리보기
              </p>
              <CBadge v-if="selectedDocType?.route_type === 'organization'" color="info" size="sm">
                조직도 기반 자동 생성
              </CBadge>
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
                <div v-if="idx < routePreview.length - 1" class="route-arrow">
                  →
                </div>
              </template>
            </div>
          </template>

          <!-- 하단 버튼 -->
          <div class="d-flex justify-content-end gap-2 mt-4 pt-3 border-top">
            <v-btn
              type="submit"
              color="blue-grey-lighten-2"
              :disabled="!!saving || !form.doc_type"
              flat
            >
              <CSpinner v-if="saving === 'draft'" size="sm" class="me-1" />
              임시저장
            </v-btn>
            <v-btn
              type="button"
              color="primary"
              :disabled="!!saving || !form.doc_type || !form.title"
              @click="onSubmitAndSend"
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
