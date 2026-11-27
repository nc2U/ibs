<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Position } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = withDefaults(
  defineProps<{
    company?: string | null
    position?: Position | null
  }>(),
  {
    company: null,
    position: null,
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
  (e: 'multi-submit', payload: Position, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
  (e: 'close'): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => canGlobal(PERM.HQ_HR_WORK_UPDATE))
const canSubmit = computed(() => (props.position ? canHrWorkUpdate.value : canHrWorkCreate.value))
const canHrWorkDelete = computed(() => canGlobal(PERM.HQ_HR_WORK_DELETE))

const refDelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

const validated = ref(false)
const submitting = ref(false)

const form = ref<Position>({
  pk: undefined,
  company: undefined,
  name: '',
  grades: [],
  desc: '',
})

const formsCheck = computed(() => {
  if (props.position) {
    const a = form.value.name === props.position.name
    const b =
      JSON.stringify([...(form.value.grades || [])]) ===
      JSON.stringify([...(props.position.grades || [])])
    const c = (form.value.desc ?? '') === (props.position.desc ?? '')

    return a && b && c
  } else return false
})

const comCompany = useCompany()
const getPkGrades = computed(() => comCompany.getPkGrades)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (canSubmit.value) {
      multiSubmit({
        ...form.value,
        grades: [...(form.value.grades || [])],
      })
    } else refAlertModal.value?.callModal()
  }
}

const multiSubmit = (payload: Position) => {
  submitting.value = true
  emit('multi-submit', payload, ok => {
    submitting.value = false
    if (ok) emit('close')
  })
}

const deleteObject = () => {
  if (props.position?.pk) {
    submitting.value = true
    emit('on-delete', props.position.pk, ok => {
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
  if (props.position) {
    form.value.pk = props.position.pk
    form.value.company = props.position.company
    form.value.name = props.position.name
    form.value.grades = [...(props.position.grades || [])]
    form.value.desc = props.position.desc
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
              <CFormLabel class="col-sm-2 col-form-label required">직위명</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.name" required placeholder="직위명" />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">직급</CFormLabel>
              <CCol sm="10">
                <Multiselect
                  v-model="form.grades"
                  :options="getPkGrades"
                  mode="tags"
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
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">설명</CFormLabel>
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
          v-if="canSubmit"
          type="submit"
          size="small"
          variant="flat"
          :color="position ? 'success' : 'primary'"
          :disabled="formsCheck || submitting"
        >
          저장
        </v-btn>
        <v-btn
          v-if="position && canHrWorkDelete"
          type="button"
          size="small"
          variant="flat"
          color="warning"
          :disabled="submitting"
          @click="deleteConfirm"
        >
          삭제
        </v-btn>
        <v-btn
          type="button"
          size="small"
          variant="flat"
          color="light"
          @click="$emit('close')"
        >
          닫기
        </v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>직위 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" variant="flat" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
