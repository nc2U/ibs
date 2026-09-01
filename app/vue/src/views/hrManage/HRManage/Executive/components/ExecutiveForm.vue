<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, type PropType } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type Executive } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  executive: { type: Object as PropType<Executive>, default: null },
})

const emit = defineEmits(['multi-submit', 'on-delete', 'close'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_UPDATE))
const canHrWorkDelete = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_DELETE))

const comStore = useCompany()
const getPkExecutiveRanks = computed(() => comStore.getPkExecutiveRanks)
const getPkStaffs = computed(() =>
  comStore.allStaffList.map(s => ({
    value: s.pk as number,
    label: `${s.name} (${s.department || '부서없음'} / ${s.position || '직위없음'})`,
  })),
)

const directorTypes = [
  { value: 'inside', label: '사내이사' },
  { value: 'outside', label: '사외이사' },
  { value: 'non_standing_director', label: '기타비상무이사' },
  { value: 'auditor', label: '감사' },
  { value: 'advisor', label: '고문/자문' },
]

const representTypes = [
  { value: 'none', label: '해당없음' },
  { value: 'sole', label: '단독대표' },
  { value: 'joint', label: '공동대표' },
  { value: 'each', label: '각자대표' },
]

const refDelModal = ref()
const refAlertModal = ref()
const validated = ref(false)

const form = ref<Executive>({
  pk: undefined,
  company: undefined,
  staff: null as any,
  rank: null,
  director_type: 'inside',
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
    const b = form.value.staff === props.executive.staff
    const c = form.value.rank === props.executive.rank
    const d = form.value.director_type === props.executive.director_type
    const e = form.value.is_registered === props.executive.is_registered
    const f = form.value.is_standing === props.executive.is_standing
    const g = form.value.represent_type === props.executive.represent_type
    const h = form.value.term_start === props.executive.term_start
    const i = form.value.term_end === props.executive.term_end
    const j = form.value.appointed_date === props.executive.appointed_date
    const k = form.value.note === props.executive.note

    return a && b && c && d && e && f && g && h && i && j && k
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

const multiSubmit = (payload: Executive) => {
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
  if (props.executive) {
    form.value.pk = props.executive.pk
    form.value.company = props.executive.company
    form.value.staff = props.executive.staff
    form.value.rank = props.executive.rank ?? null
    form.value.director_type = props.executive.director_type
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
              <CFormLabel class="col-sm-4 col-form-label required">임원 (직원선택)</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.staff"
                  :options="getPkStaffs"
                  :disabled="!!executive"
                  required
                  placeholder="직원 선택"
                />
              </CCol>
            </CRow>
          </CCol>
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">임원 직위</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.rank"
                  :options="getPkExecutiveRanks"
                  placeholder="직위 선택"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required">상법상 지위</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.director_type"
                  :options="directorTypes"
                  required
                  placeholder="상법상 지위 선택"
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
                  id="is_registered"
                  v-model="form.is_registered"
                  label="등기 임원"
                  inline
                />
                <CFormCheck
                  id="is_standing"
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
          type="submit"
          size="small"
          :color="executive ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="executive" type="button" size="small" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
        <v-btn type="button" size="small" color="light" @click="$emit('close')" flat> 닫기</v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>임원 재임 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject(executive.pk as number)">
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
