<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type StaffLeaveUsage, type LeaveType } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps<{
  company?: string
  usage?: StaffLeaveUsage
}>()

const emit = defineEmits<{
  (e: 'multi-submit', payload: StaffLeaveUsage, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
  (e: 'close'): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => canGlobal(PERM.HQ_HR_WORK_UPDATE))
const canSubmit = computed(() => (props.usage ? canHrWorkUpdate.value : canHrWorkCreate.value))
const canHrWorkDelete = computed(() => canGlobal(PERM.HQ_HR_WORK_DELETE))

const comStore = useCompany()
const allStaffList = computed(() => comStore.allStaffList)

const getPkStaffs = computed(() =>
  allStaffList.value.map(s => ({
    value: s.pk as number,
    label: `${s.name} (${s.department || '부서없음'} / ${s.position || '직위없음'})`,
  })),
)

const leaveTypeOptions = [
  { value: 'annual', label: '연차 (1일 차감)', defaultDays: 1.0 },
  { value: 'half_am', label: '오전 반차 (0.5일 차감)', defaultDays: 0.5 },
  { value: 'half_pm', label: '오후 반차 (0.5일 차감)', defaultDays: 0.5 },
  { value: 'quarter', label: '반반차 (0.25일 차감)', defaultDays: 0.25 },
  { value: 'official', label: '공가/예비군 (차감 없음)', defaultDays: 0.0 },
  { value: 'sick', label: '병가', defaultDays: 1.0 },
  { value: 'condolence', label: '경조 휴가 (차감 없음)', defaultDays: 0.0 },
  { value: 'reward', label: '포상 휴가', defaultDays: 1.0 },
  { value: 'substitute', label: '대체 휴가', defaultDays: 1.0 },
  { value: 'other', label: '기타 휴가', defaultDays: 1.0 },
]

const refDelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)
const validated = ref(false)
const submitting = ref(false)

type LeaveUsageFormState = Omit<StaffLeaveUsage, 'staff'> & { staff: number | null }

const form = ref<LeaveUsageFormState>({
  pk: undefined,
  company: undefined,
  staff: null,
  leave_type: 'annual',
  start_date: '',
  end_date: '',
  deduction_days: 1.0,
  reason: '',
  is_cancelled: false,
})

const onTypeChange = (typeVal: LeaveType) => {
  if (!props.usage) {
    const found = leaveTypeOptions.find(opt => opt.value === typeVal)
    if (found) form.value.deduction_days = found.defaultDays
  }
}

const onStartDateChange = (val: string) => {
  if (!form.value.end_date || form.value.end_date < val) {
    form.value.end_date = val
  }
}

const formsCheck = computed(() => {
  if (props.usage) {
    const a = form.value.pk === props.usage.pk
    const b = (form.value.staff ?? null) === (props.usage.staff ?? null)
    const c = form.value.leave_type === props.usage.leave_type
    const d = form.value.start_date === props.usage.start_date
    const e = form.value.end_date === props.usage.end_date
    const f = Number(form.value.deduction_days) === Number(props.usage.deduction_days)
    const g = (form.value.reason ?? '') === (props.usage.reason ?? '')
    const h = Boolean(form.value.is_cancelled) === Boolean(props.usage.is_cancelled)

    return a && b && c && d && e && f && g && h
  } else return false
})

const onSubmit = (event: Event) => {
  if (
    isValidate(event) ||
    form.value.staff === null ||
    !form.value.leave_type ||
    !form.value.start_date ||
    !form.value.end_date
  ) {
    validated.value = true
  } else {
    if (canSubmit.value) multiSubmit({ ...form.value, staff: form.value.staff })
    else refAlertModal.value?.callModal()
  }
}

const multiSubmit = (payload: StaffLeaveUsage) => {
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
  if (props.usage) {
    form.value.pk = props.usage.pk
    form.value.company = props.usage.company
    form.value.staff = props.usage.staff
    form.value.leave_type = props.usage.leave_type
    form.value.start_date = props.usage.start_date
    form.value.end_date = props.usage.end_date
    form.value.deduction_days = Number(props.usage.deduction_days)
    form.value.reason = props.usage.reason || ''
    form.value.is_cancelled = !!props.usage.is_cancelled
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
              <CFormLabel class="col-sm-4 col-form-label required">대상 직원</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.staff"
                  :options="getPkStaffs"
                  :disabled="!!usage"
                  required
                  placeholder="대상 직원 선택"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">휴가 구분</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.leave_type"
                  :options="leaveTypeOptions"
                  required
                  placeholder="휴가 구분 선택"
                  @change="onTypeChange"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="4">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">시작일</CFormLabel>
              <CCol sm="8">
                <DatePicker
                  v-model="form.start_date"
                  required
                  placeholder="휴가 시작일"
                  @update:model-value="onStartDateChange"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="4">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">종료일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.end_date" required placeholder="휴가 종료일" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="4">
            <CRow>
              <CFormLabel class="col-sm-5 col-form-label required">차감 일수</CFormLabel>
              <CCol sm="7">
                <CFormInput
                  v-model.number="form.deduction_days"
                  type="number"
                  step="0.25"
                  min="0"
                  required
                  placeholder="차감 일수 (예: 1.0, 0.5)"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">휴가 사유</CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model="form.reason"
                  placeholder="휴가 사유 및 세부 내역 (예: 개인 사유, 예비군 훈련 등)"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow v-if="usage" class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">취소 상태</CFormLabel>
              <CCol sm="10" class="pt-2">
                <CFormCheck
                  :id="`isCancelledCheck_${usage?.pk ?? 'new'}`"
                  v-model="form.is_cancelled"
                  label="휴가 취소 처리 (체크 시 사용 일수가 차감에서 복구됩니다)"
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
          :color="usage ? 'success' : 'primary'"
          :disabled="formsCheck || submitting"
        >
          저장
        </v-btn>
        <v-btn
          v-if="usage && canHrWorkDelete"
          type="button"
          size="small"
          color="warning"
          :disabled="submitting"
          @click="deleteConfirm"
        >
          삭제
        </v-btn>
        <v-btn
          type="button"
          size="small"
          color="light"
          variant="flat"
          @click="$emit('close')"
        >
          닫기
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>휴가 사용 기록 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 휴가 사용 내역을 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn
        color="warning"
        size="small"
        :disabled="submitting"
        @click="usage?.pk && deleteObject(usage.pk)"
      >
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
