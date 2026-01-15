<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { OfficialLetter } from '@/store/types/docs'
import { useDocs } from '@/store/pinia/docs'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps<{
  company: number
  letter?: OfficialLetter
  viewRoute: string
  writeAuth: boolean
}>()

const emit = defineEmits<{
  onSubmit: [payload: OfficialLetter]
}>()

const router = useRouter()
const docStore = useDocs()

const isEdit = ref(false)
const nextDocNumber = ref('')

// Form fields
const form = ref<OfficialLetter>({
  company: null,
  title: '',
  recipient_name: '',
  recipient_address: '',
  recipient_contact: '',
  recipient_reference: '',
  sender_name: '',
  sender_position: '',
  sender_department: '',
  content: '',
  issue_date: new Date().toISOString().substring(0, 10),
})

const validated = ref(false)

watch(
  () => props.letter,
  letter => {
    if (letter) {
      isEdit.value = true
      form.value = { ...letter }
    }
  },
  { immediate: true },
)

onMounted(async () => {
  if (!props.letter && props.company) {
    // Get next document number for new letters
    nextDocNumber.value = await docStore.getNextDocumentNumber(props.company)
  }
})

const onSubmit = () => {
  validated.value = true

  // Validate required fields
  if (!form.value.title || !form.value.recipient_name || !form.value.sender_name || !form.value.content || !form.value.issue_date) {
    return
  }

  emit('onSubmit', form.value)
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
          <CIcon name="cilEnvelopeLetter" class="me-2" />
          {{ isEdit ? '공문 수정' : '공문 작성' }}
        </h4>
        <small v-if="!isEdit && nextDocNumber" class="text-muted">
          예상 문서번호: {{ nextDocNumber }}
        </small>
      </CCol>
    </CRow>

    <CForm :validated="validated" @submit.prevent="onSubmit">
      <!-- Basic Info -->
      <CCard class="mb-4">
        <CCardHeader>
          <strong>기본 정보</strong>
        </CCardHeader>
        <CCardBody>
          <CRow class="mb-3">
            <CCol md="6">
              <CFormLabel>
                제목 <span class="text-danger">*</span>
              </CFormLabel>
              <CFormInput
                v-model="form.title"
                placeholder="공문 제목을 입력하세요"
                required
                :invalid="validated && !form.title"
              />
              <CFormFeedback invalid>제목을 입력해주세요.</CFormFeedback>
            </CCol>
            <CCol md="6">
              <CFormLabel>
                발신일자 <span class="text-danger">*</span>
              </CFormLabel>
              <DatePicker
                v-model="form.issue_date"
                placeholder="발신일자 선택"
                required
              />
            </CCol>
          </CRow>
        </CCardBody>
      </CCard>

      <!-- Recipient Info -->
      <CCard class="mb-4">
        <CCardHeader>
          <strong>수신처 정보</strong>
        </CCardHeader>
        <CCardBody>
          <CRow class="mb-3">
            <CCol md="6">
              <CFormLabel>
                수신처명 <span class="text-danger">*</span>
              </CFormLabel>
              <CFormInput
                v-model="form.recipient_name"
                placeholder="수신처명 (예: OO주식회사)"
                required
                :invalid="validated && !form.recipient_name"
              />
              <CFormFeedback invalid>수신처명을 입력해주세요.</CFormFeedback>
            </CCol>
            <CCol md="6">
              <CFormLabel>참조</CFormLabel>
              <CFormInput
                v-model="form.recipient_reference"
                placeholder="참조 (예: 대표이사 귀하)"
              />
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CCol md="6">
              <CFormLabel>수신처 주소</CFormLabel>
              <CFormInput
                v-model="form.recipient_address"
                placeholder="수신처 주소"
              />
            </CCol>
            <CCol md="6">
              <CFormLabel>수신처 연락처</CFormLabel>
              <CFormInput
                v-model="form.recipient_contact"
                placeholder="연락처 (전화번호, 팩스 등)"
              />
            </CCol>
          </CRow>
        </CCardBody>
      </CCard>

      <!-- Sender Info -->
      <CCard class="mb-4">
        <CCardHeader>
          <strong>발신자 정보</strong>
        </CCardHeader>
        <CCardBody>
          <CRow class="mb-3">
            <CCol md="4">
              <CFormLabel>
                발신자명 <span class="text-danger">*</span>
              </CFormLabel>
              <CFormInput
                v-model="form.sender_name"
                placeholder="발신자명 (예: 홍길동)"
                required
                :invalid="validated && !form.sender_name"
              />
              <CFormFeedback invalid>발신자명을 입력해주세요.</CFormFeedback>
            </CCol>
            <CCol md="4">
              <CFormLabel>직위</CFormLabel>
              <CFormInput
                v-model="form.sender_position"
                placeholder="직위 (예: 대표이사)"
              />
            </CCol>
            <CCol md="4">
              <CFormLabel>부서</CFormLabel>
              <CFormInput
                v-model="form.sender_department"
                placeholder="부서 (예: 경영지원팀)"
              />
            </CCol>
          </CRow>
        </CCardBody>
      </CCard>

      <!-- Content -->
      <CCard class="mb-4">
        <CCardHeader>
          <strong>공문 내용</strong>
        </CCardHeader>
        <CCardBody>
          <CFormLabel>
            내용 <span class="text-danger">*</span>
          </CFormLabel>
          <CFormTextarea
            v-model="form.content"
            placeholder="공문 본문을 입력하세요"
            rows="15"
            required
            :invalid="validated && !form.content"
          />
          <CFormFeedback invalid>공문 내용을 입력해주세요.</CFormFeedback>
          <CFormText class="text-muted">
            줄바꿈은 그대로 반영됩니다. 문단을 구분하려면 빈 줄을 추가하세요.
          </CFormText>
        </CCardBody>
      </CCard>

      <!-- Actions -->
      <CRow>
        <CCol class="d-flex justify-content-between">
          <CButton color="secondary" variant="outline" @click="goBack">
            <CIcon name="cilArrowLeft" class="me-1" />
            취소
          </CButton>
          <CButton type="submit" color="primary" :disabled="!writeAuth">
            <CIcon name="cilSave" class="me-1" />
            {{ isEdit ? '수정 저장' : '저장' }}
          </CButton>
        </CCol>
      </CRow>
    </CForm>
  </div>
</template>
