<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, type PropType } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type StaffLeaveQuota } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  quota: { type: Object as PropType<StaffLeaveQuota>, default: null },
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

const refDelModal = ref()
const refAlertModal = ref()
const validated = ref(false)

const form = ref<StaffLeaveQuota>({
  pk: undefined,
  company: undefined,
  staff: null as any,
  year: currentYear,
  granted_days: 15.0,
  carry_over_days: 0.0,
  reward_days: 0.0,
  valid_start: `${currentYear}-01-01`,
  valid_end: `${currentYear}-12-31`,
  note: '',
})

const onYearChange = (yearVal: number) => {
  if (yearVal && !props.quota) {
    form.value.valid_start = `${yearVal}-01-01`
    form.value.valid_end = `${yearVal}-12-31`
  }
}

const totalGranted = computed(
  () =>
    Number(form.value.granted_days || 0) +
    Number(form.value.carry_over_days || 0) +
    Number(form.value.reward_days || 0),
)

const formsCheck = computed(() => {
  if (props.quota) {
    const a = form.value.pk === props.quota.pk
    const b = form.value.staff === props.quota.staff
    const c = form.value.year === props.quota.year
    const d = Number(form.value.granted_days) === Number(props.quota.granted_days)
    const e = Number(form.value.carry_over_days) === Number(props.quota.carry_over_days)
    const f = Number(form.value.reward_days) === Number(props.quota.reward_days)
    const g = form.value.valid_start === props.quota.valid_start
    const h = form.value.valid_end === props.quota.valid_end
    const i = form.value.note === props.quota.note

    return a && b && c && d && e && f && g && h && i
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

const multiSubmit = (payload: StaffLeaveQuota) => {
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
  if (props.quota) {
    form.value.pk = props.quota.pk
    form.value.company = props.quota.company
    form.value.staff = props.quota.staff
    form.value.year = props.quota.year
    form.value.granted_days = Number(props.quota.granted_days)
    form.value.carry_over_days = Number(props.quota.carry_over_days)
    form.value.reward_days = Number(props.quota.reward_days)
    form.value.valid_start = props.quota.valid_start
    form.value.valid_end = props.quota.valid_end
    form.value.note = props.quota.note || ''
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
              <CFormLabel class="col-sm-4 col-form-label required">대상 연도</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.year"
                  :options="years"
                  :disabled="!!quota"
                  required
                  placeholder="대상 연도"
                  @change="onYearChange"
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
                  :disabled="!!quota"
                  required
                  placeholder="대상 직원 선택"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="4">
            <CRow>
              <CFormLabel class="col-sm-5 col-form-label required">기본 발생</CFormLabel>
              <CCol sm="7">
                <CFormInput
                  v-model.number="form.granted_days"
                  type="number"
                  step="0.5"
                  min="0"
                  required
                  placeholder="기본 발생일"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="4">
            <CRow>
              <CFormLabel class="col-sm-5 col-form-label">이월/조정</CFormLabel>
              <CCol sm="7">
                <CFormInput
                  v-model.number="form.carry_over_days"
                  type="number"
                  step="0.5"
                  placeholder="이월 일수"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="4">
            <CRow>
              <CFormLabel class="col-sm-5 col-form-label">포상/가산</CFormLabel>
              <CCol sm="7">
                <CFormInput
                  v-model.number="form.reward_days"
                  type="number"
                  step="0.5"
                  placeholder="포상 일수"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <!-- 총 부여일수 계산 안내 -->
        <CAlert color="info" class="py-2 text-center">
          <strong>총 부여 연차 일수: {{ totalGranted.toFixed(2) }} 일</strong>
          (기본: {{ form.granted_days || 0 }} + 이월: {{ form.carry_over_days || 0 }} + 포상:
          {{ form.reward_days || 0 }})
        </CAlert>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">사용 시작일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.valid_start" required placeholder="사용 가능 시작일" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">사용 만료일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.valid_end" required placeholder="사용 가능 만료일" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">비고</CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model="form.note"
                  placeholder="부여 사유, 근속연수 가산 내역 등 관리 메모"
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
          :color="quota ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="quota" type="button" size="small" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
        <v-btn type="button" size="small" color="light" @click="$emit('close')" flat> 닫기</v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>연차 부여 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 연차 부여 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject(quota.pk as number)">
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
