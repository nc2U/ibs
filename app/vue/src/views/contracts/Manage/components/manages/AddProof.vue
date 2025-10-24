<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useContract } from '@/store/pinia/contract.ts'
import type { ContractDocument, RequiredDocs } from '@/store/types/contract'

const route = useRoute()
const contStore = useContract()

// 계약자 ID
const contractorId = computed(() =>
  route.params.contractorId ? parseInt(route.params.contractorId as string, 10) : null,
)

// Store 데이터
const requiredDocsList = computed(() => contStore.requiredDocsList)
const contractDocumentList = computed(() => contStore.contractDocumentList)
const contractor = computed(() => contStore.contractor)

// 편집 중인 문서 ID 추적
const editingDocId = ref<number | null>(null)
const editingField = ref<'quantity' | 'date' | null>(null)

// 파일 업로드 다이얼로그
const fileUploadDialog = ref(false)
const uploadingDocId = ref<number | null>(null)
const selectedFile = ref<File | null>(null)

// 로딩 상태
const isLoading = ref(false)

// 데이터 병합: 필요 서류 + 제출 서류 통합
interface MergedDocument extends RequiredDocs {
  contract_doc_pk?: number
  submitted_quantity: number
  submission_date: string | null
  is_complete: boolean
  files: any[]
}

const mergedDocuments = computed<MergedDocument[]>(() => {
  // 필요 서류 목록이 없으면 빈 배열 반환
  if (!requiredDocsList.value || !Array.isArray(requiredDocsList.value)) {
    return []
  }

  // contractDocumentList가 없거나 배열이 아니면 빈 배열로 초기화
  // (제출 서류가 없어도 필요 서류는 표시되어야 함)
  const submittedList = Array.isArray(contractDocumentList.value) ? contractDocumentList.value : []

  return requiredDocsList.value.map(required => {
    const submitted = submittedList.find(doc => doc.required_document === required.pk)

    const isComplete = submitted ? submitted.submitted_quantity >= required.quantity : false

    return {
      ...required,
      contract_doc_pk: submitted?.pk,
      submitted_quantity: submitted?.submitted_quantity || 0,
      submission_date: submitted?.submission_date || null,
      is_complete: isComplete,
      files: submitted?.files || [],
    }
  })
})

// 완료율 계산
const completionRate = computed(() => {
  if (mergedDocuments.value.length === 0) return 0
  const completed = mergedDocuments.value.filter(doc => doc.is_complete).length
  return Math.round((completed / mergedDocuments.value.length) * 100)
})

// 필수 서류 미제출 건수
const missingRequiredDocs = computed(() => {
  return mergedDocuments.value.filter(doc => doc.require_type === 'required' && !doc.is_complete)
    .length
})

// 데이터 로드
const loadData = async () => {
  if (!contractorId.value) return

  try {
    isLoading.value = true
    await contStore.fetchContractDocuments(contractorId.value)
  } catch (error) {
    console.error('데이터 로드 실패:', error)
  } finally {
    isLoading.value = false
  }
}

// 자동 저장 함수
const saveDocument = async (doc: MergedDocument) => {
  if (!contractorId.value) return

  try {
    const payload: Partial<ContractDocument> = {
      contractor: contractorId.value,
      required_document: doc.pk,
      submitted_quantity: doc.submitted_quantity,
      submission_date: doc.submission_date,
    }

    if (doc.contract_doc_pk) {
      // 업데이트
      await contStore.updateContractDocument(doc.contract_doc_pk, payload)
    } else {
      // 신규 생성
      await contStore.createContractDocument(payload as ContractDocument)
    }
  } catch (error) {
    console.error('서류 저장 실패:', error)
  }
}

// 수량 변경 핸들러 (debounce 적용)
let saveTimeout: ReturnType<typeof setTimeout> | null = null
const onQuantityChange = (doc: MergedDocument, value: number) => {
  doc.submitted_quantity = value

  if (saveTimeout) clearTimeout(saveTimeout)
  saveTimeout = setTimeout(() => {
    saveDocument(doc)
  }, 500) // 500ms debounce
}

// 날짜 변경 핸들러 (즉시 저장)
const onDateChange = (doc: MergedDocument) => {
  saveDocument(doc)
}

// 편집 모드 토글
const startEdit = (docId: number, field: 'quantity' | 'date') => {
  editingDocId.value = docId
  editingField.value = field
}

const endEdit = () => {
  editingDocId.value = null
  editingField.value = null
}

// 파일 업로드 다이얼로그
const openFileUpload = (doc: MergedDocument) => {
  if (!doc.contract_doc_pk) {
    // 서류 기록이 없으면 먼저 생성
    saveDocument(doc).then(() => {
      uploadingDocId.value = doc.contract_doc_pk!
      fileUploadDialog.value = true
    })
  } else {
    uploadingDocId.value = doc.contract_doc_pk
    fileUploadDialog.value = true
  }
}

const onFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  }
}

const uploadFile = async () => {
  if (!selectedFile.value || !uploadingDocId.value || !contractorId.value) return

  try {
    await contStore.uploadDocumentFile(uploadingDocId.value, selectedFile.value, contractorId.value)
    closeFileUpload()
  } catch (error) {
    console.error('파일 업로드 실패:', error)
  }
}

const closeFileUpload = () => {
  fileUploadDialog.value = false
  uploadingDocId.value = null
  selectedFile.value = null
}

// 파일 삭제
const deleteFile = async (fileId: number, contractDocId: number) => {
  if (!contractorId.value) return

  if (confirm('파일을 삭제하시겠습니까?')) {
    try {
      await contStore.deleteDocumentFile(fileId, contractDocId, contractorId.value)
    } catch (error) {
      console.error('파일 삭제 실패:', error)
    }
  }
}

// 파일 다운로드
const downloadFile = (fileUrl: string, fileName: string) => {
  contStore.downloadDocumentFile(fileUrl, fileName)
}

// 서류 행 스타일 결정
const getRowClass = (doc: MergedDocument) => {
  if (doc.require_type === 'required' && !doc.is_complete) {
    return 'table-danger' // 필수 서류 미제출: 빨간색
  }
  if (!doc.is_complete && doc.submitted_quantity === 0) {
    return 'table-warning' // 미제출: 노란색
  }
  return ''
}

// Watch: contractorId 변경 시 데이터 로드
watch(
  contractorId,
  newId => {
    if (newId) {
      loadData()
    } else {
      // contractorId가 없으면 데이터 초기화
      contStore.contractDocumentList = []
    }
  },
  { immediate: true },
)

onMounted(() => {
  if (contractorId.value) {
    loadData()
  }
})
</script>

<template>
  <CCard class="mb-3">
    <CCardHeader>
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <strong>구비서류 제출 현황</strong>
          <span v-if="contractor" class="ms-2 text-muted">
            ({{ contractor.name }} / {{ contractor.__str__ }})
          </span>
        </div>
        <div class="text-end">
          <v-progress-circular
            :model-value="completionRate"
            :size="50"
            :width="5"
            :color="completionRate === 100 ? 'success' : 'primary'"
          >
            {{ completionRate }}%
          </v-progress-circular>
          <div v-if="missingRequiredDocs > 0" class="text-danger mt-1" style="font-size: 0.875rem">
            필수 서류 미제출: {{ missingRequiredDocs }}건
          </div>
        </div>
      </div>
    </CCardHeader>
    <CCardBody>
      <!-- 로딩 상태 -->
      <div v-if="isLoading" class="text-center py-5">
        <v-progress-circular indeterminate color="primary" />
        <div class="mt-2">데이터 로딩 중...</div>
      </div>

      <!-- 계약자 미선택 -->
      <div v-else-if="!contractorId" class="text-center py-5 text-muted">
        계약자를 선택해주세요.
      </div>

      <!-- 서류 목록이 없음 -->
      <div v-else-if="mergedDocuments.length === 0" class="text-center py-5 text-muted">
        등록된 필요 서류가 없습니다.
      </div>

      <!-- 서류 목록 테이블 -->
      <CTable v-else hover responsive>
        <colgroup>
          <col style="width: 25%" />
          <col style="width: 10%" />
          <col style="width: 12%" />
          <col style="width: 12%" />
          <col style="width: 12%" />
          <col style="width: 20%" />
          <col style="width: 9%" />
        </colgroup>
        <CTableHead>
          <CTableRow class="text-center">
            <CTableHeaderCell>해당서류</CTableHeaderCell>
            <CTableHeaderCell>필수여부</CTableHeaderCell>
            <CTableHeaderCell>필요수량</CTableHeaderCell>
            <CTableHeaderCell>제출수량</CTableHeaderCell>
            <CTableHeaderCell>제출일자</CTableHeaderCell>
            <CTableHeaderCell>첨부파일</CTableHeaderCell>
            <CTableHeaderCell>완료</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow
            v-for="doc in mergedDocuments"
            :key="`required-${doc.pk}`"
            :class="getRowClass(doc)"
          >
            <!-- 서류명 -->
            <CTableDataCell>
              <div class="d-flex align-items-center">
                <v-icon
                  v-if="doc.require_type === 'required'"
                  icon="mdi-star"
                  color="error"
                  size="16"
                  class="me-1"
                />
                {{ doc.document_name }}
              </div>
              <div v-if="doc.description" class="text-muted" style="font-size: 0.8rem">
                {{ doc.description }}
              </div>
            </CTableDataCell>

            <!-- 필수여부 -->
            <CTableDataCell class="text-center">
              <v-chip :color="doc.require_type === 'required' ? 'error' : 'default'" size="small">
                {{ doc.required }}
              </v-chip>
            </CTableDataCell>

            <!-- 필요수량 -->
            <CTableDataCell class="text-center">
              {{ doc.quantity }}
            </CTableDataCell>

            <!-- 제출수량 (편집 가능) -->
            <CTableDataCell class="text-center">
              <span
                v-if="editingDocId !== doc.pk || editingField !== 'quantity'"
                @dblclick="startEdit(doc.pk, 'quantity')"
                class="pointer"
              >
                {{ doc.submitted_quantity }}
              </span>
              <CFormInput
                v-else
                type="number"
                min="0"
                :value="doc.submitted_quantity"
                size="sm"
                style="width: 70px; margin: 0 auto"
                @input="onQuantityChange(doc, parseInt(($event.target as HTMLInputElement).value))"
                @blur="endEdit"
                @keydown.enter="endEdit"
              />
            </CTableDataCell>

            <!-- 제출일자 (편집 가능) -->
            <CTableDataCell class="text-center">
              <span
                v-if="editingDocId !== doc.pk || editingField !== 'date'"
                @dblclick="startEdit(doc.pk, 'date')"
                class="pointer"
              >
                {{ doc.submission_date || '-' }}
              </span>
              <CFormInput
                v-else
                type="date"
                :value="doc.submission_date || ''"
                size="sm"
                style="width: 140px; margin: 0 auto"
                @change="
                  ((doc.submission_date = ($event.target as HTMLInputElement).value),
                  onDateChange(doc))
                "
                @blur="endEdit"
              />
            </CTableDataCell>

            <!-- 첨부파일 -->
            <CTableDataCell>
              <div class="d-flex flex-wrap gap-1">
                <v-chip
                  v-for="file in doc.files"
                  :key="file.pk"
                  size="small"
                  closable
                  @click="downloadFile(file.file, file.file_name)"
                  @click:close="deleteFile(file.pk, doc.contract_doc_pk!)"
                >
                  <v-icon icon="mdi-file" size="14" class="me-1" />
                  {{ file.file_name }}
                </v-chip>
                <v-btn
                  size="x-small"
                  icon="mdi-plus"
                  variant="outlined"
                  @click="openFileUpload(doc)"
                />
              </div>
            </CTableDataCell>

            <!-- 완료 상태 -->
            <CTableDataCell class="text-center">
              <v-icon
                :icon="doc.is_complete ? 'mdi-check-circle' : 'mdi-alert-circle'"
                :color="doc.is_complete ? 'success' : 'warning'"
                size="24"
              />
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCardBody>
  </CCard>

  <!-- 파일 업로드 다이얼로그 -->
  <v-dialog v-model="fileUploadDialog" max-width="500">
    <v-card>
      <v-card-title>파일 업로드</v-card-title>
      <v-card-text>
        <CFormInput type="file" @change="onFileSelect" />
        <div v-if="selectedFile" class="mt-2">선택된 파일: {{ selectedFile.name }}</div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn color="grey" @click="closeFileUpload">취소</v-btn>
        <v-btn color="primary" @click="uploadFile" :disabled="!selectedFile">업로드</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.pointer {
  cursor: pointer;
}

.table-danger {
  background-color: #f8d7da !important;
}

.table-warning {
  background-color: #fff3cd !important;
}
</style>
