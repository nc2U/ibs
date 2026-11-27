<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { type ExecutiveRank } from '@/store/types/company.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = withDefaults(
  defineProps<{
    company?: string | null
    executiveRank?: ExecutiveRank | null
  }>(),
  {
    company: null,
    executiveRank: null,
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
  (e: 'multi-submit', payload: ExecutiveRank, done?: (ok: boolean) => void): void
  (e: 'on-delete', pk: number, done?: (ok: boolean) => void): void
  (e: 'close'): void
}>()

const { canGlobal, PERM } = usePerms()
const canHrWorkCreate = computed(() => canGlobal(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => canGlobal(PERM.HQ_HR_WORK_UPDATE))
const canSubmit = computed(() =>
  props.executiveRank ? canHrWorkUpdate.value : canHrWorkCreate.value,
)
const canHrWorkDelete = computed(() => canGlobal(PERM.HQ_HR_WORK_DELETE))

const refDelModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const refAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

const validated = ref(false)
const submitting = ref(false)

const form = ref<ExecutiveRank>({
  pk: undefined,
  company: undefined,
  code: '',
  name: '',
  sort_order: 1,
  role_desc: '',
})

const formsCheck = computed(() => {
  if (props.executiveRank) {
    const a = (form.value.code ?? '') === (props.executiveRank.code ?? '')
    const b = form.value.name === props.executiveRank.name
    const c = (form.value.sort_order ?? 1) === (props.executiveRank.sort_order ?? 1)
    const d = (form.value.role_desc ?? '') === (props.executiveRank.role_desc ?? '')

    return a && b && c && d
  } else return false
})

const onSubmit = (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (canSubmit.value) multiSubmit({ ...form.value })
    else refAlertModal.value?.callModal()
  }
}

const multiSubmit = (payload: ExecutiveRank) => {
  submitting.value = true
  emit('multi-submit', payload, ok => {
    submitting.value = false
    if (ok) emit('close')
  })
}

const deleteObject = () => {
  if (props.executiveRank?.pk) {
    submitting.value = true
    emit('on-delete', props.executiveRank.pk, ok => {
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
  if (props.executiveRank) {
    form.value.pk = props.executiveRank.pk
    form.value.company = props.executiveRank.company
    form.value.code = props.executiveRank.code || ''
    form.value.name = props.executiveRank.name
    form.value.sort_order = props.executiveRank.sort_order ?? 1
    form.value.role_desc = props.executiveRank.role_desc || ''
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
              <CFormLabel class="col-sm-2 col-form-label required">정렬 순서</CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model.number="form.sort_order"
                  type="number"
                  required
                  placeholder="정렬 순서"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required">직위 코드</CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model="form.code"
                  required
                  placeholder="예: E1, E2, E3, CEO 등"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label required">임원 직위명</CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model="form.name"
                  required
                  placeholder="예: 이사, 상무, 전무, 부사장, 사장, 부회장, 회장 등"
                />
              </CCol>
            </CRow>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol sm="12">
            <CRow>
              <CFormLabel class="col-sm-2 col-form-label">역할/관장 설명</CFormLabel>
              <CCol sm="10">
                <CFormInput v-model="form.role_desc" placeholder="주요 역할 및 관장 부문 요약" />
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
          :color="executiveRank ? 'success' : 'primary'"
          :disabled="formsCheck || submitting"
        >
          저장
        </v-btn>
        <v-btn
          v-if="executiveRank && canHrWorkDelete"
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
    <template #header>임원 직위 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" variant="flat" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
