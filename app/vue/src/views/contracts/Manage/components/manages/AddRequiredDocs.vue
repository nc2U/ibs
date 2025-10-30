<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { cutString } from '@/utils/baseMixins.ts'
import { downloadFile } from '@/utils/helper'
import { useContract } from '@/store/pinia/contract.ts'
import type { ContractDocument, Contractor, RequiredDocs } from '@/store/types/contract'

// Props
const props = defineProps<{
  sortFilter?: 'proof' | 'pledge'
}>()

const route = useRoute()
const contStore = useContract()

// 계약자 ID
const contractorId = computed(() =>
  route.params.contractorId ? parseInt(route.params.contractorId as string, 10) : null,
)

// Store 데이터
const requiredDocsList = computed(() => {
  const list = contStore.requiredDocsList
  // sortFilter가 있으면 필터링
  if (props.sortFilter && list) return list.filter(doc => (doc as any).sort === props.sortFilter)

  return list
})
const contractDocumentList = computed(() => contStore.contractDocumentList)
const contractor = computed(() => contStore.contractor as Contractor | null)

// 편집 중인 문서 ID 추적
const editingDocId = ref<number | null>(null)

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
      is_complete: isComplete,
      files: submitted?.files || [],
    }
  })
})

// 완료율 계산 (필수 서류만)
const completionRate = computed(() => {
  const requiredDocs = mergedDocuments.value.filter(doc => doc.require_type === 'required')
  if (requiredDocs.length === 0) return 0
  const completed = requiredDocs.filter(doc => doc.is_complete).length
  return Math.round((completed / requiredDocs.length) * 100)
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
    }

    // 서버에 실제 데이터가 있는지 확인
    const existingDoc = await contStore.checkContractDocumentExists(contractorId.value, doc.pk)

    if (existingDoc) {
      // 서버에 데이터가 있으면 업데이트
      await contStore.updateContractDocument(existingDoc.pk, payload)
      // 클라이언트 상태도 동기화
      doc.contract_doc_pk = existingDoc.pk
    } else {
      // 서버에 데이터가 없으면 신규 생성
      const newDoc = await contStore.createContractDocument(payload as ContractDocument)
      // 클라이언트 상태 업데이트
      doc.contract_doc_pk = newDoc.pk
    }
  } catch (error) {
    console.error('서류 저장 실패:', error)
  }
}

// 수량 변경 핸들러 (debounce 적용)
const onQuantityChange = (doc: MergedDocument, value: number) => (doc.submitted_quantity = value)

// 편집 모드 토글
const startEdit = (docId: number) => {
  editingDocId.value = docId
}

const endEdit = async (doc: MergedDocument) => {
  await saveDocument(doc)
  editingDocId.value = null
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
  <CCardBody class="pt-0">
    <div class="text-end mb-2">
      <span v-if="missingRequiredDocs > 0" class="text-danger mt-1 mr-2" style="font-size: 0.8rem">
        필수 서류 미제출: {{ missingRequiredDocs }}건
      </span>
      <v-progress-circular
        :model-value="completionRate"
        :size="40"
        :width="4"
        :color="completionRate === 100 ? 'primary' : 'warning'"
        style="font-size: 0.6rem"
      >
        {{ completionRate }}%
      </v-progress-circular>
    </div>

    <!-- 로딩 상태 -->
    <div v-if="isLoading" class="text-center py-5">
      <v-progress-circular indeterminate color="primary" />
      <div class="mt-2">데이터 로딩 중...</div>
    </div>

    <!-- 계약자 미선택 -->
    <div v-else-if="!contractorId" class="text-center py-5 text-grey">계약자를 선택해주세요.</div>

    <!-- 서류 목록이 없음 -->
    <div v-else-if="mergedDocuments.length === 0" class="text-center py-5 text-grey">
      등록된 필요 서류가 없습니다.<br />
      <v-icon icon="mdi-arrow-right" size="18" class="me-1" />
      <router-link :to="{ name: '구비 서류 등록' }">구비 서류 등록 바로가기</router-link>
    </div>

    <!-- 서류 목록 테이블 -->
    <CTable v-else hover responsive>
      <colgroup>
        <col style="width: 25%" />
        <col style="width: 12%" />
        <col style="width: 12%" />
        <col style="width: 15%" />
        <col style="width: 27%" />
        <col style="width: 9%" />
      </colgroup>
      <CTableHead>
        <CTableRow class="text-center" color="light">
          <CTableHeaderCell>해당서류</CTableHeaderCell>
          <CTableHeaderCell>필수여부</CTableHeaderCell>
          <CTableHeaderCell>필요수량</CTableHeaderCell>
          <CTableHeaderCell>제출수량</CTableHeaderCell>
          <CTableHeaderCell>첨부파일</CTableHeaderCell>
          <CTableHeaderCell>완료</CTableHeaderCell>
        </CTableRow>
      </CTableHead>
      <CTableBody>
        <CTableRow v-for="doc in mergedDocuments" :key="`required-${doc.pk}`">
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
              {{ cutString(doc.document_name, 10) }}
              <v-tooltip activator="parent">{{ doc.document_name }}</v-tooltip>
            </div>
          </CTableDataCell>

          <!-- 필수여부 -->
          <CTableDataCell class="text-center">
            <v-chip :color="doc.require_type === 'required' ? 'error' : 'primary'" size="x-small">
              {{ doc.required }}
              <v-tooltip v-if="doc.description" activator="parent">
                {{ doc.description }}
              </v-tooltip>
            </v-chip>
          </CTableDataCell>

          <!-- 필요수량 -->
          <CTableDataCell class="text-center">
            {{ doc.quantity }}
          </CTableDataCell>

          <!-- 제출수량 (편집 가능) -->
          <CTableDataCell
            class="text-center pointer"
            :class="getRowClass(doc)"
            @dblclick="startEdit(doc.pk)"
          >
            <span
              v-if="editingDocId !== doc.pk"
              :class="{ 'text-primary': doc.is_complete, strong: doc.is_complete }"
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
              @blur="endEdit(doc)"
              @keydown.enter="endEdit"
            />
          </CTableDataCell>

          <!-- 첨부파일 -->
          <CTableDataCell>
            <div
              class="d-flex align-items-center justify-content-end gap-1"
              style="flex-wrap: nowrap; overflow-x: auto"
            >
              <v-chip
                v-for="file in doc.files"
                :key="file.pk"
                size="small"
                closable
                @click="downloadFile(file.file, file.file_name)"
                @click:close="deleteFile(file.pk, doc.contract_doc_pk!)"
                style="flex-shrink: 0"
              >
                <v-icon icon="mdi-file" size="14" class="me-1" />
                {{ cutString(file.file_name, 3) }}
              </v-chip>
              <v-icon
                icon="mdi-plus-circle"
                size="22"
                class="me-1 pointer"
                color="secondary"
                @click="openFileUpload(doc)"
              />
            </div>
          </CTableDataCell>

          <!-- 완료 상태 -->
          <CTableDataCell class="text-center">
            <v-icon
              :icon="doc.is_complete ? 'mdi-check-circle' : 'mdi-alert-circle'"
              :color="doc.is_complete ? 'success' : 'warning'"
              size="22"
            />
          </CTableDataCell>
        </CTableRow>
      </CTableBody>
    </CTable>
  </CCardBody>

  <!-- 파일 업로드 다이얼로그 -->
  <v-dialog v-model="fileUploadDialog" max-width="500">
    <v-card>
      <v-card-title>파일 업로드</v-card-title>
      <v-card-text>
        <CFormInput type="file" @change="onFileSelect" />
        <div v-if="selectedFile" class="mt-2">선택된 파일: {{ (selectedFile as File)?.name }}</div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn color="grey" @click="closeFileUpload">취소</v-btn>
        <v-btn color="primary" @click="uploadFile" :disabled="!selectedFile">업로드</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
