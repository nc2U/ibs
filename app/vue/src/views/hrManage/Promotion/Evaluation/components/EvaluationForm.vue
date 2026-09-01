<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, type PropType } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type StaffEvaluation, type EvaluationGrade, type EvaluationPeriod } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  evaluation: { type: Object as PropType<StaffEvaluation>, default: null },
})

const emit = defineEmits(['multi-submit', 'on-delete', 'close'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_UPDATE))
const canHrWorkDelete = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_DELETE))

const comStore = useCompany()
const allStaffList = computed(() => comStore.allStaffList)

const getPkStaffs = computed(() =>
  allStaffList.value.map(s => ({
    value: s.pk as number,
    label: `${s.name} (${s.department || '부서없음'} / ${s.position || '직위없음'})`,
  })),
)

const currentYear = new Date().getFullYear()
const years = Array.from({ length: 6 }, (_, i) => ({
  value: currentYear - 3 + i,
  label: `${currentYear - 3 + i}년`,
}))

const periodOptions = [
  { value: 'yearly', label: '연간' },
  { value: '1H', label: '상반기' },
  { value: '2H', label: '하반기' },
]

const gradeOptions = [
  { value: 'S', label: 'S (탁월, 95~100점)' },
  { value: 'A', label: 'A (우수, 85~94점)' },
  { value: 'B', label: 'B (보통, 75~84점)' },
  { value: 'C', label: 'C (미흡, 65~74점)' },
  { value: 'D', label: 'D (불량, 64점 이하)' },
]

const refDelModal = ref()
const refAlertModal = ref()
const validated = ref(false)

const form = ref<StaffEvaluation>({
  pk: undefined,
  company: undefined,
  staff: null as any,
  eval_year: currentYear,
  eval_period: 'yearly',
  grade: 'B',
  score: null,
  achievement_summary: '',
  evaluator: null,
  reviewer: null,
  notes: '',
})

const formsCheck = computed(() => {
  if (props.evaluation) {
    const a = form.value.pk === props.evaluation.pk
    const b = form.value.staff === props.evaluation.staff
    const c = form.value.eval_year === props.evaluation.eval_year
    const d = form.value.eval_period === props.evaluation.eval_period
    const e = form.value.grade === props.evaluation.grade
    const f = Number(form.value.score) === Number(props.evaluation.score)
    const g = form.value.achievement_summary === props.evaluation.achievement_summary
    const h = form.value.evaluator === props.evaluation.evaluator
    const i = form.value.reviewer === props.evaluation.reviewer
    const j = form.value.notes === props.evaluation.notes

    return a && b && c && d && e && f && g && h && i && j
  } else return false
})

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (canHrWorkCreate.value || canHrWorkUpdate.value) multiSubmit({ ...form.value })
    else refAlertModal.value.callModal()
  }
}

const multiSubmit = (payload: StaffEvaluation) => {
  emit('multi-submit', payload)
  emit('close')
}

const deleteObject = (pk: number) => {
  emit('on-delete', pk)
  refDelModal.value.close()
  emit('close')
}

const deleteConfirm = () => {
  if (canHrWorkDelete.value) refDelModal.value.callModal()
  else refAlertModal.value.callModal()
}

const formDataSetup = () => {
  if (props.evaluation) {
    form.value.pk = props.evaluation.pk
    form.value.company = props.evaluation.company
    form.value.staff = props.evaluation.staff
    form.value.eval_year = props.evaluation.eval_year
    form.value.eval_period = props.evaluation.eval_period
    form.value.grade = props.evaluation.grade
    form.value.score = props.evaluation.score !== null && props.evaluation.score !== undefined ? Number(props.evaluation.score) : null
    form.value.achievement_summary = props.evaluation.achievement_summary || ''
    form.value.evaluator = props.evaluation.evaluator || null
    form.value.reviewer = props.evaluation.reviewer || null
    form.value.notes = props.evaluation.notes || ''
  } else form.value.company = props.company
}

onBeforeMount(() => formDataSetup())

watch(
  () => props.company,
  newVal => {
    if (!!newVal) form.value.company = newVal
    else form.value.company = undefined
  },
)
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <div>
        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">피평가자</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.staff"
                  :options="getPkStaffs"
                  :disabled="!!evaluation"
                  required
                  searchable
                  placeholder="대상 직원 선택"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">평가 연도</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.eval_year"
                  :options="years"
                  :disabled="!!evaluation"
                  required
                  placeholder="평가 연도"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">평가 주기</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.eval_period"
                  :options="periodOptions"
                  :disabled="!!evaluation"
                  required
                  placeholder="평가 주기 선택"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">평가 등급</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.grade"
                  :options="gradeOptions"
                  required
                  placeholder="평가 등급 선택"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="4">
            <CRow>
              <CFormLabel class="col-sm-5 col-form-label">환산 점수</CFormLabel>
              <CCol sm="7">
                <CFormInput
                  v-model.number="form.score"
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  placeholder="100점 만점"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="4">
            <CRow>
              <CFormLabel class="col-sm-5 col-form-label">1차 평가자</CFormLabel>
              <CCol sm="7">
                <Multiselect
                  v-model="form.evaluator"
                  :options="getPkStaffs"
                  searchable
                  placeholder="1차 평가자"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="4">
            <CRow>
              <CFormLabel class="col-sm-5 col-form-label">2차 확인자</CFormLabel>
              <CCol sm="7">
                <Multiselect
                  v-model="form.reviewer"
                  :options="getPkStaffs"
                  searchable
                  placeholder="2차 확인자"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">주요 업적</CFormLabel>
              <CCol sm="10">
                <CFormTextarea
                  v-model="form.achievement_summary"
                  rows="3"
                  placeholder="해당 평가 기간 주요 업무 수행 실적 및 핵심 성과 요약"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">종합 의견</CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model="form.notes"
                  placeholder="평가자 종합 코멘트 및 승진/보상 참고 의견"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </div>
    </CModalBody>

    <CModalFooter>
      <slot name="footer">
        <v-btn
          type="submit"
          size="small"
          :color="evaluation ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="evaluation" type="button" size="small" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
        <v-btn type="button" size="small" color="light" @click="$emit('close')" flat> 닫기</v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>인사 평가 기록 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 인사 평가 기록을 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject(evaluation.pk as number)">
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
