<script lang="ts" setup>
import { ref, reactive, computed, watch, inject, type PropType } from 'vue'
import { usePerms } from '@/composables/usePerms'
import { useAccount } from '@/store/pinia/account'
import type { ProOutBudget } from '@/store/types/project'
import type { AccItem } from './BudgetAddForm.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  budget: { type: Object as PropType<ProOutBudget>, required: true },
})

const emit = defineEmits<{
  (e: 'on-update', payload: ProOutBudget): void
  (e: 'on-delete', pk: number): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const isSuperAuth = computed(() => useAccount().superAuth)

const accountList = inject<AccItem[]>('accountList')

const form = reactive<{
  pk: number | null
  account: number | ''
  basis_calc: string
  budget: number | '' | null
  revised_budget: number | '' | null
}>({
  pk: null,
  account: '',
  basis_calc: '',
  budget: null,
  revised_budget: null,
})

const toNullableNumber = (val: number | '' | null) =>
  val !== null && val !== '' ? Number(val) : null

const refAlertModal = ref()
const refConfirmModal = ref()

const dataSetup = () => {
  form.pk = props.budget.pk ?? null
  form.account = props.budget.account
  form.basis_calc = props.budget.basis_calc ?? ''
  form.budget = props.budget.budget ?? null
  form.revised_budget = props.budget.revised_budget ?? null
}

watch(
  () => props.budget,
  () => dataSetup(),
  { deep: true, immediate: true },
)

const isUnchanged = computed(() => {
  return (
    Number(form.account) === props.budget.account &&
    form.basis_calc.trim() === (props.budget.basis_calc || '') &&
    toNullableNumber(form.budget) === props.budget.budget &&
    toNullableNumber(form.revised_budget) === (props.budget.revised_budget || null)
  )
})

const formsCheck = computed(() => {
  return (
    !form.account ||
    form.budget === null ||
    form.budget === '' ||
    Number(form.budget) < 0 ||
    isUnchanged.value
  )
})

const onUpdateBudget = () => {
  if (formsCheck.value) return

  if (canProjectUpdate.value) {
    emit('on-update', {
      pk: props.budget.pk,
      project: props.budget.project,
      account: Number(form.account),
      basis_calc: form.basis_calc.trim(),
      budget: Number(form.budget),
      revised_budget: toNullableNumber(form.revised_budget),
    })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const onDeleteBudget = () => {
  if (isSuperAuth.value) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const modalAction = () => {
  if (props.budget.pk) {
    emit('on-delete', props.budget.pk)
  }
  refConfirmModal.value.close()
}
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model.number="form.account" :disabled="!canProjectUpdate" required>
        <option value="">계정과목</option>
        <option v-for="acc in accountList" :key="acc.value" :value="acc.value">
          {{ acc.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.basis_calc"
        maxlength="255"
        placeholder="산출근거"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.budget"
        type="number"
        min="0"
        required
        placeholder="인준 지출 예산"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.revised_budget"
        type="number"
        min="0"
        placeholder="현황 지출 예산"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateBudget">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" class="ms-1" @click="onDeleteBudget">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 지출 예산 삭제</template>
    <template #default> 해당 지출 예산 항목을 삭제 하시겠습니까?</template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
