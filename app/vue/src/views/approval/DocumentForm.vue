<template>
  <CRow class="justify-content-center">
    <CCol lg="8">
      <CCard>
        <CCardHeader class="d-flex align-items-center justify-content-between">
          <span>
            <CIcon icon="cil-pencil" class="me-2" />
            {{ isEdit ? '결재문서 수정' : '새 기안 작성' }}
          </span>
          <CButton color="secondary" variant="outline" size="sm" @click="router.back()">
            취소
          </CButton>
        </CCardHeader>
        <CCardBody>
          <CForm @submit.prevent="onSubmit">
            <!-- 문서 유형 선택 -->
            <CRow class="mb-3">
              <CFormLabel class="col-sm-3 col-form-label">문서 유형 <span class="text-danger">*</span></CFormLabel>
              <CCol sm="9">
                <CFormSelect
                  v-model="form.doc_type"
                  :disabled="isEdit"
                  required
                  @change="onDocTypeChange"
                >
                  <option value="">-- 선택 --</option>
                  <option v-for="dt in docTypeList" :key="dt.id" :value="dt.id">
                    {{ dt.name }}
                  </option>
                </CFormSelect>
              </CCol>
            </CRow>

            <!-- 제목 -->
            <CRow class="mb-3">
              <CFormLabel class="col-sm-3 col-form-label">제목 <span class="text-danger">*</span></CFormLabel>
              <CCol sm="9">
                <CFormInput v-model="form.title" placeholder="제목을 입력하세요." required />
              </CCol>
            </CRow>

            <!-- 동적 양식 필드 (form_schema) -->
            <template v-if="selectedDocType">
              <CRow
                v-for="field in selectedDocType.form_schema"
                :key="field.key"
                class="mb-3"
              >
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
                  />
                  <CFormInput
                    v-else
                    v-model="dynamicContent[field.key]"
                    :type="field.type"
                    :required="field.required"
                  />
                </CCol>
              </CRow>
            </template>

            <!-- 결재선 미리보기 -->
            <template v-if="selectedDocType?.route_templates?.length">
              <hr />
              <p class="text-medium-emphasis small fw-semibold mb-2">결재선</p>
              <div class="d-flex flex-wrap gap-2 mb-3">
                <div
                  v-for="step in selectedDocType.route_templates"
                  :key="step.id"
                  class="border rounded px-3 py-2 text-center"
                  style="min-width: 110px"
                >
                  <div class="small text-medium-emphasis">{{ step.step_order }}단계</div>
                  <div class="fw-semibold small">{{ step.role_label }}</div>
                  <div class="text-muted" style="font-size: 0.75rem">
                    {{ step.approvers.map(a => a.full_name).join(', ') }}
                  </div>
                  <CBadge :color="step.condition === 'AND' ? 'primary' : 'info'" size="sm" class="mt-1">
                    {{ step.condition === 'AND' ? '전원 승인' : '1인 승인' }}
                  </CBadge>
                </div>
              </div>
            </template>

            <div class="d-flex justify-content-end gap-2 mt-4">
              <CButton type="submit" color="secondary" variant="outline" :disabled="saving">
                <CSpinner v-if="saving === 'draft'" size="sm" class="me-1" />임시저장
              </CButton>
              <CButton type="button" color="primary" :disabled="saving" @click="onSubmitAndSend">
                <CSpinner v-if="saving === 'submit'" size="sm" class="me-1" />저장 후 상신
              </CButton>
            </div>
          </CForm>
        </CCardBody>
      </CCard>
    </CCol>
  </CRow>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApproval } from '@/store/pinia/approval'
import type { DocumentType } from '@/store/types/approval'

const route = useRoute()
const router = useRouter()
const store = useApproval()
const { docTypeList, document, fetchDocTypeList, fetchDocument, createDocument, updateDocument, submitDocument } = store

const isEdit = computed(() => !!route.params.docId)
const saving = ref<'draft' | 'submit' | ''>('')

const form = reactive({ doc_type: '' as number | '', title: '' })
const dynamicContent = reactive<Record<string, string>>({})

const selectedDocType = computed<DocumentType | null>(() =>
  docTypeList.find(d => d.id === Number(form.doc_type)) ?? null
)

const onDocTypeChange = () => {
  // 선택 변경 시 동적 필드 초기화
  Object.keys(dynamicContent).forEach(k => delete dynamicContent[k])
}

const buildPayload = () => ({
  doc_type: Number(form.doc_type),
  title: form.title,
  content: { ...dynamicContent },
})

const onSubmit = async () => {
  saving.value = 'draft'
  if (isEdit.value) {
    await updateDocument(Number(route.params.docId), buildPayload())
  } else {
    const created = await createDocument(buildPayload())
    if (created) router.push(`/approval/${created.id}/edit`)
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
    router.push('/approval/drafted')
  }
  saving.value = ''
}

onMounted(async () => {
  await fetchDocTypeList()
  if (isEdit.value) {
    await fetchDocument(Number(route.params.docId))
    if (document) {
      form.doc_type = document.doc_type
      form.title = document.title
      Object.assign(dynamicContent, document.content)
    }
  }
})
</script>
