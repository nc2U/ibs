<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, type PropType } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type PersonnelOrder, type Staff } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  order: { type: Object as PropType<PersonnelOrder>, default: null },
})

const emit = defineEmits(['multi-submit', 'on-delete', 'close'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_UPDATE))
const canHrWorkDelete = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_DELETE))

const comStore = useCompany()
const getPkDeparts = computed(() => comStore.getPkDeparts)
const getPkGrades = computed(() => comStore.getPkGrades)
const getPkPositions = computed(() => comStore.getPkPositions)
const getPkDutys = computed(() => comStore.getPkDutys)
const allStaffList = computed(() => comStore.allStaffList)

const getPkStaffs = computed(() =>
  allStaffList.value.map(s => ({
    value: s.pk as number,
    label: `${s.name} (${s.department || '부서없음'} / ${s.position || '직위없음'})`,
  })),
)

const orderTypes = [
  { value: '10', label: '채용/신규입사' },
  { value: '20', label: '승진/승급' },
  { value: '30', label: '부서이동(전보)' },
  { value: '40', label: '보직임면/겸직' },
  { value: '50', label: '휴직' },
  { value: '51', label: '복직' },
  { value: '60', label: '파견/전적' },
  { value: '70', label: '포상/표창' },
  { value: '80', label: '징계/문책' },
  { value: '90', label: '퇴사/면직' },
]

const refDelModal = ref()
const refAlertModal = ref()
const validated = ref(false)

const form = ref<PersonnelOrder>({
  pk: undefined,
  company: undefined,
  staff: null as any,
  order_type: '20',
  order_date: '',
  effective_end_date: null,
  order_no: '',
  prev_department: null,
  prev_grade: null,
  prev_position: null,
  prev_duty: null,
  new_department: null,
  new_grade: null,
  new_position: null,
  new_duty: null,
  description: '',
  is_processed: true,
})

const onStaffSelected = (staffPk: number) => {
  if (!staffPk) return
  const targetStaff = allStaffList.value.find(s => s.pk === staffPk)
  if (targetStaff) {
    // 이전 상태 자동 프리필
    const currentDep = comStore.allDepartList.find(d => d.name === targetStaff.department)
    const currentGrade = comStore.allGradeList.find(g => g.code === targetStaff.grade)
    const currentPos = comStore.allPositionList.find(p => p.name === targetStaff.position)
    const currentDuty = comStore.allDutyList.find(du => du.name === targetStaff.duty)

    form.value.prev_department = currentDep?.pk ?? null
    form.value.prev_grade = currentGrade?.pk ?? null
    form.value.prev_position = currentPos?.pk ?? null
    form.value.prev_duty = currentDuty?.pk ?? null

    // 발령 후 상태도 초기값으로 세팅
    if (!props.order) {
      form.value.new_department = currentDep?.pk ?? null
      form.value.new_grade = currentGrade?.pk ?? null
      form.value.new_position = currentPos?.pk ?? null
      form.value.new_duty = currentDuty?.pk ?? null
    }
  }
}

const formsCheck = computed(() => {
  if (props.order) {
    const a = form.value.pk === props.order.pk
    const b = form.value.staff === props.order.staff
    const c = form.value.order_type === props.order.order_type
    const d = form.value.order_date === props.order.order_date
    const e = form.value.effective_end_date === props.order.effective_end_date
    const f = form.value.order_no === props.order.order_no
    const g = form.value.new_department === props.order.new_department
    const h = form.value.new_grade === props.order.new_grade
    const i = form.value.new_position === props.order.new_position
    const j = form.value.new_duty === props.order.new_duty
    const k = form.value.description === props.order.description
    const l = form.value.is_processed === props.order.is_processed

    return a && b && c && d && e && f && g && h && i && j && k && l
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

const multiSubmit = (payload: PersonnelOrder) => {
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
  if (props.order) {
    form.value.pk = props.order.pk
    form.value.company = props.order.company
    form.value.staff = props.order.staff
    form.value.order_type = props.order.order_type
    form.value.order_date = props.order.order_date
    form.value.effective_end_date = props.order.effective_end_date || null
    form.value.order_no = props.order.order_no || ''
    form.value.prev_department = props.order.prev_department ?? null
    form.value.prev_grade = props.order.prev_grade ?? null
    form.value.prev_position = props.order.prev_position ?? null
    form.value.prev_duty = props.order.prev_duty ?? null
    form.value.new_department = props.order.new_department ?? null
    form.value.new_grade = props.order.new_grade ?? null
    form.value.new_position = props.order.new_position ?? null
    form.value.new_duty = props.order.new_duty ?? null
    form.value.description = props.order.description || ''
    form.value.is_processed = props.order.is_processed ?? true
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
                  :disabled="!!order"
                  required
                  placeholder="대상 직원 선택"
                  @change="onStaffSelected"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">발령 구분</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.order_type"
                  :options="orderTypes"
                  required
                  placeholder="발령 구분 선택"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">발령 일자(시행일)</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.order_date" required placeholder="발령 일자" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">종료 예정일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.effective_end_date" placeholder="휴직/파견 종료일" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">발령 문서번호</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.order_no" placeholder="예: 인사이력-2026-001" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">자동 반영</CFormLabel>
              <CCol sm="8" class="pt-1">
                <CFormCheck
                  id="is_processed"
                  v-model="form.is_processed"
                  label="직원 현재 상태에 즉시 자동 반영"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <!-- 발령 전 상태 스냅샷 -->
        <CCallout color="secondary" class="p-3 my-3 bg-light">
          <h6 class="fw-bold mb-2">발령 전 상태 (스냅샷)</h6>
          <CRow>
            <CCol sm="3">
              <CFormLabel class="small text-muted">이전 부서</CFormLabel>
              <Multiselect
                v-model="form.prev_department"
                :options="getPkDeparts"
                placeholder="이전 부서"
              />
            </CCol>
            <CCol sm="3">
              <CFormLabel class="small text-muted">이전 직급</CFormLabel>
              <Multiselect
                v-model="form.prev_grade"
                :options="getPkGrades"
                placeholder="이전 직급"
              />
            </CCol>
            <CCol sm="3">
              <CFormLabel class="small text-muted">이전 직위</CFormLabel>
              <Multiselect
                v-model="form.prev_position"
                :options="getPkPositions"
                placeholder="이전 직위"
              />
            </CCol>
            <CCol sm="3">
              <CFormLabel class="small text-muted">이전 직책</CFormLabel>
              <Multiselect
                v-model="form.prev_duty"
                :options="getPkDutys"
                placeholder="이전 직책"
              />
            </CCol>
          </CRow>
        </CCallout>

        <!-- 발령 후 상태 -->
        <CCallout color="primary" class="p-3 my-3 bg-light">
          <h6 class="fw-bold mb-2 text-primary">발령 후 상태 (새 보직/직급/직위)</h6>
          <CRow>
            <CCol sm="3">
              <CFormLabel class="small text-muted">새 발령 부서</CFormLabel>
              <Multiselect
                v-model="form.new_department"
                :options="getPkDeparts"
                placeholder="발령 부서"
              />
            </CCol>
            <CCol sm="3">
              <CFormLabel class="small text-muted">새 발령 직급</CFormLabel>
              <Multiselect
                v-model="form.new_grade"
                :options="getPkGrades"
                placeholder="발령 직급"
              />
            </CCol>
            <CCol sm="3">
              <CFormLabel class="small text-muted">새 발령 직위</CFormLabel>
              <Multiselect
                v-model="form.new_position"
                :options="getPkPositions"
                placeholder="발령 직위"
              />
            </CCol>
            <CCol sm="3">
              <CFormLabel class="small text-muted">새 발령 직책</CFormLabel>
              <Multiselect
                v-model="form.new_duty"
                :options="getPkDutys"
                placeholder="발령 직책"
              />
            </CCol>
          </CRow>
        </CCallout>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">발령 사유 / 내용</CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model="form.description"
                  placeholder="발령 사유, 세부 조치사항 요약"
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
          :color="order ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="order" type="button" size="small" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
        <v-btn type="button" size="small" color="light" @click="$emit('close')" flat> 닫기</v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>인사 발령 이력 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 발령 이력을 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject(order.pk as number)">
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
