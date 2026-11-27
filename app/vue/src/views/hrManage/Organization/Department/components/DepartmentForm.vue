<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { type Department } from '@/store/types/company.ts'
import MultiSelect from '@/components/MultiSelect/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = withDefaults(
  defineProps<{
    company?: string | null
    department?: Department | null
  }>(),
  {
    company: null,
    department: null,
  },
)

watch(
  () => props.company,
  newVal => {
    if (!!newVal) form.value.company = newVal
    else form.value.company = undefined
  },
)

const emit = defineEmits<{
  (e: 'multi-submit', payload: Department, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
  (e: 'close'): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => canGlobal(PERM.HQ_HR_WORK_UPDATE))
const canSubmit = computed(() =>
  props.department ? canHrWorkUpdate.value : canHrWorkCreate.value,
)
const canHrWorkDelete = computed(() => canGlobal(PERM.HQ_HR_WORK_DELETE))

const refDelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

const validated = ref(false)
const submitting = ref(false)

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
    const a = (form.value.upper_depart ?? null) === (props.department.upper_depart ?? null)
    const b = form.value.name === props.department.name
    const c = (form.value.manager ?? null) === (props.department.manager ?? null)
    const d = (form.value.task ?? '') === (props.department.task ?? '')

    return a && b && c && d
  } else return false
})

const comStore = useCompany()
const getPkDeparts = computed(() =>
  comStore.getPkDeparts.filter(d => d.value !== props.department?.pk),
)
const allStaffs = computed(() => comStore.getAllStaffs)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (canSubmit.value) multiSubmit({ ...form.value })
    else refAlertModal.value?.callModal()
  }
}

const multiSubmit = (payload: Department) => {
  submitting.value = true
  emit('multi-submit', payload, ok => {
    submitting.value = false
    if (ok) emit('close')
  })
}

const deleteObject = () => {
  if (props.department?.pk) {
    submitting.value = true
    emit('on-delete', props.department.pk, ok => {
      submitting.value = false
      refDelModal.value?.close()
      if (ok) emit('close')
    })
  }
}

const deleteConfirm = () => {
  if (canHrWorkDelete.value) refDelModal.value?.callModal()
  else refAlertModal.value?.callModal()
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
  } else form.value.company = props.company || undefined
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
                  v-model="form.upper_depart"
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
                <CFormInput v-model="form.name" required placeholder="부서명" />
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
          v-if="canSubmit"
          type="submit"
          variant="flat"
          :color="department ? 'success' : 'primary'"
          size="small"
          :disabled="formsCheck || submitting"
        >
          저장
        </v-btn>
        <v-btn
          v-if="department && canHrWorkDelete"
          type="button"
          variant="flat"
          color="warning"
          size="small"
          :disabled="submitting"
          @click="deleteConfirm"
        >
          삭제
        </v-btn>
        <v-btn
          type="button"
          variant="flat"
          color="light"
          size="small"
          @click="$emit('close')"
        >
          닫기
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>부서 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" variant="flat" @click="deleteObject">
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
