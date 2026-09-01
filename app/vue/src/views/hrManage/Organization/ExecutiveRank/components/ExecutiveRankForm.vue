<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, type PropType } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { type ExecutiveRank } from '@/store/types/company.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  company: { type: String, default: null },
  executiveRank: { type: Object as PropType<ExecutiveRank>, default: null },
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
const canHrWorkCreate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_CREATE))
const canHrWorkUpdate = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_UPDATE))
const canHrWorkDelete = computed(() => accStore.isStaff && can(PERM.HQ_HR_WORK_DELETE))

const refDelModal = ref()
const refAlertModal = ref()

const validated = ref(false)

const form = ref<ExecutiveRank>({
  pk: undefined,
  company: undefined,
  code: '',
  name: '',
  rank_order: 1,
  role_desc: '',
})

const formsCheck = computed(() => {
  if (props.executiveRank) {
    const a = form.value.code === props.executiveRank.code
    const b = form.value.name === props.executiveRank.name
    const c = form.value.rank_order === props.executiveRank.rank_order
    const d = form.value.role_desc === props.executiveRank.role_desc

    return a && b && c && d
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

const multiSubmit = (payload: ExecutiveRank) => {
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
  if (props.executiveRank) {
    form.value.pk = props.executiveRank.pk
    form.value.company = props.executiveRank.company
    form.value.code = props.executiveRank.code || ''
    form.value.name = props.executiveRank.name
    form.value.rank_order = props.executiveRank.rank_order ?? 1
    form.value.role_desc = props.executiveRank.role_desc || ''
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
              <CFormLabel class="col-sm-2 col-form-label required">서열 순서</CFormLabel>
              <CCol sm="10">
                <CFormInput
                  v-model.number="form.rank_order"
                  type="number"
                  required
                  placeholder="서열 순서 (낮을수록 상위 서열, 예: 1, 2, 3...)"
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
                <CFormInput v-model="form.code" placeholder="예: E1, E2, E3, CEO 등" />
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
          type="submit"
          size="small"
          :color="executiveRank ? 'success' : 'primary'"
          :disabled="formsCheck"
        >
          저장
        </v-btn>
        <v-btn v-if="executiveRank" type="button" size="small" color="warning" @click="deleteConfirm">
          삭제
        </v-btn>
        <v-btn type="button" size="small" color="light" @click="$emit('close')" flat> 닫기</v-btn>
      </slot>
    </CModalFooter>
  </CForm>

  <ConfirmModal ref="refDelModal">
    <template #header>임원 직위 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject(executiveRank.pk as number)">
        삭제
      </v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
