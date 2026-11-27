<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type Executive } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps<{
  company?: string
  executive?: Executive
}>()

const emit = defineEmits<{
  (e: 'multi-submit', payload: Executive, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
  (e: 'close'): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => canGlobal(PERM.HQ_HR_WORK_UPDATE))
const canSubmit = computed(() => (props.executive ? canHrWorkUpdate.value : canHrWorkCreate.value))
const canHrWorkDelete = computed(() => canGlobal(PERM.HQ_HR_WORK_DELETE))

const comStore = useCompany()
const getPkExecutiveRanks = computed(() => comStore.getPkExecutiveRanks)
const getPkStaffs = computed(() =>
  comStore.allStaffList.map(s => ({
    value: s.pk as number,
    label: `${s.name} (${s.department || '부서없음'} / ${s.position || '직위없음'})`,
  })),
)

const executiveTypes = [
  { value: 'inside', label: '사내이사' },
  { value: 'outside', label: '사외이사' },
  { value: 'non_standing', label: '기타비상무이사' },
  { value: 'auditor', label: '감사' },
  { value: 'advisor', label: '고문' },
]

const representTypes = [
  { value: 'none', label: '해당없음' },
  { value: 'sole', label: '단독대표' },
  { value: 'joint', label: '공동대표' },
  { value: 'each', label: '각자대표' },
]

const refDelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)
const validated = ref(false)
const submitting = ref(false)

const form = ref<Executive>({
  pk: undefined,
  company: undefined,
  staff: null,
  name: '',
  contact: '',
  rank: null,
  executive_type: 'inside',
  is_registered: false,
  is_standing: true,
  represent_type: 'none',
  term_start: null,
  term_end: null,
  appointed_date: null,
  note: '',
})

const formsCheck = computed(() => {
  if (props.executive) {
    const a = form.value.pk === props.executive.pk
    const b = (form.value.staff ?? null) === (props.executive.staff ?? null)
    const c = (form.value.name ?? '') === (props.executive.name ?? '')
    const d = (form.value.contact ?? '') === (props.executive.contact ?? '')
    const e = (form.value.rank ?? null) === (props.executive.rank ?? null)
    const f = form.value.executive_type === props.executive.executive_type
    const g = form.value.is_registered === props.executive.is_registered
    const h = form.value.is_standing === props.executive.is_standing
    const i = form.value.represent_type === props.executive.represent_type
    const j = (form.value.term_start ?? null) === (props.executive.term_start ?? null)
    const k = (form.value.term_end ?? null) === (props.executive.term_end ?? null)
    const l = (form.value.appointed_date ?? null) === (props.executive.appointed_date ?? null)
    const m = (form.value.note ?? '') === (props.executive.note ?? '')

    return a && b && c && d && e && f && g && h && i && j && k && l && m
  } else return false
})

const isStaffRequired = computed(() => !form.value.name)
const isNameRequired = computed(() => !form.value.staff)

const onSubmit = (event: Event) => {
  if (
    isValidate(event) ||
    !form.value.rank ||
    (!form.value.staff && !form.value.name?.trim())
  ) {
    validated.value = true
  } else {
    if (canSubmit.value) multiSubmit({ ...form.value })
    else refAlertModal.value?.callModal()
  }
}

const multiSubmit = (payload: Executive) => {
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
  if (props.executive) {
    form.value.pk = props.executive.pk
    form.value.company = props.executive.company
    form.value.staff = props.executive.staff
    form.value.name = props.executive.name
    form.value.contact = props.executive.contact
    form.value.rank = props.executive.rank ?? null
    form.value.executive_type = props.executive.executive_type
    form.value.is_registered = props.executive.is_registered
    form.value.is_standing = props.executive.is_standing
    form.value.represent_type = props.executive.represent_type
    form.value.term_start = props.executive.term_start || null
    form.value.term_end = props.executive.term_end || null
    form.value.appointed_date = props.executive.appointed_date || null
    form.value.note = props.executive.note || ''
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
              <CFormLabel class="col-sm-4 col-form-label" :class="{ required: isStaffRequired }">
                임원 (직원선택)
              </CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.staff"
                  :options="getPkStaffs"
                  :disabled="!!executive || !!form.name"
                  :required="isStaffRequired"
                  placeholder="직원 선택"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">임원 직위</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.rank"
                  :options="getPkExecutiveRanks"
                  required
                  placeholder="직위 선택"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="{ required: isNameRequired }">
                이름
              </CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model="form.name"
                  maxlength="20"
                  placeholder="이름"
                  :disabled="!!form.staff"
                  :required="isNameRequired"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">연락처</CFormLabel>
              <CCol sm="8">
                <input
                  v-model="form.contact"
                  v-maska
                  :data-maska="['###-###-####', '###-####-####']"
                  placeholder="연락처"
                  class="form-control"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">임원 구분</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.executive_type"
                  :options="executiveTypes"
                  required
                  placeholder="임원 구분 선택"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">대표권 구분</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.represent_type"
                  :options="representTypes"
                  required
                  placeholder="대표권 구분 선택"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">등기 / 상근 여부</CFormLabel>
              <CCol sm="8" class="d-flex align-items-center gap-4 pt-1">
                <CFormCheck
                  :id="`is_registered_${executive?.pk ?? 'new'}`"
                  v-model="form.is_registered"
                  label="등기 임원"
                  inline
                />
                <CFormCheck
                  :id="`is_standing_${executive?.pk ?? 'new'}`"
                  v-model="form.is_standing"
                  label="상근"
                  inline
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">최초 선임일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.appointed_date" placeholder="최초 선임일" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">임기 시작일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.term_start" placeholder="취임일 / 임기 시작일" />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">임기 만료일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.term_end" placeholder="임기 만료일" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">비고</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.note" placeholder="비고 및 주요 관장 업무" />
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
          :color="executive ? 'success' : 'primary'"
          :disabled="formsCheck || submitting"
        >
          저장
        </v-btn>
        <v-btn
          v-if="executive && canHrWorkDelete"
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
    <template #header>임원 재임 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn
        color="warning"
        size="small"
        :disabled="submitting"
        @click="executive?.pk && deleteObject(executive.pk)"
      >
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
