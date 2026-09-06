<script lang="ts" setup>
import { ref, reactive, computed } from 'vue'
import { useSales } from '@/store/pinia/sales'
import { usePerms } from '@/composables/usePerms'
import type { SalesPerson, SalesPersonDocument, SalesDocType } from '@/store/types/sales'
import FormModal from '@/components/Modals/FormModal.vue'
import { TableSecondary } from '@/utils/cssMixins'

const emit = defineEmits(['updated'])

const { can, PERM } = usePerms()
const salesStore = useSales()
const modalRef = ref()
const fileInputRef = ref<HTMLInputElement | null>(null)

const currentPerson = ref<SalesPerson | null>(null)
const selectedFile = ref<File | null>(null)
const isUploading = ref(false)

const docTypeLabels: Record<SalesDocType, string> = {
  '1': '주민등록등본/초본',
  '2': '통장 사본 (계좌 사본)',
  '3': '신분증 사본',
  '4': '영업 위촉계약서',
  '5': '각종 서약서/각서',
  '9': '기타 증빙서류',
}

const docTypeBadgeColor: Record<SalesDocType, string> = {
  '1': 'primary',
  '2': 'success',
  '3': 'info',
  '4': 'warning',
  '5': 'danger',
  '9': 'secondary',
}

const form = reactive({
  doc_type: '1' as SalesDocType,
  title: '',
})

const documents = computed(() => salesStore.personDocumentList)

const open = async (person: SalesPerson) => {
  currentPerson.value = person
  form.doc_type = '1'
  form.title = ''
  selectedFile.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  await salesStore.fetchPersonDocuments(person.id)
  modalRef.value.callModal()
}

const onDocTypeChange = () => {
  if (form.doc_type === '5') {
    form.title = '보안/비밀유지 서약서'
  } else if (form.doc_type === '9') {
    form.title = '사업자등록증 사본'
  } else {
    form.title = ''
  }
}

const onFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  } else {
    selectedFile.value = null
  }
}

const handleUpload = async () => {
  if (!currentPerson.value) return
  if (!selectedFile.value) {
    alert('업로드할 서류 파일을 선택해주세요.')
    return
  }

  isUploading.value = true
  try {
    const formData = new FormData()
    formData.append('sales_person', String(currentPerson.value.id))
    formData.append('doc_type', form.doc_type)
    if (form.title.trim()) {
      formData.append('title', form.title.trim())
    }
    formData.append('file', selectedFile.value)

    await salesStore.uploadPersonDocument(formData)
    await salesStore.fetchPersonDocuments(currentPerson.value.id)

    selectedFile.value = null
    form.title = ''
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
    emit('updated')
  } finally {
    isUploading.value = false
  }
}

const toggleVerify = async (doc: SalesPersonDocument) => {
  if (!currentPerson.value) return
  await salesStore.verifyPersonDocument(doc.id, !doc.is_verified)
  await salesStore.fetchPersonDocuments(currentPerson.value.id)
  emit('updated')
}

const removeDoc = async (doc: SalesPersonDocument) => {
  if (!currentPerson.value) return
  if (confirm(`'${doc.title}' 서류를 삭제하시겠습니까?`)) {
    await salesStore.deletePersonDocument(doc.id)
    await salesStore.fetchPersonDocuments(currentPerson.value.id)
    emit('updated')
  }
}

const formatFileSize = (bytes?: number | null) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

defineExpose({ open })
</script>

<template>
  <FormModal ref="modalRef" size="xl">
    <template #icon>
      <v-icon icon="mdi-file-document-multiple-outline" size="small" color="primary" class="mr-2" />
    </template>
    <template #header>
      {{ currentPerson?.name }} [{{ currentPerson?.duty_display || '상담사' }}] 증빙 서류 관리
    </template>
    <template #default>
      <CModalBody>
        <!-- 1. 신규 서류 첨부 영역 -->
        <CCard v-if="can(PERM.SALES_MANAGE)" class="mb-4 bg-light border">
          <CCardHeader class="py-2 bg-transparent fw-bold d-flex align-items-center">
            <v-icon icon="mdi-cloud-upload-outline" size="small" class="mr-1 text-primary" />
            신규 서류 접수 및 업로드
          </CCardHeader>
          <CCardBody class="py-3">
            <CRow class="g-2 align-items-end">
              <CCol md="3">
                <CFormLabel class="small fw-semibold">서류 구분 *</CFormLabel>
                <CFormSelect v-model="form.doc_type" size="sm" @change="onDocTypeChange">
                  <option value="1">주민등록등본/초본</option>
                  <option value="2">통장 사본 (계좌 사본)</option>
                  <option value="3">신분증 사본</option>
                  <option value="4">영업 위촉계약서</option>
                  <option value="5">각종 서약서/각서</option>
                  <option value="9">기타 증빙서류</option>
                </CFormSelect>
              </CCol>

              <CCol md="4">
                <CFormLabel class="small fw-semibold">세부 명칭 (선택)</CFormLabel>
                <CFormInput
                  v-model="form.title"
                  size="sm"
                  placeholder="예: 보안서약서, 청렴이행각서, 사업자등록증 등"
                />
              </CCol>

              <CCol md="3">
                <CFormLabel class="small fw-semibold">파일 선택 (PDF, 이미지) *</CFormLabel>
                <CFormInput
                  ref="fileInputRef"
                  type="file"
                  size="sm"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                  @change="onFileChange"
                />
              </CCol>

              <CCol md="2">
                <v-btn
                  color="primary"
                  size="small"
                  block
                  :loading="isUploading"
                  :disabled="!selectedFile"
                  @click="handleUpload"
                >
                  <v-icon icon="mdi-upload" size="small" class="mr-1" />
                  서류 등록
                </v-btn>
              </CCol>
            </CRow>
          </CCardBody>
        </CCard>

        <!-- 2. 기제출 서류 목록 테이블 -->
        <div class="d-flex justify-content-between align-items-center mb-2">
          <div class="fw-bold d-flex align-items-center">
            <v-icon icon="mdi-folder-file-outline" size="small" class="mr-1 text-primary" />
            제출된 증빙 서류 목록
            <CBadge color="primary" class="ms-2" shape="rounded-pill">
              {{ documents.length }}건
            </CBadge>
          </div>
          <small class="text-body-secondary">
            * 서류 검토 후 [검증]을 클릭하면 관리자 검증 완료 처리됩니다.
          </small>
        </div>

        <CTable hover responsive class="align-middle text-center small border">
          <CTableHead :color="TableSecondary">
            <CTableRow>
              <CTableHeaderCell style="width: 140px">서류 구분</CTableHeaderCell>
              <CTableHeaderCell style="width: 180px">세부 명칭</CTableHeaderCell>
              <CTableHeaderCell>첨부 파일명</CTableHeaderCell>
              <CTableHeaderCell style="width: 90px">크기</CTableHeaderCell>
              <CTableHeaderCell style="width: 110px">등록일</CTableHeaderCell>
              <CTableHeaderCell style="width: 110px">검증 상태</CTableHeaderCell>
              <CTableHeaderCell style="width: 140px">관리</CTableHeaderCell>
            </CTableRow>
          </CTableHead>
          <CTableBody>
            <CTableRow v-for="doc in documents" :key="doc.id">
              <CTableDataCell>
                <CBadge :color="docTypeBadgeColor[doc.doc_type] || 'secondary'" shape="rounded-pill">
                  {{ doc.doc_type_display || docTypeLabels[doc.doc_type] }}
                </CBadge>
              </CTableDataCell>
              <CTableDataCell class="fw-semibold text-start">
                {{ doc.title }}
              </CTableDataCell>
              <CTableDataCell class="text-start">
                <a
                  :href="doc.file"
                  target="_blank"
                  class="text-decoration-none text-primary d-inline-flex align-items-center"
                >
                  <v-icon icon="mdi-file-pdf-box" size="small" class="me-1 text-danger" />
                  <span class="text-truncate" style="max-width: 220px">{{ doc.file_name }}</span>
                </a>
              </CTableDataCell>
              <CTableDataCell class="text-body-secondary">
                {{ formatFileSize(doc.file_size) }}
              </CTableDataCell>
              <CTableDataCell class="text-body-secondary">
                {{ doc.created_at ? doc.created_at.substring(0, 10) : '-' }}
              </CTableDataCell>
              <CTableDataCell>
                <CBadge
                  v-if="doc.is_verified"
                  color="success"
                  class="px-2 py-1"
                >
                  <v-icon icon="mdi-check-circle" size="x-small" class="me-1" />
                  검증완료
                </CBadge>
                <CBadge
                  v-else
                  color="warning"
                  class="px-2 py-1 text-dark"
                >
                  <v-icon icon="mdi-clock-outline" size="x-small" class="me-1" />
                  확인대기
                </CBadge>
              </CTableDataCell>
              <CTableDataCell>
                <div class="d-flex justify-content-center align-items-center gap-1">
                  <!-- 다운로드/열기 -->
                  <v-btn
                    :href="doc.file"
                    target="_blank"
                    icon="mdi-download"
                    size="x-small"
                    variant="text"
                    color="primary"
                    title="다운로드/열기"
                  />
                  <!-- 검증 토글 -->
                  <v-btn
                    v-if="can(PERM.SALES_MANAGE)"
                    size="x-small"
                    :color="doc.is_verified ? 'secondary' : 'success'"
                    variant="tonal"
                    @click="toggleVerify(doc)"
                  >
                    {{ doc.is_verified ? '검증취소' : '검증' }}
                  </v-btn>
                  <!-- 삭제 -->
                  <v-btn
                    v-if="can(PERM.SALES_MANAGE)"
                    icon="mdi-delete"
                    size="x-small"
                    variant="text"
                    color="error"
                    title="서류 삭제"
                    @click="removeDoc(doc)"
                  />
                </div>
              </CTableDataCell>
            </CTableRow>

            <CTableRow v-if="documents.length === 0">
              <CTableDataCell colspan="7" class="py-4 text-body-secondary">
                <v-icon icon="mdi-file-hidden" size="large" class="mb-2 text-muted" />
                <div>등록된 증빙 서류가 없습니다. 상단에서 서류를 등록해주세요.</div>
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </CModalBody>
      <CModalFooter>
        <v-btn color="light" size="small" flat @click="modalRef.close()">닫기</v-btn>
      </CModalFooter>
    </template>
  </FormModal>
</template>
