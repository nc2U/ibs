<script lang="ts" setup>
import { reactive, ref } from 'vue'
import type { SuitCase } from '@/store/types/docs'
import { btnLight } from '@/utils/cssMixins.ts'
import { courtChoices } from '@/components/LawSuitCase/components/court'
import DatePicker from '@/components/DatePicker/index.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({ getSuitCase: { type: Object, default: null } })

const refConfirmModal = ref()
const refCaseForm = ref()
const callModal = () => refCaseForm.value.callModal()

const validated = ref(false)
const form = ref<SuitCase>({
  pk: null,
  issue_project: null, // Todo 데이터 생성 시 업무 프로젝트 주입하기
  sort: '',
  level: '',
  related_case: null,
  court: '',
  other_agency: '',
  case_number: '',
  case_name: '',
  plaintiff: '',
  plaintiff_attorney: '',
  plaintiff_case_price: null,
  defendant: '',
  defendant_attorney: '',
  defendant_case_price: null,
  related_debtor: '',
  case_start_date: null,
  case_end_date: null,
  summary: '',
})

defineExpose({ callModal })

const emit = defineEmits(['on-submit'])

const onSubmit = (event: Event) => {
  const el = event.currentTarget as HTMLFormElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()

    validated.value = true
  } else refConfirmModal.value.callModal()
}

const modalAction = () => {
  emit('on-submit', { ...form.value })
  validated.value = false
  refConfirmModal.value.close()
}
</script>

<template>
  <FormModal ref="refCaseForm" :size="'lg'">
    <template #header>새 소송사건 생성</template>
    <template #default>
      <CModalBody class="text-body px-4">
        <CForm
          enctype="multipart/form-data"
          class="needs-validation"
          novalidate
          :validated="validated"
          @submit.prevent="onSubmit"
        >
          <CRow class="mb-3">
            <CFormLabel for="sort" class="col-md-2 col-form-label">유형</CFormLabel>
            <CCol md="4">
              <CFormSelect id="sort" v-model="form.sort" required>
                <option value="">사건유형 선택</option>
                <option value="1">민사</option>
                <option value="2">형사</option>
                <option value="3">행정</option>
                <option value="4">신청</option>
                <option value="5">집행</option>
              </CFormSelect>
            </CCol>

            <CFormLabel for="level" class="col-md-2 col-form-label">심급</CFormLabel>
            <CCol md="4">
              <CFormSelect id="level" v-model="form.level" required>
                <option value="">사건심급 선택</option>
                <option v-if="!form.sort || form.sort <= '3'" value="1">1심</option>
                <option v-if="!form.sort || form.sort <= '3'" value="2">2심</option>
                <option v-if="!form.sort || form.sort <= '3'" value="3">3심</option>
                <option v-if="!form.sort || form.sort === '2'" value="4">고소/수사</option>
                <option v-if="!form.sort || form.sort === '4'" value="5">신청</option>
                <option v-if="!form.sort || form.sort === '4'" value="6">항고/이의</option>
                <option v-if="!form.sort || form.sort === '5'" value="7">압류/추심</option>
                <option v-if="!form.sort || form.sort === '5'" value="8">정지/이의</option>
              </CFormSelect>
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="related_case" class="col-md-2 col-form-label"> 관련사건</CFormLabel>
            <CCol md="4">
              <MultiSelect
                v-model="form.related_case"
                mode="single"
                :options="getSuitCase"
                placeholder="관련 사건"
              />
              <small class="text-blue-grey-lighten-2">
                본안 사건인 경우 원심(1심) 사건, 신청/집행 사건인 경우 관련 본안 사건 지정
              </small>
            </CCol>
            <CFormLabel for="related_debtor" class="col-md-2 col-form-label"> 제3채무자</CFormLabel>
            <CCol md="4">
              <CFormInput
                id="related_debtor"
                v-model="form.related_debtor"
                maxlength="30"
                placeholder="제3채무자"
              />
              <small class="text-blue-grey-lighten-2">
                압류/가압류 등 집행(압류/추심) 사건에서 제3채무자가 있는 경우 기재
              </small>
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="related_case" class="col-md-2 col-form-label"> 법원명</CFormLabel>
            <CCol md="4">
              <MultiSelect
                v-model="form.court"
                mode="single"
                :options="courtChoices"
                placeholder="법원 선택"
                :attrs="form.court || form.other_agency ? {} : { required: true }"
              />
            </CCol>

            <CFormLabel for="other_agency" class="col-md-2 col-form-label">
              기타 처리기관
            </CFormLabel>
            <CCol md="4">
              <CFormInput
                id="other_agency"
                v-model="form.other_agency"
                maxlength="30"
                placeholder="법원 외 사건 처리기관"
              />
              <small class="text-blue-grey-lighten-2">
                사건 유형이 기소 전 형사 사건인 경우 해당 수사기관을 기재
              </small>
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="case_number" class="col-md-2 col-form-label"> 사건번호</CFormLabel>
            <CCol md="4">
              <CFormInput
                id="case_number"
                v-model="form.case_number"
                maxlength="20"
                placeholder="사건번호"
                required
              />
            </CCol>

            <CFormLabel for="case_name" class="col-md-2 col-form-label"> 사건명</CFormLabel>
            <CCol md="4">
              <CFormInput
                id="case_name"
                v-model="form.case_name"
                maxlength="30"
                placeholder="사건명"
                required
              />
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="plaintiff" class="col-md-2 col-form-label"> 원고(채권자)</CFormLabel>
            <CCol md="4">
              <CFormInput
                id="plaintiff"
                v-model="form.plaintiff"
                maxlength="30"
                placeholder="원고(채권자)"
                required
              />
            </CCol>

            <CFormLabel for="defendant" class="col-md-2 col-form-label"> 피고(채무자)</CFormLabel>
            <CCol md="4">
              <CFormInput
                id="defendant"
                v-model="form.defendant"
                maxlength="30"
                placeholder="피고(채무자)"
                required
              />
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="plaintiff_attorney" class="col-md-2 col-form-label">
              원고측 대리인
            </CFormLabel>
            <CCol md="4">
              <CFormInput
                id="plaintiff_attorney"
                v-model="form.plaintiff_attorney"
                maxlength="50"
                placeholder="원고측 대리인"
              />
            </CCol>

            <CFormLabel for="defendant_attorney" class="col-md-2 col-form-label">
              피고측 대리인
            </CFormLabel>
            <CCol md="4">
              <CFormInput
                id="defendant_attorney"
                v-model="form.defendant_attorney"
                maxlength="50"
                placeholder="피고측 대리인"
              />
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="plaintiff_attorney" class="col-md-2 col-form-label">
              원고 소가
            </CFormLabel>
            <CCol md="4">
              <CFormInput
                id="plaintiff_case_price"
                v-model.number="form.plaintiff_case_price"
                type="number"
                min="0"
                placeholder="원고 소가"
              />
            </CCol>

            <CFormLabel for="defendant_attorney" class="col-md-2 col-form-label">
              피고 소가
            </CFormLabel>
            <CCol md="4">
              <CFormInput
                id="defendant_case_price"
                v-model.number="form.defendant_case_price"
                type="number"
                min="0"
                placeholder="피고 소가"
              />
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="case_start_date" class="col-md-2 col-form-label">
              사건개시일
            </CFormLabel>
            <CCol md="4">
              <DatePicker
                id="case_start_date"
                v-model="form.case_start_date"
                placeholder="사건개시일"
                required
              />
            </CCol>

            <CFormLabel for="case_end_date" class="col-md-2 col-form-label"> 사건종결일</CFormLabel>
            <CCol md="4">
              <DatePicker
                id="case_end_date"
                v-model="form.case_end_date"
                placeholder="사건종결일"
              />
            </CCol>
          </CRow>

          <CRow class="mb-3">
            <CFormLabel for="summary" class="col-md-2 col-form-label"> 개요 및 경과</CFormLabel>
            <CCol>
              <CFormTextarea
                id="summary"
                v-model="form.summary"
                rows="4"
                placeholder="개요 및 경과"
              />
            </CCol>
          </CRow>

          <CRow>
            <CCol class="text-right">
              <v-btn :color="btnLight" size="small" @click="refCaseForm.close()"> 닫기</v-btn>
              <v-btn color="primary" type="submit" size="small"> 저장하기</v-btn>
            </CCol>
          </CRow>
        </CForm>
      </CModalBody>
    </template>
  </FormModal>

  <ConfirmModal ref="refConfirmModal">
    <template #header>소송사건</template>
    <template #default> 소송사건 저장을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="success" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>
</template>
