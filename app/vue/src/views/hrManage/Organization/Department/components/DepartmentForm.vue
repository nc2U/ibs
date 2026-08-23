<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, type PropType } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { type Department } from '@/store/types/company.ts'
import MultiSelect from '@/components/MultiSelect/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  department: { type: Object as PropType<Department>, default: null },
})

watch(
  () => props.company,
  newVal => {
    if (!!newVal) form.value.company = newVal
    else form.value.company = undefined
  },
)

const emit = defineEmits(['multi-submit', 'on-delete', 'close'])

const { can, PERM } = usePerms()
const accStore = useAccount()
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => accStore.isStaff && can(PERM.HR_WORK_UPDATE))
const canHrWorkManager = computed(() => canHrWorkCreate.value || canHrWorkUpdate.value)
const canHrWorkDelete = computed(() => accStore.isStaff && can(PERM.HR_WORK_DELETE))

const refDelModal = ref()
const refAlertModal = ref()

const validated = ref(false)

const form = ref<Department>({
  pk: undefined,
  company: undefined,
  upper_depart: null,
  level: 1,
  name: '',
  manager: null,
  task: '',
})

const formsCheck = computed(() => {
  if (props.department) {
    const a = form.value.upper_depart === props.department.upper_depart
    const b = form.value.name === props.department.name
    const c = form.value.manager === props.department.manager
    const d = form.value.task === props.department.task

    return a && b && c && d
  } else return false
})

const comStore = useCompany()
const getPkDeparts = computed(() => comStore.getPkDeparts)
const allStaffs = computed(() => comStore.getAllStaffs)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (canHrWorkManager.value) multiSubmit({ ...form.value })
    else refAlertModal.value.callModal()
  }
}

const multiSubmit = (payload: Department) => {
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
  if (props.department) {
    form.value.pk = props.department.pk
    form.value.company = props.department.company
    form.value.upper_depart = props.department.upper_depart
    form.value.level = props.department.level
    form.value.name = props.department.name
    form.value.manager = props.department.manager
    form.value.task = props.department.task
  } else form.value.company = props.company
}

onBeforeMount(() => formDataSetup())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <div>
        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">상위부서</CFormLabel>
              <CCol sm="10">
                <MultiSelect
                  v-model.number="form.upper_depart"
                  mode="single"
                  :options="getPkDeparts"
                  placeholder="상위부서"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required">부서명</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model.number="form.name" required placeholder="부서명" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">주요업무</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.task" placeholder="주요업무" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">책임자</CFormLabel>
              <CCol sm="10">
                <MultiSelect
                  v-model="form.manager"
                  mode="single"
                  :options="allStaffs"
                  placeholder="책임자"
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
          v-if="canHrWorkManager"
          type="submit"
          :color="department ? 'success' : 'primary'"
          size="small"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn
          v-if="department && canHrWorkDelete"
          type="button"
          color="warning"
          size="small"
          @click="deleteConfirm"
        >
          삭제
        </v-btn>
        <v-btn type="button" color="light" size="small" @click="$emit('close')" flat> 닫기</v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>부서 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject(department.pk as number)">
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
