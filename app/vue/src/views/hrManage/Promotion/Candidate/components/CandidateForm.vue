<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type PromotionCandidate, type PromotionStatus } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps<{
  company?: string | null
  candidate?: PromotionCandidate | null
}>()

const emit = defineEmits<{
  (e: 'multi-submit', payload: PromotionCandidate, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
  (e: 'close'): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => canGlobal(PERM.HQ_HR_WORK_UPDATE))
const canSubmit = computed(() =>
  props.candidate ? canHrWorkUpdate.value : canHrWorkCreate.value,
)
const canHrWorkDelete = computed(() => canGlobal(PERM.HQ_HR_WORK_DELETE))

const comStore = useCompany()
const allStaffList = computed(() => comStore.allStaffList)
const allPromotionPolicyList = computed(() => comStore.allPromotionPolicyList)

const getPkStaffs = computed(() =>
  allStaffList.value.map(s => ({
    value: s.pk as number,
    label: `${s.name} (${s.department || '부서없음'} / ${s.position || s.grade || '직급없음'})`,
  })),
)

const policyOptions = computed(() =>
  allPromotionPolicyList.value.map(p => ({
    value: p.pk as number,
    label: `[${p.current_grade_code} → ${p.target_grade_code}] (최소 ${p.min_years}년)`,
  })),
)

const currentYear = new Date().getFullYear()
const years = Array.from({ length: 6 }, (_, i) => ({
  value: currentYear - 3 + i,
  label: `${currentYear - 3 + i}년`,
}))

const statusOptions = [
  { value: 'candidate', label: '심사 대상' },
  { value: 'recommended', label: '부서 추천' },
  { value: 'approved', label: '승진 확정' },
  { value: 'rejected', label: '심사 탈락' },
  { value: 'hold', label: '심사 보류' },
]

const refDelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)
const validated = ref(false)
const submitting = ref(false)

const normalizeNum = (v: number | string | null | undefined) =>
  v === '' || v === null || v === undefined ? null : Number(v)

const getLocalToday = () => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

type CandidateFormState = Omit<PromotionCandidate, 'staff' | 'policy'> & {
  staff: number | null
  policy: number | null
}

const form = ref<CandidateFormState>({
  pk: undefined,
  company: undefined,
  policy: null,
  staff: null,
  eval_year: currentYear,
  tenure_years: 0,
  avg_eval_score: null,
  status: 'candidate',
  committee_review: '',
  promoted_date: null,
})

const onStatusChange = (newStatus: PromotionStatus) => {
  if (newStatus === 'approved' && !form.value.promoted_date) {
    form.value.promoted_date = getLocalToday()
  } else if (newStatus !== 'approved') {
    form.value.promoted_date = null
  }
}

const formsCheck = computed(() => {
  if (props.candidate) {
    const a = form.value.pk === props.candidate.pk
    const b = (form.value.policy ?? null) === (props.candidate.policy ?? null)
    const c = (form.value.staff ?? null) === (props.candidate.staff ?? null)
    const d = form.value.eval_year === props.candidate.eval_year
    const e = Number(form.value.tenure_years) === Number(props.candidate.tenure_years)
    const f =
      normalizeNum(form.value.avg_eval_score) === normalizeNum(props.candidate.avg_eval_score)
    const g = form.value.status === props.candidate.status
    const h = (form.value.committee_review ?? '') === (props.candidate.committee_review ?? '')
    const i = (form.value.promoted_date ?? null) === (props.candidate.promoted_date ?? null)

    return a && b && c && d && e && f && g && h && i
  } else return false
})

const onSubmit = (event: Event) => {
  if (
    isValidate(event) ||
    !form.value.eval_year ||
    form.value.staff === null ||
    form.value.policy === null ||
    !form.value.status
  ) {
    validated.value = true
  } else {
    if (canSubmit.value) {
      multiSubmit({
        ...form.value,
        staff: form.value.staff,
        policy: form.value.policy,
        avg_eval_score: normalizeNum(form.value.avg_eval_score),
      })
    } else refAlertModal.value?.callModal()
  }
}

const multiSubmit = (payload: PromotionCandidate) => {
  submitting.value = true
  emit('multi-submit', payload, ok => {
    submitting.value = false
    if (ok) emit('close')
  })
}

const deleteObject = (pk: number) => {
  submitting.value = true
  emit('on-delete', pk, ok => {
    submitting.value = false
    refDelModal.value?.close()
    if (ok) emit('close')
  })
}

const deleteConfirm = () => {
  if (canHrWorkDelete.value) refDelModal.value?.callModal()
  else refAlertModal.value?.callModal()
}

const formDataSetup = () => {
  if (props.candidate) {
    form.value.pk = props.candidate.pk
    form.value.company = props.candidate.company
    form.value.policy = props.candidate.policy
    form.value.staff = props.candidate.staff
    form.value.eval_year = props.candidate.eval_year
    form.value.tenure_years = Number(props.candidate.tenure_years || 0)
    form.value.avg_eval_score =
      props.candidate.avg_eval_score !== null && props.candidate.avg_eval_score !== undefined
        ? Number(props.candidate.avg_eval_score)
        : null
    form.value.status = props.candidate.status
    form.value.committee_review = props.candidate.committee_review || ''
    form.value.promoted_date = props.candidate.promoted_date || null
  } else form.value.company = props.company || undefined
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
              <CFormLabel class="col-sm-4 col-form-label required">심사 연도</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.eval_year"
                  :options="years"
                  :disabled="!!candidate"
                  required
                  placeholder="심사 연도 선택"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">대상 직원</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.staff"
                  :options="getPkStaffs"
                  :disabled="!!candidate"
                  required
                  searchable
                  placeholder="승급 대상 직원 선택"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required">승급 정책</CFormLabel>
              <CCol sm="10">
                <Multiselect
                  v-model="form.policy"
                  :options="policyOptions"
                  required
                  placeholder="적용 승급 정책 선택 (현재직급 → 승급대상직급)"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">체류 년수</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.tenure_years"
                  type="number"
                  step="0.5"
                  min="0"
                  required
                  placeholder="현 직급 체류 년수 (년)"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">평가 점수</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.avg_eval_score"
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  placeholder="최근 평가 평균 점수"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">심사 상태</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.status"
                  :options="statusOptions"
                  required
                  placeholder="심사 상태 선택"
                  @change="onStatusChange"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">승진 발령일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.promoted_date"
                  :disabled="form.status !== 'approved'"
                  placeholder="승진 확정 시 발령일"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">심의 의견</CFormLabel>
              <CCol sm="10">
                <CFormTextarea
                  v-model="form.committee_review"
                  rows="3"
                  placeholder="인사위원회 심의 의견, 승진 추천 사유 및 보류/탈락 사유"
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
          v-if="canSubmit"
          type="submit"
          size="small"
          variant="flat"
          :color="candidate ? 'success' : 'primary'"
          :disabled="formsCheck || submitting"
        >
          저장
        </v-btn>
        <v-btn
          v-if="candidate && canHrWorkDelete"
          type="button"
          size="small"
          variant="flat"
          color="warning"
          :disabled="submitting"
          @click="deleteConfirm"
        >
          삭제
        </v-btn>
        <v-btn
          type="button"
          size="small"
          variant="flat"
          color="light"
          @click="$emit('close')"
        >
          닫기
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>승급 심사 대상 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 승급 심사 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn
        color="warning"
        size="small"
        variant="flat"
        :disabled="!candidate?.pk || submitting"
        @click="candidate?.pk && deleteObject(candidate.pk)"
      >
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
