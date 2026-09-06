<script lang="ts" setup>
import { ref, reactive, computed } from 'vue'
import { useSales } from '@/store/pinia/sales'
import type { SalesPerson, SalesDuty, SalesPersonStatus, TaxType } from '@/store/types/sales'
import FormModal from '@/components/Modals/FormModal.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'

const props = defineProps({
  defaultTeamId: { type: Number, default: null },
})

const emit = defineEmits(['saved', 'open-docs'])

const salesStore = useSales()
const modalRef = ref()
const isEdit = ref(false)
const targetId = ref<number | null>(null)

const currentPerson = computed(() => {
  if (!targetId.value) return null
  return salesStore.personList.find(p => p.id === targetId.value) || null
})

const teamList = computed(() => salesStore.teamList)

const bankOptions = [
  '국민은행', '신한은행', '우리은행', '하나은행', '농협은행',
  '기업은행', '카카오뱅크', '토스뱅크', 'SC제일은행', '대구은행',
  '부산은행', '광주은행', '경남은행', '전북은행', '제주은행',
  '우체국', '새마을금고', '신협', '수협은행', '케이뱅크'
]

const form = reactive({
  team: null as number | null,
  name: '',
  duty: '1' as SalesDuty,
  status: '1' as SalesPersonStatus,
  phone: '',
  id_number: '',
  tax_type: '1' as TaxType,
  bank_name: '',
  account_number: '',
  account_holder: '',
  join_date: '',
  quit_date: '',
  notes: '',
})

const resetForm = () => {
  form.team = props.defaultTeamId || (teamList.value[0]?.id ?? null)
  form.name = ''
  form.duty = '1'
  form.status = '1'
  form.phone = ''
  form.id_number = ''
  form.tax_type = '1'
  form.bank_name = '국민은행'
  form.account_number = ''
  form.account_holder = ''
  form.join_date = ''
  form.quit_date = ''
  form.notes = ''
  targetId.value = null
  isEdit.value = false
}

const open = (person?: SalesPerson, teamId?: number) => {
  resetForm()
  if (teamId) form.team = teamId
  if (person) {
    isEdit.value = true
    targetId.value = person.id
    form.team = person.team
    form.name = person.name
    form.duty = person.duty
    form.status = person.status
    form.phone = person.phone
    form.id_number = person.id_number
    form.tax_type = person.tax_type
    form.bank_name = person.bank_name || '국민은행'
    form.account_number = person.account_number
    form.account_holder = person.account_holder
    form.join_date = person.join_date || ''
    form.quit_date = person.quit_date || ''
    form.notes = person.notes
  }
  modalRef.value.callModal()
}

const submit = async () => {
  if (!form.team) {
    alert('소속 팀을 선택해주세요.')
    return
  }
  if (!form.name.trim()) {
    alert('성명을 입력해주세요.')
    return
  }
  if (!form.phone.trim()) {
    alert('연락처를 입력해주세요.')
    return
  }

  const payload: Partial<SalesPerson> = {
    team: form.team,
    name: form.name.trim(),
    duty: form.duty,
    status: form.status,
    phone: form.phone.trim(),
    id_number: form.id_number.trim(),
    tax_type: form.tax_type,
    bank_name: form.bank_name,
    account_number: form.account_number.trim(),
    account_holder: form.account_holder.trim() || form.name.trim(),
    join_date: form.join_date || null,
    quit_date: form.quit_date || null,
    notes: form.notes.trim(),
  }

  if (isEdit.value && targetId.value) {
    await salesStore.updatePerson(targetId.value, payload)
  } else {
    await salesStore.createPerson(payload)
  }
  modalRef.value.close()
  emit('saved')
}

defineExpose({ open })
</script>

<template>
  <FormModal ref="modalRef" size="lg">
    <template #header>{{ isEdit ? '영업 인력 정보 수정' : '신규 영업 인력 등록' }}</template>
    <template #default>
      <CModalBody>
        <CRow class="g-3">
          <!-- 기본 인적사항 -->
          <CCol md="4">
            <CFormLabel>소속 팀 <span class="text-danger">*</span></CFormLabel>
            <CFormSelect v-model.number="form.team" required>
              <option :value="null">소속 팀을 선택하세요</option>
              <option v-for="t in teamList" :key="t.id" :value="t.id">
                {{ t.agency_name ? `[${t.agency_name}] ` : '' }}{{ t.parent_name ? `${t.parent_name} > ` : '' }}{{ t.name }}
              </option>
            </CFormSelect>
          </CCol>

          <CCol md="4">
            <CFormLabel>성명 <span class="text-danger">*</span></CFormLabel>
            <CFormInput v-model="form.name" placeholder="홍길동" required />
          </CCol>

          <CCol md="4">
            <CFormLabel>직책 <span class="text-danger">*</span></CFormLabel>
            <CFormSelect v-model="form.duty">
              <option value="1">분양상담사</option>
              <option value="2">팀장</option>
              <option value="3">본부장</option>
              <option value="4">총괄본부장</option>
              <option value="5">지원/기타</option>
            </CFormSelect>
          </CCol>

          <CCol md="4">
            <CFormLabel>연락처 <span class="text-danger">*</span></CFormLabel>
            <CFormInput v-model="form.phone" placeholder="010-0000-0000" required />
          </CCol>

          <CCol md="4">
            <CFormLabel>주민등록번호 (원천세용)</CFormLabel>
            <CFormInput v-model="form.id_number" placeholder="주민번호(식별용)" />
          </CCol>

          <CCol md="4">
            <CFormLabel>소득 구분 <span class="text-danger">*</span></CFormLabel>
            <CFormSelect v-model="form.tax_type">
              <option value="1">3.3% 사업소득 (프리랜서)</option>
              <option value="2">근로소득</option>
              <option value="3">사업자 (세금계산서)</option>
              <option value="4">기타</option>
            </CFormSelect>
          </CCol>

          <!-- 계좌 정보 -->
          <CCol md="12" class="pt-2">
            <div class="border-bottom pb-1 text-primary fw-bold">
              <v-icon icon="mdi-bank" size="small" class="mr-1" /> 정산 계좌 정보
            </div>
          </CCol>

          <CCol md="4">
            <CFormLabel>정산 은행</CFormLabel>
            <CFormSelect v-model="form.bank_name">
              <option v-for="b in bankOptions" :key="b" :value="b">{{ b }}</option>
            </CFormSelect>
          </CCol>

          <CCol md="5">
            <CFormLabel>계좌번호</CFormLabel>
            <CFormInput v-model="form.account_number" placeholder="'-' 제외 숫자만 입력" />
          </CCol>

          <CCol md="3">
            <CFormLabel>예금주</CFormLabel>
            <CFormInput v-model="form.account_holder" :placeholder="form.name || '예금주명'" />
          </CCol>

          <!-- 재직 및 일정 -->
          <CCol md="12" class="pt-2">
            <div class="border-bottom pb-1 text-primary fw-bold">
              <v-icon icon="mdi-calendar-check" size="small" class="mr-1" /> 활동 및 재직 정보
            </div>
          </CCol>

          <CCol md="4">
            <CFormLabel>재직 상태</CFormLabel>
            <CFormSelect v-model="form.status">
              <option value="1">재직 (활동 중)</option>
              <option value="2">휴직</option>
              <option value="3">해촉 (퇴사)</option>
            </CFormSelect>
          </CCol>

          <CCol md="4">
            <CFormLabel>위촉/입사일</CFormLabel>
            <DatePicker v-model="form.join_date" placeholder="위촉/입사일" />
          </CCol>

          <CCol md="4">
            <CFormLabel>해촉/퇴사일</CFormLabel>
            <DatePicker v-model="form.quit_date" placeholder="해촉/퇴사일" />
          </CCol>

          <!-- 증빙 서류 정보 안내 (수정 모드) -->
          <CCol v-if="isEdit && currentPerson" md="12" class="pt-2">
            <div class="border-bottom pb-1 text-primary fw-bold d-flex justify-content-between align-items-center">
              <div>
                <v-icon icon="mdi-file-document-multiple-outline" size="small" class="mr-1" />
                증빙 서류 현황
              </div>
              <v-btn
                color="primary"
                size="x-small"
                variant="tonal"
                @click="emit('open-docs', currentPerson)"
              >
                <v-icon icon="mdi-paperclip" size="x-small" class="mr-1" />
                서류 접수 및 관리 ({{ currentPerson.documents_count ?? 0 }}건)
              </v-btn>
            </div>
            <div class="small text-muted mt-2">
              주민등록등본, 통장 사본, 신분증, 영업 위촉계약서, 보안서약서 등 접수된 증빙 서류를 확인하고 관리합니다.
            </div>
          </CCol>

          <CCol md="12">
            <CFormLabel>비고 / 특이사항</CFormLabel>
            <CFormTextarea v-model="form.notes" rows="2" placeholder="경력 사항, 추천인, 메모 등" />
          </CCol>
        </CRow>
      </CModalBody>
      <CModalFooter class="d-flex justify-content-between">
        <div>
          <v-btn
            v-if="isEdit && currentPerson"
            color="info"
            variant="tonal"
            size="small"
            @click="emit('open-docs', currentPerson)"
          >
            <v-icon icon="mdi-file-document-multiple-outline" size="small" class="mr-1" />
            증빙 서류 관리 ({{ currentPerson.documents_count ?? 0 }}건)
          </v-btn>
        </div>
        <div>
          <v-btn color="primary" size="small" class="me-2" @click="submit">
            {{ isEdit ? '수정 저장' : '등록하기' }}
          </v-btn>
          <v-btn color="light" size="small" flat @click="modalRef.close()">취소</v-btn>
        </div>
      </CModalFooter>
    </template>
  </FormModal>
</template>
