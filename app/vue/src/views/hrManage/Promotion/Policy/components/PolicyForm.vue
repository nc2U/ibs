<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type PromotionPolicy } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps<{
  company?: string | null
  policy?: PromotionPolicy | null
}>()

const emit = defineEmits<{
  (e: 'multi-submit', payload: PromotionPolicy, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
  (e: 'close'): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => canGlobal(PERM.HQ_HR_WORK_UPDATE))
const canSubmit = computed(() => (props.policy ? canHrWorkUpdate.value : canHrWorkCreate.value))
const canHrWorkDelete = computed(() => canGlobal(PERM.HQ_HR_WORK_DELETE))

const comStore = useCompany()
const getPkGrades = computed(() => comStore.getPkGrades)

const refDelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)
const validated = ref(false)
const submitting = ref(false)

const normalizeNum = (v: number | string | null | undefined) =>
  v === '' || v === null || v === undefined ? null : Number(v)

type PolicyFormState = Omit<PromotionPolicy, 'current_grade' | 'target_grade'> & {
  current_grade: number | null
  target_grade: number | null
}

const form = ref<PolicyFormState>({
  pk: undefined,
  company: undefined,
  current_grade: null,
  target_grade: null,
  min_years: 3,
  min_avg_grade_point: null,
  required_eval_grade: '',
  required_credentials: '',
  disqualification_conditions: '',
  description: '',
  is_active: true,
})

const formsCheck = computed(() => {
  if (props.policy) {
    const a = form.value.pk === props.policy.pk
    const b = (form.value.current_grade ?? null) === (props.policy.current_grade ?? null)
    const c = (form.value.target_grade ?? null) === (props.policy.target_grade ?? null)
    const d = Number(form.value.min_years) === Number(props.policy.min_years)
    const e =
      normalizeNum(form.value.min_avg_grade_point) ===
      normalizeNum(props.policy.min_avg_grade_point)
    const f = (form.value.required_eval_grade ?? '') === (props.policy.required_eval_grade ?? '')
    const g = (form.value.required_credentials ?? '') === (props.policy.required_credentials ?? '')
    const h =
      (form.value.disqualification_conditions ?? '') ===
      (props.policy.disqualification_conditions ?? '')
    const i = (form.value.description ?? '') === (props.policy.description ?? '')
    const j = form.value.is_active === props.policy.is_active

    return a && b && c && d && e && f && g && h && i && j
  } else return false
})

const onSubmit = (event: Event) => {
  if (
    isValidate(event) ||
    form.value.current_grade === null ||
    form.value.target_grade === null ||
    !form.value.min_years
  ) {
    validated.value = true
  } else {
    if (canSubmit.value) {
      multiSubmit({
        ...form.value,
        current_grade: form.value.current_grade,
        target_grade: form.value.target_grade,
        min_avg_grade_point: normalizeNum(form.value.min_avg_grade_point),
      })
    } else refAlertModal.value?.callModal()
  }
}

const multiSubmit = (payload: PromotionPolicy) => {
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
  if (props.policy) {
    form.value.pk = props.policy.pk
    form.value.company = props.policy.company
    form.value.current_grade = props.policy.current_grade
    form.value.target_grade = props.policy.target_grade
    form.value.min_years = props.policy.min_years || 3
    form.value.min_avg_grade_point =
      props.policy.min_avg_grade_point !== null && props.policy.min_avg_grade_point !== undefined
        ? Number(props.policy.min_avg_grade_point)
        : null
    form.value.required_eval_grade = props.policy.required_eval_grade || ''
    form.value.required_credentials = props.policy.required_credentials || ''
    form.value.disqualification_conditions = props.policy.disqualification_conditions || ''
    form.value.description = props.policy.description || ''
    form.value.is_active = props.policy.is_active
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
              <CFormLabel class="col-sm-4 col-form-label required">현재 직급</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.current_grade"
                  :options="getPkGrades"
                  :disabled="!!policy"
                  required
                  placeholder="현재 직급 선택"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">승급 대상 직급</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.target_grade"
                  :options="getPkGrades"
                  :disabled="!!policy"
                  required
                  placeholder="승급 대상 직급 선택"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">최소 체류기간</CFormLabel>
              <CCol sm="8">
                <CInputGroup>
                  <CFormInput
                    v-model.number="form.min_years"
                    type="number"
                    min="1"
                    required
                    placeholder="최소 근속년수"
                  />
                  <CInputGroupText>년</CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">최소 평가평점</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.min_avg_grade_point"
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  placeholder="예: 80.0"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">최소 평가등급</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model="form.required_eval_grade"
                  placeholder="예: 최근 2개년 평균 B+ 이상"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">사용 여부</CFormLabel>
              <CCol sm="8" class="pt-2">
                <CFormCheck
                  :id="`policy_is_active_${policy?.pk ?? 'new'}`"
                  v-model="form.is_active"
                  label="현재 승급 정책 활성화(사용)"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">필수 역량/자격</CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model="form.required_credentials"
                  placeholder="예: 리더십 교육 이수, 어학 기준, 관련 기사/기술사 자격증 등"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">승급 결격 사유</CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model="form.disqualification_conditions"
                  placeholder="예: 최근 1년 이내 견책 이상의 징계 처분 이력 등"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">세부 기준 설명</CFormLabel>
              <CCol sm="10">
                <CFormTextarea
                  v-model="form.description"
                  rows="3"
                  placeholder="직급 승급 심사 가이드라인 및 세부 기준 설명"
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
          :color="policy ? 'success' : 'primary'"
          :disabled="formsCheck || submitting"
        >
          저장
        </v-btn>
        <v-btn
          v-if="policy && canHrWorkDelete"
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
    <template #header>승급 정책 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 승급 정책을 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn
        color="warning"
        size="small"
        variant="flat"
        :disabled="!policy?.pk || submitting"
        @click="policy?.pk && deleteObject(policy.pk)"
      >
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
