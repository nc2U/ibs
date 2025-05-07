<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, type PropType } from 'vue'
import { useStore } from '@/store'
import { useCompany } from '@/store/pinia/company'
import { useAccount } from '@/store/pinia/account'
import { type Staff } from '@/store/types/company'
import { isValidate } from '@/utils/helper'
import { write_human_resource } from '@/utils/pageAuth'
import Multiselect from '@vueform/multiselect'
import DatePicker from '@/components/DatePicker/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  staff: { type: Object as PropType<Staff>, default: null },
})

const emit = defineEmits(['multi-submit', 'on-delete', 'close'])

const refDelModal = ref()
const refAlertModal = ref()

const validated = ref(false)

const form = ref<Staff>({
  pk: undefined,
  company: undefined,
  sort: '2',
  name: '',
  id_number: '',
  personal_phone: '',
  email: '',
  department: '',
  grade: '',
  position: '',
  duty: '',
  date_join: null,
  date_leave: null,
  status: '1',
  user: null,
})

const formsCheck = computed(() => {
  if (props.staff) {
    const a = form.value.pk === props.staff.pk
    const b = form.value.sort === props.staff.sort
    const c = form.value.name === props.staff.name
    const d = form.value.id_number === props.staff.id_number
    const e = form.value.personal_phone === props.staff.personal_phone
    const f = form.value.email === props.staff.email
    const g = form.value.department === props.staff.department
    const h = form.value.grade === props.staff.grade
    const i = form.value.position === props.staff.position
    const j = form.value.duty === props.staff.duty
    const k = form.value.date_join === props.staff.date_join
    const l = form.value.date_leave === props.staff.date_leave
    const m = form.value.status === props.staff.status
    const n = form.value.user === props.staff.user

    return a && b && c && d && e && f && g && h && i && j && k && l && m && n
  } else return false
})

const store = useStore()
const isDark = computed(() => store.theme === 'dark')
const bgLight = computed(() => (!isDark.value ? 'bg-light' : 'bg-grey-darken-2'))
const comStore = useCompany()
const getSlugDeparts = computed(() => comStore.getSlugDeparts)
const getGrades = computed(() => comStore.getGrades)
const getPositions = computed(() => comStore.getPositions)
const getDutys = computed(() => comStore.getDutys)

const accStore = useAccount()
const getUsers = computed(() => accStore.getUsers)

const sorts = [
  { value: '1', label: '임원' },
  { value: '2', label: '직원' },
]

const statuses = [
  { value: '1', label: '근무 중' },
  { value: '2', label: '휴직 중' },
  { value: '3', label: '퇴직신청' },
  { value: '4', label: '퇴사처리' },
]

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (write_human_resource.value) multiSubmit({ ...form.value })
    else refAlertModal.value.callModal()
  }
}

const multiSubmit = (payload: Staff) => {
  emit('multi-submit', payload)
  emit('close')
}

const deleteObject = (pk: number) => {
  emit('on-delete', pk)
  refDelModal.value.close()
  emit('close')
}

const deleteConfirm = () => {
  if (write_human_resource.value) refDelModal.value.callModal()
  else refAlertModal.value.callModal()
}

const formDataSetup = () => {
  if (props.staff) {
    form.value.pk = props.staff.pk
    form.value.company = props.staff.company
    form.value.sort = props.staff.sort
    form.value.name = props.staff.name
    form.value.id_number = props.staff.id_number
    form.value.personal_phone = props.staff.personal_phone
    form.value.email = props.staff.email
    form.value.department = props.staff.department
    form.value.grade = props.staff.grade
    form.value.position = props.staff.position
    form.value.duty = props.staff.duty
    form.value.date_join = props.staff.date_join
    form.value.date_leave = props.staff.date_leave
    form.value.status = props.staff.status
    form.value.user = props.staff.user
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
              <CFormLabel class="col-sm-4 col-form-label" :class="bgLight"> 구분</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.sort"
                  :options="sorts"
                  autocomplete="label"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                  placeholder="구분"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required" :class="bgLight">
                입사일
              </CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.date_join" maxlength="10" placeholder="입사일" required />
              </CCol>
            </CRow>
          </CCol>
        </CRow>
        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required" :class="bgLight">
                성명
              </CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.name" required placeholder="성명" />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required" :class="bgLight">
                주민등록번호
              </CFormLabel>
              <CCol sm="8">
                <input
                  v-model="form.id_number"
                  v-maska
                  data-maska="######-#######"
                  class="form-control"
                  required
                  maxlength="14"
                  placeholder="주민등록번호"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label required" :class="bgLight">
                휴대전화
              </CFormLabel>
              <CCol sm="8">
                <input
                  v-model="form.personal_phone"
                  v-maska
                  data-maska="['###-###-####', '###-####-####']"
                  class="form-control"
                  maxlength="13"
                  required
                  placeholder="휴대전화"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="bgLight"> 이메일</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.email" type="email" placeholder="이메일" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <v-divider />

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="bgLight"> 부서</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.department"
                  :options="getSlugDeparts"
                  autocomplete="label"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                  placeholder="부서"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="bgLight"> 직급</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.grade"
                  :options="getGrades"
                  autocomplete="label"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                  placeholder="직급"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="bgLight"> 직위</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.position"
                  :options="getPositions"
                  autocomplete="label"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                  placeholder="직위"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="bgLight"> 직책</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.duty"
                  :options="getDutys"
                  autocomplete="label"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                  placeholder="직책"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="bgLight"> 상태</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model="form.status"
                  :options="statuses"
                  autocomplete="label"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                  placeholder="상태"
                />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="bgLight"> 퇴사일</CFormLabel>
              <CCol sm="8">
                <DatePicker v-model="form.date_leave" maxlength="10" placeholder="퇴사일" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <v-divider />

        <CRow class="mt-3">
          <CCol sm="6"></CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label" :class="bgLight"> 유저 정보</CFormLabel>
              <CCol sm="8">
                <Multiselect
                  v-model.number="form.user"
                  :options="getUsers"
                  autocomplete="label"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                  placeholder="유저 정보"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>
      </div>
    </CModalBody>

    <CModalFooter>
      <v-btn type="button" color="light" @click="$emit('close')"> 닫기</v-btn>
      <slot name="footer">
        <v-btn type="submit" :color="staff ? 'success' : 'primary'" :disabled="formsCheck">
          저장
        </v-btn>
        <v-btn v-if="staff" type="button" color="warning" @click="deleteConfirm"> 삭제</v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>직원 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
