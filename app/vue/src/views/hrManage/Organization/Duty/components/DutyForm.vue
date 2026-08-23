<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, type PropType } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { type Duty } from '@/store/types/company.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  duty: { type: Object as PropType<Duty>, default: null },
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
const canHrWorkDelete = computed(() => accStore.isStaff && can(PERM.HR_WORK_DELETE))

const refDelModal = ref()
const refAlertModal = ref()

const validated = ref(false)

const form = ref<Duty>({
  pk: undefined,
  company: undefined,
  code: '',
  name: '',
  desc: '',
})

const formsCheck = computed(() => {
  if (props.duty) {
    const a = form.value.code === props.duty.code
    const b = form.value.name === props.duty.name
    const c = form.value.desc === props.duty.desc

    return a && b && c
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

const multiSubmit = (payload: Duty) => {
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
  if (props.duty) {
    form.value.pk = props.duty.pk
    form.value.company = props.duty.company
    form.value.code = props.duty.code || ''
    form.value.name = props.duty.name
    form.value.desc = props.duty.desc
  } else form.value.company = props.company
}

onBeforeMount(() => formDataSetup())
</script>

<template>
  <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
    <CModalBody class="p-4">
      <div>
        <CRow class="mb-3"></CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required">직책 코드</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.code" placeholder="예: CEO, HQ_HEAD, TEAM_LEADER 등" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required">직책명</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.name" required placeholder="직책명" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label"> 설명</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.desc" placeholder="설명" />
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
          :color="duty ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="duty" type="button" size="small" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
        <v-btn type="button" size="small" color="light" @click="$emit('close')" flat> 닫기</v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>직급 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject(duty.pk as number)">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
