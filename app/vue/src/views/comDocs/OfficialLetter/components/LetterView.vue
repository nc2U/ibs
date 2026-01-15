<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import type { OfficialLetter } from '@/store/types/docs'
import type { LetterFilter } from '@/store/pinia/docs'
import { useDocs } from '@/store/pinia/docs'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps<{
  letter: OfficialLetter | null
  viewRoute: string
  writeAuth: boolean
  letterFilter: LetterFilter
}>()

const emit = defineEmits<{
  onDelete: [pk: number]
  generatePdf: [pk: number]
}>()

const router = useRouter()
const docStore = useDocs()

const showDeleteModal = ref(false)
const pdfLoading = ref(false)

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
  showDeleteModal.value = true
}

const onDelete = () => {
  if (props.letter?.pk) {
    emit('onDelete', props.letter.pk)
  }
  showDeleteModal.value = false
}

const onGeneratePdf = async () => {
  if (props.letter?.pk) {
    pdfLoading.value = true
    try {
      emit('generatePdf', props.letter.pk)
    } finally {
      pdfLoading.value = false
    }
  }
}

const downloadPdf = () => {
  if (props.letter?.pdf_file) {
    window.open(props.letter.pdf_file, '_blank')
  }
}

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

const formatDateTime = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return dateStr.replace('T', ' ').substring(0, 19)
}
</script>

<template>
  <div v-if="letter">
    <!-- Navigation -->
    <CRow class="mb-3">
      <CCol class="d-flex justify-content-between align-items-center">
        <CButton color="secondary" variant="outline" size="sm" @click="goToList">
          <CIcon name="cilList" class="me-1" />
          목록
        </CButton>
        <div>
          <CButton
            color="light"
            size="sm"
            :disabled="!prevPk"
            class="me-1"
            @click="goToPrev"
          >
            <CIcon name="cilChevronLeft" />
            이전
          </CButton>
          <CButton
            color="light"
            size="sm"
            :disabled="!nextPk"
            @click="goToNext"
          >
            다음
            <CIcon name="cilChevronRight" />
          </CButton>
        </div>
      </CCol>
    </CRow>

    <!-- Letter Header -->
    <CCard class="mb-4">
      <CCardHeader class="d-flex justify-content-between align-items-center">
        <div>
          <CBadge color="primary" class="me-2">{{ letter.document_number }}</CBadge>
          <strong>{{ letter.title }}</strong>
        </div>
        <div>
          <small class="text-muted">
            작성자: {{ letter.creator?.username || '-' }} |
            작성일: {{ formatDateTime(letter.created) }}
          </small>
        </div>
      </CCardHeader>
    </CCard>

    <!-- Letter Info -->
    <CRow>
      <CCol md="6">
        <CCard class="mb-4">
          <CCardHeader>
            <strong>수신처 정보</strong>
          </CCardHeader>
          <CCardBody>
            <table class="table table-borderless mb-0">
              <tbody>
                <tr>
                  <th style="width: 100px">수신처명</th>
                  <td>{{ letter.recipient_name }}</td>
                </tr>
                <tr v-if="letter.recipient_reference">
                  <th>참조</th>
                  <td>{{ letter.recipient_reference }}</td>
                </tr>
                <tr v-if="letter.recipient_address">
                  <th>주소</th>
                  <td>{{ letter.recipient_address }}</td>
                </tr>
                <tr v-if="letter.recipient_contact">
                  <th>연락처</th>
                  <td>{{ letter.recipient_contact }}</td>
                </tr>
              </tbody>
            </table>
          </CCardBody>
        </CCard>
      </CCol>

      <CCol md="6">
        <CCard class="mb-4">
          <CCardHeader>
            <strong>발신자 정보</strong>
          </CCardHeader>
          <CCardBody>
            <table class="table table-borderless mb-0">
              <tbody>
                <tr>
                  <th style="width: 100px">발신자명</th>
                  <td>{{ letter.sender_name }}</td>
                </tr>
                <tr v-if="letter.sender_position">
                  <th>직위</th>
                  <td>{{ letter.sender_position }}</td>
                </tr>
                <tr v-if="letter.sender_department">
                  <th>부서</th>
                  <td>{{ letter.sender_department }}</td>
                </tr>
                <tr>
                  <th>발신일자</th>
                  <td>{{ formatDate(letter.issue_date) }}</td>
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
        <strong>공문 내용</strong>
      </CCardHeader>
      <CCardBody>
        <div class="letter-content" style="white-space: pre-wrap; line-height: 1.8">
          {{ letter.content }}
        </div>
      </CCardBody>
    </CCard>

    <!-- PDF Section -->
    <CCard class="mb-4">
      <CCardHeader>
        <strong>PDF 파일</strong>
      </CCardHeader>
      <CCardBody>
        <div v-if="letter.pdf_file" class="d-flex align-items-center">
          <CBadge color="success" class="me-3">
            <CIcon name="cilFile" class="me-1" />
            PDF 생성됨
          </CBadge>
          <CButton color="primary" size="sm" @click="downloadPdf">
            <CIcon name="cilCloudDownload" class="me-1" />
            다운로드
          </CButton>
          <CButton
            v-if="writeAuth"
            color="warning"
            size="sm"
            class="ms-2"
            :disabled="pdfLoading"
            @click="onGeneratePdf"
          >
            <CSpinner v-if="pdfLoading" size="sm" class="me-1" />
            <CIcon v-else name="cilReload" class="me-1" />
            재생성
          </CButton>
        </div>
        <div v-else>
          <span class="text-muted me-3">PDF 파일이 아직 생성되지 않았습니다.</span>
          <CButton
            v-if="writeAuth"
            color="primary"
            size="sm"
            :disabled="pdfLoading"
            @click="onGeneratePdf"
          >
            <CSpinner v-if="pdfLoading" size="sm" class="me-1" />
            <CIcon v-else name="cilFile" class="me-1" />
            PDF 생성
          </CButton>
        </div>
      </CCardBody>
    </CCard>

    <!-- Action Buttons -->
    <CRow>
      <CCol class="d-flex justify-content-between">
        <CButton color="secondary" variant="outline" @click="goToList">
          <CIcon name="cilList" class="me-1" />
          목록으로
        </CButton>
        <div v-if="writeAuth">
          <CButton color="danger" variant="outline" class="me-2" @click="confirmDelete">
            <CIcon name="cilTrash" class="me-1" />
            삭제
          </CButton>
          <CButton color="primary" @click="goToEdit">
            <CIcon name="cilPencil" class="me-1" />
            수정
          </CButton>
        </div>
      </CCol>
    </CRow>

    <!-- Delete Confirm Modal -->
    <ConfirmModal v-model="showDeleteModal" @confirmed="onDelete">
      <template #header>공문 삭제</template>
      <template #default>
        <p>이 공문을 삭제하시겠습니까?</p>
        <p class="text-muted mb-0">
          <small>문서번호: {{ letter.document_number }}</small><br>
          <small>제목: {{ letter.title }}</small>
        </p>
      </template>
    </ConfirmModal>
  </div>

  <div v-else class="text-center py-5">
    <CSpinner color="primary" />
    <p class="mt-3 text-muted">공문 정보를 불러오는 중...</p>
  </div>
</template>

<style scoped>
.letter-content {
  min-height: 200px;
  padding: 1rem;
  background-color: #fafafa;
  border-radius: 4px;
}
</style>
