<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount, inject } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { write_project } from '@/utils/pageAuth'
import { type ProjectAccountD2, type ProjectAccountD3 } from '@/store/types/proCash'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const d2List = inject<ProjectAccountD2[]>('d2List')
const d3List = inject<ProjectAccountD3[]>('d3List')

const props = defineProps({ budget: { type: Object, required: true } })
const emit = defineEmits(['on-update', 'on-delete'])

const form = reactive({
  pk: null,
  account_d2: null,
  account_opt: '',
  account_d3: null,
  basis_calc: null,
  budget: null,
  revised_budget: null,
})

const refAlertModal = ref()
const refConfirmModal = ref()

const formsCheck = computed(() => {
  const a = form.pk === props.budget.pk
  const b = form.account_d2 === props.budget.account_d2
  const c = form.account_opt === props.budget.account_opt
  const d = form.account_d3 === props.budget.account_d3
  const e = form.basis_calc === props.budget.basis_calc
  const f = form.budget === props.budget.budget || !props.budget.budget
  const g = form.revised_budget === props.budget.revised_budget
  return a && b && c && d && e && f && g
})

const onUpdateBudget = () => {
  if (write_project.value) {
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
  form.account_d2 = props.budget.account_d2
  form.account_opt = props.budget.account_opt
  form.account_d3 = props.budget.account_d3
  form.basis_calc = props.budget.basis_calc
  form.budget = props.budget.budget || '0'
  form.revised_budget = props.budget.revised_budget
}

onBeforeMount(() => dataSetup())
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model.number="form.account_d2" required>
        <option value="">대분류</option>
        <option v-for="d2 in d2List" :key="d2.pk" :value="d2.pk">
          {{ d2.name }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.account_opt"
        placeholder="중분류(필요시 기재)"
        @keydown.enter="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model.number="form.account_d3" required>
        <option value="">소분류</option>
        <option v-for="d3 in d3List" :key="d3.pk" :value="d3.pk">
          {{ d3.name }}
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
    <CTableDataCell v-if="write_project" class="text-center pt-3">
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
