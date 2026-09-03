<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, type PropType } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type StaffLeaveUsage, type LeaveType } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  usage: { type: Object as PropType<StaffLeaveUsage>, default: null },
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

const refDelModal = ref()
const refAlertModal = ref()
const validated = ref(false)

const form = ref<StaffLeaveUsage>({
  pk: undefined,
  company: undefined,
  staff: null as any,
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
    const b = form.value.staff === props.usage.staff
    const c = form.value.leave_type === props.usage.leave_type
    const d = form.value.start_date === props.usage.start_date
    const e = form.value.end_date === props.usage.end_date
    const f = Number(form.value.deduction_days) === Number(props.usage.deduction_days)
    const g = form.value.reason === props.usage.reason
    const h = form.value.is_cancelled === props.usage.is_cancelled

    return a && b && c && d && e && f && g && h
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

const multiSubmit = (payload: StaffLeaveUsage) => {
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
                  id="isCancelledCheck"
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
          type="submit"
          size="small"
          :color="usage ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="usage" type="button" size="small" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
        <v-btn type="button" size="small" color="light" @click="$emit('close')" flat> 닫기</v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>휴가 사용 기록 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 휴가 사용 내역을 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject(usage.pk as number)"> 삭제 </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
