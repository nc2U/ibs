<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { useCompany } from '@/store/pinia/company.ts'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type Grade } from '@/store/types/company.ts'
import Multiselect from '@vueform/multiselect'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = withDefaults(
  defineProps<{
    company?: string | null
    grade?: Grade | null
  }>(),
  {
    company: null,
    grade: null,
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
  (e: 'multi-submit', payload: Grade, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
  (e: 'close'): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => canGlobal(PERM.HQ_HR_WORK_UPDATE))
const canSubmit = computed(() => (props.grade ? canHrWorkUpdate.value : canHrWorkCreate.value))
const canHrWorkDelete = computed(() => canGlobal(PERM.HQ_HR_WORK_DELETE))

const refDelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

const validated = ref(false)
const submitting = ref(false)

const normalizeNum = (v: number | string | null | undefined) =>
  v === '' || v === null || v === undefined ? null : Number(v)

const form = ref<Grade>({
  pk: undefined,
  company: undefined,
  code: '',
  role: '',
  min_promotion_years: null,
  positions: [],
  promotion_criteria: '',
})

const formsCheck = computed(() => {
  if (props.grade) {
    const a = form.value.code === props.grade.code
    const b = (form.value.role ?? '') === (props.grade.role ?? '')
    const c =
      normalizeNum(form.value.min_promotion_years) ===
      normalizeNum(props.grade.min_promotion_years)
    const d =
      JSON.stringify([...(form.value.positions || [])]) ===
      JSON.stringify([...(props.grade.positions || [])])
    const e = (form.value.promotion_criteria ?? '') === (props.grade.promotion_criteria ?? '')

    return a && b && c && d && e
  } else return false
})

const comStore = useCompany()
const getPkPositions = computed(() => comStore.getPkPositions)

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (canSubmit.value) {
      multiSubmit({
        ...form.value,
        min_promotion_years: normalizeNum(form.value.min_promotion_years),
        positions: [...(form.value.positions || [])],
      })
    } else refAlertModal.value?.callModal()
  }
}

const multiSubmit = (payload: Grade) => {
  submitting.value = true
  emit('multi-submit', payload, ok => {
    submitting.value = false
    if (ok) emit('close')
  })
}

const deleteObject = () => {
  if (props.grade?.pk) {
    submitting.value = true
    emit('on-delete', props.grade.pk, ok => {
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
  if (props.grade) {
    form.value.pk = props.grade.pk
    form.value.company = props.grade.company
    form.value.code = props.grade.code
    form.value.role = props.grade.role
    form.value.min_promotion_years = props.grade.min_promotion_years
    form.value.positions = [...(props.grade.positions || [])]
    form.value.promotion_criteria = props.grade.promotion_criteria
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
              <CFormLabel class="col-sm-2 col-form-label required">직급 코드</CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model="form.code"
                  required
                  placeholder="직급 코드 (예: G1, G2, G3 등)"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">역할</CFormLabel>
              <CCol sm="8">
                <CFormInput v-model="form.role" placeholder="역할 / 직무 수준" />
              </CCol>
            </CRow>
          </CCol>

          <CCol sm="6">
            <CRow>
              <CFormLabel class="col-sm-4 col-form-label">최소 근속기간</CFormLabel>
              <CCol sm="8">
                <CFormInput
                  v-model.number="form.min_promotion_years"
                  type="number"
                  placeholder="최소 근속기간 (년)"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">허용직위</CFormLabel>
              <CCol sm="10">
                <Multiselect
                  v-model="form.positions"
                  :options="getPkPositions"
                  mode="tags"
                  autocomplete="label"
                  :classes="{ search: 'form-control multiselect-search' }"
                  :add-option-on="['enter', 'tab']"
                  searchable
                  placeholder="허용직위"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">승급 기준</CFormLabel>
              <CCol sm="10">
                <CFormTextarea
                  v-model="form.promotion_criteria"
                  rows="3"
                  placeholder="승급 기준 및 요건"
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
          size="small"
          variant="flat"
          :color="grade ? 'success' : 'primary'"
          :disabled="formsCheck || submitting"
        >
          저장
        </v-btn>
        <v-btn
          v-if="grade && canHrWorkDelete"
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
    <template #header>직급 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" variant="flat" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
