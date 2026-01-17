<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount, inject } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { write_project } from '@/utils/pageAuth'
import { type OGroup, type UType } from './BudgetAddForm.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const accountList = inject<any>('accountList')
const orderGroups = inject<OGroup[]>('orderGroups')
const unitTypes = inject<UType[]>('unitTypes')

const props = defineProps({ budget: { type: Object, required: true } })
const emit = defineEmits(['on-update', 'on-delete'])

const form = reactive({
  pk: null,
  account: null,
  order_group: null,
  unit_type: null,
  item_name: '',
  average_price: null,
  quantity: null,
  budget: null,
  revised_budget: null,
})

const refAlertModal = ref()
const refConfirmModal = ref()

const formsCheck = computed(() => {
  const a = form.pk === props.budget.pk
  const b = form.account === props.budget.account
  const c = form.order_group === props.budget.order_group
  const d = form.unit_type === props.budget.unit_type
  const e = form.item_name === props.budget.item_name
  const f = form.average_price === props.budget.average_price
  const g = form.quantity === props.budget.quantity
  const h = form.budget === props.budget.budget
  const i = form.revised_budget === props.budget.revised_budget
  return a && b && c && d && e && f && g && h && i
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
  form.account = props.budget.account
  form.order_group = props.budget.order_group
  form.unit_type = props.budget.unit_type
  form.item_name = props.budget.item_name
  form.average_price = props.budget.average_price
  form.quantity = props.budget.quantity
  form.budget = props.budget.budget
  form.revised_budget = props.budget.revised_budget
}

onBeforeMount(() => dataSetup())
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model="form.account" required>
        <option value="">계정</option>
        <option v-for="acc in accountList" :key="acc.value" :value="acc.value">
          {{ acc.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.order_group">
        <option value="">차수</option>
        <option v-for="og in orderGroups" :key="og.value" :value="og.value">
          {{ og.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.unit_type">
        <option value="">타입</option>
        <option v-for="ut in unitTypes" :key="ut.value" :value="ut.value">
          {{ ut.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput v-model="form.item_name" placeholder="항목명칭" @keydown.enter="onUpdateBudget" />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.average_price"
        type="number"
        min="0"
        placeholder="평균가격"
        @keydown.enter="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.quantity"
        type="number"
        min="0"
        placeholder="수량"
        @keydown.enter="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.budget"
        type="number"
        min="0"
        placeholder="인준수입예산"
        @keydown.enter="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.revised_budget"
        type="number"
        min="0"
        placeholder="현황수입예산"
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
    <template #header> 수입 예산 삭제</template>
    <template #default> 해당 수입 예산 항목을 삭제 하시겠습니까?</template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
