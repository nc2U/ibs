<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useDocs } from '@/store/pinia/docs'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company'
import type { OfficialLetter } from '@/store/types/docs'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps<{
  company: number
  letter?: OfficialLetter
  viewRoute: string
}>()

const emit = defineEmits<{
  onSubmit: [payload: OfficialLetter]
}>()

const { can, PERM } = usePerms()
const accStore = useAccount()
const comStore = useCompany()
const sealList = computed(() => comStore.sealList)
const selectedSealImage = computed(() => {
  if (!form.value.seal) return null
  const s = sealList.value.find(item => item.pk === form.value.seal)
  return s?.seal_image || null
})

const isEdit = computed(() => !!props.letter?.pk)
const canOLManage = computed(() => (isEdit.value ? can(PERM.DOCS_UPDATE) : can(PERM.DOCS_CREATE)))

const router = useRouter()
const docStore = useDocs()

const nextDocNumber = ref('')

// Form fields
const form = ref<OfficialLetter>({
  company: null,
  title: '',
  recipient_name: '',
  via: '',
  recipient_reference: '',
  content: '',
  attachment_text: '',
  issue_date: new Date().toISOString().substring(0, 10),
  seal: null,
  sender_name: '',
  sender_position: '',
  sender_department: '',
  sender_zipcode: '',
  sender_address: '',
  // 발송 관리 메타 정보
  recipient_address: '',
  recipient_contact: '',
  dispatch_method: 'email',
  tracking_number: '',
  dispatched_at: null,
})

const validated = ref(false)

watch(
  () => props.letter,
  letter => {
    if (letter) {
      form.value = {
        ...letter,
        via: letter.via || '',
        attachment_text: letter.attachment_text || '',
        sender_zipcode: letter.sender_zipcode || '',
        sender_address: letter.sender_address || '',
        dispatch_method: letter.dispatch_method || 'email',
        tracking_number: letter.tracking_number || '',
      }
    }
  },
  { immediate: true },
)

onMounted(async () => {
  if (props.company) {
    await comStore.fetchCompanySealList(props.company)
  }
  if (!props.letter && props.company) {
    // Get next document number for new letters
    nextDocNumber.value = await docStore.getNextDocumentNumber(props.company)
  }
})

const onSubmit = () => {
  validated.value = true

  // Validate required fields
  if (
    !form.value.title ||
    !form.value.recipient_name ||
    !form.value.sender_name ||
    !form.value.content ||
    !form.value.issue_date
  ) {
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
      <!-- 1. 공문서 서식 영역 (PDF 템플릿과 동일 순서) -->
      <CCard class="mb-4 border-primary">
        <CCardHeader class="bg-primary text-white d-flex align-items-center">
          <CIcon name="cilDescription" class="me-2" />
          <strong>공문서 서식 (PDF 인쇄 영역)</strong>
        </CCardHeader>
        <CCardBody>
          <!-- 수신 / (경유) / 참조 / 제목 (상단 4행 고정 서식) -->
          <div class="p-3 bg-light rounded mb-4 border">
            <h6 class="text-primary mb-3">
              <CIcon name="cilAddressBook" class="me-1" />
              수신 및 제목 정보
            </h6>
            <CRow class="mb-3">
              <CCol md="6">
                <CFormLabel> 수신 <span class="text-danger">*</span></CFormLabel>
                <CFormInput
                  v-model="form.recipient_name"
                  placeholder="수신처 명칭 (예: OO주식회사, 구청장 등)"
                  required
                  :invalid="validated && !form.recipient_name"
                />
                <CFormFeedback invalid>수신처명을 입력해주세요.</CFormFeedback>
              </CCol>
              <CCol md="6">
                <CFormLabel>(경유)</CFormLabel>
                <CFormInput
                  v-model="form.via"
                  placeholder="경유 기관 또는 부서 (없을 시 빈칸)"
                />
              </CCol>
            </CRow>
            <CRow class="mb-3">
              <CCol md="6">
                <CFormLabel>참조</CFormLabel>
                <CFormInput
                  v-model="form.recipient_reference"
                  placeholder="참조 부서 또는 직위 (예: 대표이사 귀하)"
                />
              </CCol>
              <CCol md="6">
                <CFormLabel>시행(발신) 일자 <span class="text-danger">*</span></CFormLabel>
                <DatePicker v-model="form.issue_date" placeholder="시행일자 선택" required />
              </CCol>
            </CRow>
            <CRow>
              <CCol md="12">
                <CFormLabel> 제목 <span class="text-danger">*</span></CFormLabel>
                <CFormInput
                  v-model="form.title"
                  placeholder="공문 제목을 입력하세요"
                  required
                  :invalid="validated && !form.title"
                />
                <CFormFeedback invalid>제목을 입력해주세요.</CFormFeedback>
              </CCol>
            </CRow>
          </div>

          <!-- 본문 내용 -->
          <div class="mb-4">
            <CFormLabel class="fw-bold">
              본문 내용 <span class="text-danger">*</span>
            </CFormLabel>
            <CFormTextarea
              v-model="form.content"
              placeholder="공문 본문 내용을 입력하세요"
              rows="12"
              required
              :invalid="validated && !form.content"
            />
            <CFormFeedback invalid>공문 본문 내용을 입력해주세요.</CFormFeedback>
            <CFormText class="text-muted">
              줄 바꿈은 인쇄 시 그대로 반영됩니다. 문단을 구분하려면 빈 줄을 추가하세요.
            </CFormText>
          </div>

          <!-- 붙임(첨부) 목록 -->
          <div class="mb-4 p-3 bg-light rounded border">
            <CFormLabel class="fw-bold mb-1">
              붙임 (첨부 서류 목록)
            </CFormLabel>
            <CFormText class="text-muted d-block mb-2">
              공문서 본문 하단에 인쇄될 붙임 서류 목록을 기재합니다. (예: 1. 사업계획서 1부.)
            </CFormText>
            <CFormTextarea
              v-model="form.attachment_text"
              placeholder="1. 관련 서류 1부.&#10;2. 사업계획서 1부. 끝."
              rows="3"
            />
          </div>

          <!-- 발신 명의, 날인 및 기안자 정보 -->
          <div class="p-3 bg-light rounded border">
            <h6 class="text-primary mb-3">
              <CIcon name="cilPen" class="me-1" />
              발신 명의, 직인 날인 및 기안 정보
            </h6>
            <CRow class="mb-3">
              <CCol md="6">
                <CFormLabel>날인 인감 (직인)</CFormLabel>
                <CFormSelect
                  :value="form.seal || ''"
                  @change="form.seal = Number(($event.target as HTMLSelectElement).value) || null"
                >
                  <option value="">인장 미선택 / (직인생략)</option>
                  <option v-for="s in sealList" :key="s.pk" :value="s.pk">
                    {{ s.name }} ({{ s.seal_type_desc || s.seal_type }})
                  </option>
                </CFormSelect>
                <div v-if="selectedSealImage" class="mt-2 d-flex align-items-center">
                  <img
                    :src="selectedSealImage"
                    alt="인장"
                    style="width: 40px; height: 40px; object-fit: contain"
                    class="border rounded p-1 bg-white me-2"
                  />
                  <small class="text-muted">등록된 직인 이미지 (PDF 자동 날인)</small>
                </div>
              </CCol>
              <CCol md="6">
                <CFormLabel>기안/담당자명 <span class="text-danger">*</span></CFormLabel>
                <CFormInput
                  v-model="form.sender_name"
                  placeholder="기안/담당자명 (예: 홍길동)"
                  required
                  :invalid="validated && !form.sender_name"
                />
                <CFormFeedback invalid>기안/담당자명을 입력해주세요.</CFormFeedback>
                <CFormText class="text-muted">전자결재 미연동 수동 발송 시 하단 결재/담당란에 표기됩니다.</CFormText>
              </CCol>
            </CRow>
            <CRow class="mb-3">
              <CCol md="6">
                <CFormLabel>담당 직위/직책</CFormLabel>
                <CFormInput v-model="form.sender_position" placeholder="직위 (예: 과장, 팀장)" />
              </CCol>
              <CCol md="6">
                <CFormLabel>담당 부서</CFormLabel>
                <CFormInput v-model="form.sender_department" placeholder="부서 (예: 개발기획팀)" />
              </CCol>
            </CRow>
            <CRow>
              <CCol md="4">
                <CFormLabel>발신 우편번호 (현장/지사)</CFormLabel>
                <CFormInput
                  v-model="form.sender_zipcode"
                  placeholder="예: 12345"
                />
              </CCol>
              <CCol md="8">
                <CFormLabel>발신 도로명 주소 (현장/지사)</CFormLabel>
                <CFormInput
                  v-model="form.sender_address"
                  placeholder="특정 현장/지사 주소 발송 시 입력 (비워두면 본사 기본주소 자동 적용)"
                />
                <CFormText class="text-muted">비워두면 본사 기본 주소가 인쇄됩니다.</CFormText>
              </CCol>
            </CRow>
          </div>
        </CCardBody>
      </CCard>

      <!-- 2. 발송 및 대장 관리 메타 영역 (공문서에는 인쇄되지 않는 업무 관리 데이터) -->
      <CCard class="mb-4">
        <CCardHeader class="bg-secondary text-white d-flex align-items-center">
          <CIcon name="cilFolderOpen" class="me-2" />
          <strong>발송 및 대장 관리 정보 (시스템 관리용 메타데이터)</strong>
        </CCardHeader>
        <CCardBody>
          <CAlert color="info" class="py-2 mb-3">
            <small>
              <CIcon name="cilInfo" class="me-1" />
              아래 정보는 공문서 본문에는 인쇄되지 않으며, 우편 라벨 출력, 등기번호 추적 및 발송 대장 이력 관리에 사용됩니다.
            </small>
          </CAlert>

          <CRow class="mb-3">
            <CCol md="6">
              <CFormLabel>수신처 주소 (우편/등기 발송지)</CFormLabel>
              <CFormInput
                v-model="form.recipient_address"
                placeholder="우편 발송지 주소 (봉투 라벨 인쇄용)"
              />
            </CCol>
            <CCol md="6">
              <CFormLabel>수신처 연락처/담당자</CFormLabel>
              <CFormInput
                v-model="form.recipient_contact"
                placeholder="수신처 담당자 전화번호, 휴대폰 등"
              />
            </CCol>
          </CRow>

          <CRow class="mb-2">
            <CCol md="4">
              <CFormLabel>발송 방법</CFormLabel>
              <CFormSelect v-model="form.dispatch_method">
                <option value="email">이메일</option>
                <option value="registered_mail">등기우편</option>
                <option value="direct">인편/직접교부</option>
                <option value="courier">퀵/택배</option>
                <option value="fax">팩스</option>
                <option value="etc">기타</option>
              </CFormSelect>
            </CCol>
            <CCol md="4">
              <CFormLabel>등기 / 송장 번호</CFormLabel>
              <CFormInput
                v-model="form.tracking_number"
                placeholder="13자리 등기번호 또는 택배 송장번호"
              />
            </CCol>
            <CCol md="4">
              <CFormLabel>발송 완료일자</CFormLabel>
              <DatePicker
                :model-value="form.dispatched_at ? form.dispatched_at.substring(0, 10) : ''"
                placeholder="실제 발송 완료일"
                @update:model-value="form.dispatched_at = $event ? `${$event}T00:00:00` : null"
              />
            </CCol>
          </CRow>
        </CCardBody>
      </CCard>

      <!-- Actions -->
      <CRow>
        <CCol class="d-flex justify-content-between">
          <CButton color="secondary" variant="outline" @click="goBack">
            <CIcon name="cilArrowLeft" class="me-1" />
            취소
          </CButton>
          <CButton
            type="submit"
            :color="isEdit ? 'success' : 'primary'"
            :disabled="!accStore.isStaff && canOLManage"
          >
            <CIcon name="cilSave" class="me-1" />
            {{ isEdit ? '수정 저장' : '공문 저장' }}
          </CButton>
        </CCol>
      </CRow>
    </CForm>
  </div>
</template>

