<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount, inject } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ budget: { type: Object, required: true } })
const emit = defineEmits(['on-update', 'on-delete'])

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const accountList = inject<any>('accountList')

const form = reactive({
  pk: null,
  account: null,
  basis_calc: null,
  budget: null,
  revised_budget: null,
})

const refAlertModal = ref()
const refConfirmModal = ref()

const formsCheck = computed(() => {
  const a = form.pk === props.budget.pk
  const b = form.account === props.budget.account
  const c = form.basis_calc === props.budget.basis_calc
  const d = form.budget === props.budget.budget || !props.budget.budget
  const e = form.revised_budget === props.budget.revised_budget
  return a && b && c && d && e
})

const onUpdateBudget = () => {
  if (canProjectUpdate.value) {
    emit('on-update', { ...form })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const accStore = useAccount()
const onDeleteBudget = () => {
  if (accStore.superAuth) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const modalAction = () => {
  emit('on-delete', props.budget.pk)
  refConfirmModal.value.close()
}

const dataSetup = () => {
  form.pk = props.budget.pk
  form.account = props.budget.account
  form.basis_calc = props.budget.basis_calc
  form.budget = props.budget.budget || '0'
  form.revised_budget = props.budget.revised_budget
}

onBeforeMount(() => dataSetup())
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model.number="form.account" required>
        <option value="">계정과목</option>
        <option v-for="acc in accountList" :key="acc.value" :value="acc.value">
          {{ acc.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.basis_calc"
        placeholder="산출근거"
        @keydown.enter="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.budget"
        type="number"
        min="0"
        required
        placeholder="인준 지출 예산"
        @keydown.enter="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.revised_budget"
        type="number"
        min="0"
        placeholder="현황 지출 예산"
        @keydown.enter="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateBudget">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" @click="onDeleteBudget">삭제</v-btn>
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
