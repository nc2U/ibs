<script lang="ts" setup>
import { ref, reactive, computed, watch, inject, type PropType } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account'
import type { ProIncBudget } from '@/store/types/project'
import { type AccItem, type OGroup, type UType } from './BudgetAddForm.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  budget: { type: Object as PropType<ProIncBudget>, required: true },
})

const emit = defineEmits<{
  (e: 'on-update', payload: ProIncBudget): void
  (e: 'on-delete', pk: number): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const isSuperAuth = computed(() => useAccount().superAuth)

const accountList = inject<AccItem[]>('accountList')
const orderGroups = inject<OGroup[]>('orderGroups')
const unitTypes = inject<UType[]>('unitTypes')

const form = reactive<{
  pk: number | null
  account: number | ''
  order_group: number | ''
  unit_type: number | ''
  item_name: string
  average_price: number | '' | null
  quantity: number | '' | null
  budget: number | '' | null
  revised_budget: number | '' | null
}>({
  pk: null,
  account: '',
  order_group: '',
  unit_type: '',
  item_name: '',
  average_price: null,
  quantity: null,
  budget: null,
  revised_budget: null,
})

const toNullableNumber = (val: number | '' | null) =>
  val !== null && val !== '' ? Number(val) : null

const refAlertModal = ref()
const refConfirmModal = ref()

const isUnchanged = computed(() => {
  return (
    Number(form.account) === props.budget.account &&
    (form.order_group ? Number(form.order_group) : null) === (props.budget.order_group || null) &&
    (form.unit_type ? Number(form.unit_type) : null) === (props.budget.unit_type || null) &&
    form.item_name.trim() === (props.budget.item_name || '') &&
    toNullableNumber(form.average_price) === (props.budget.average_price || null) &&
    toNullableNumber(form.quantity) === props.budget.quantity &&
    toNullableNumber(form.budget) === props.budget.budget &&
    toNullableNumber(form.revised_budget) === (props.budget.revised_budget || null)
  )
})

const formsCheck = computed(() => {
  return (
    !form.account ||
    (!form.unit_type && !form.item_name.trim()) ||
    form.quantity === null ||
    form.quantity === '' ||
    Number(form.quantity) <= 0 ||
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
      order_group: form.order_group ? Number(form.order_group) : null,
      unit_type: form.unit_type ? Number(form.unit_type) : null,
      item_name: form.item_name.trim(),
      average_price: toNullableNumber(form.average_price),
      quantity: Number(form.quantity),
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

const dataSetup = () => {
  form.pk = props.budget.pk ?? null
  form.account = props.budget.account ?? ''
  form.order_group = props.budget.order_group ?? ''
  form.unit_type = props.budget.unit_type ?? ''
  form.item_name = props.budget.item_name ?? ''
  form.average_price = props.budget.average_price ?? null
  form.quantity = props.budget.quantity ?? null
  form.budget = props.budget.budget ?? null
  form.revised_budget = props.budget.revised_budget ?? null
}

watch(
  () => props.budget,
  () => dataSetup(),
  { deep: true, immediate: true },
)
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <CFormSelect v-model="form.account" :disabled="!canProjectUpdate" required>
        <option value="">계정</option>
        <option v-for="acc in accountList" :key="acc.value" :value="acc.value">
          {{ acc.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.order_group" :disabled="!canProjectUpdate">
        <option value="">차수</option>
        <option v-for="og in orderGroups" :key="og.value" :value="og.value">
          {{ og.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormSelect v-model="form.unit_type" :disabled="!canProjectUpdate">
        <option value="">타입</option>
        <option v-for="ut in unitTypes" :key="ut.value" :value="ut.value">
          {{ ut.label }}
        </option>
      </CFormSelect>
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.item_name"
        placeholder="항목명칭"
        :disabled="!canProjectUpdate"
        :required="!form.unit_type"
        @keydown.enter.prevent="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.average_price"
        type="number"
        min="0"
        placeholder="평균가격"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.quantity"
        type="number"
        min="0"
        placeholder="수량"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.budget"
        type="number"
        min="0"
        placeholder="인준수입예산"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onUpdateBudget"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.revised_budget"
        type="number"
        min="0"
        placeholder="현황수입예산"
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
    <template #header> 수입 예산 삭제</template>
    <template #default> 해당 수입 예산 항목을 삭제 하시겠습니까?</template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
