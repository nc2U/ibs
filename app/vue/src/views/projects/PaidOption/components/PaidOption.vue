<script lang="ts" setup>
import { ref, reactive, computed, watch, inject, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms'
import type { OptionItem } from '@/store/types/project'
import type { TypeOption } from './OptionAddForm.vue'
import Multiselect from '@/components/MultiSelect/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  optionItem: { type: Object as PropType<OptionItem>, required: true },
})

const emit = defineEmits<{
  (e: 'on-update', payload: OptionItem): void
  (e: 'on-delete', pk: number): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const isSuperAuth = computed(() => useAccount().superAuth)

const getTypes = inject<TypeOption[]>('getTypes')

const toNullableNumber = (val: number | '' | null | undefined): number | null =>
  val !== null && val !== undefined && val !== '' ? Number(val) : null

const form = reactive<{
  types: number[]
  opt_code: string
  opt_name: string
  opt_desc: string
  opt_maker: string
  opt_price: number | '' | null
  opt_deposit: number | '' | null
  opt_balance: number | '' | null
}>({
  types: [],
  opt_code: '',
  opt_name: '',
  opt_desc: '',
  opt_maker: '',
  opt_price: null,
  opt_deposit: null,
  opt_balance: null,
})

const refAlertModal = ref()
const refConfirmModal = ref()

const dataSetup = () => {
  form.types = [...(props.optionItem.types || [])]
  form.opt_code = props.optionItem.opt_code ?? ''
  form.opt_name = props.optionItem.opt_name ?? ''
  form.opt_desc = props.optionItem.opt_desc ?? ''
  form.opt_maker = props.optionItem.opt_maker ?? ''
  form.opt_price = props.optionItem.opt_price ?? null
  form.opt_deposit = props.optionItem.opt_deposit ?? null
  form.opt_balance = props.optionItem.opt_balance ?? null
}

watch(
  () => props.optionItem,
  () => dataSetup(),
  { deep: true, immediate: true },
)

const areArraysEqual = (a: number[], b: number[]) => {
  if (a.length !== b.length) return false
  const sortedA = [...a].sort((x, y) => x - y)
  const sortedB = [...b].sort((x, y) => x - y)
  return sortedA.every((val, idx) => val === sortedB[idx])
}

const isDepositBalanceValid = computed(() => {
  const price = toNullableNumber(form.opt_price)
  const deposit = toNullableNumber(form.opt_deposit)
  const balance = toNullableNumber(form.opt_balance)
  if (price !== null && deposit !== null && balance !== null) {
    return deposit + balance === price
  }
  return true
})

const isUnchanged = computed(() => {
  const typesSame = areArraysEqual(form.types, props.optionItem.types || [])
  const codeSame = (form.opt_code || '').trim() === (props.optionItem.opt_code || '').trim()
  const nameSame = form.opt_name.trim() === (props.optionItem.opt_name || '').trim()
  const descSame = (form.opt_desc || '').trim() === (props.optionItem.opt_desc || '').trim()
  const makerSame = (form.opt_maker || '').trim() === (props.optionItem.opt_maker || '').trim()
  const priceSame = toNullableNumber(form.opt_price) === (props.optionItem.opt_price ?? null)
  const depositSame = toNullableNumber(form.opt_deposit) === (props.optionItem.opt_deposit ?? null)
  const balanceSame = toNullableNumber(form.opt_balance) === (props.optionItem.opt_balance ?? null)

  return (
    typesSame &&
    codeSame &&
    nameSame &&
    descSame &&
    makerSame &&
    priceSame &&
    depositSame &&
    balanceSame
  )
})

const formsCheck = computed(() => {
  const hasTypes = form.types.length > 0
  const hasName = Boolean(form.opt_name.trim())
  const price = toNullableNumber(form.opt_price)
  const deposit = toNullableNumber(form.opt_deposit)
  const balance = toNullableNumber(form.opt_balance)
  const hasPrice = price !== null && price >= 0
  const depositValid = deposit === null || deposit >= 0
  const balanceValid = balance === null || balance >= 0

  if (
    !hasTypes ||
    !hasName ||
    !hasPrice ||
    !depositValid ||
    !balanceValid ||
    !isDepositBalanceValid.value
  ) {
    return true
  }
  return isUnchanged.value
})

const onUpdateOption = () => {
  if (formsCheck.value) return
  const price = toNullableNumber(form.opt_price)
  if (price === null) return

  if (canProjectUpdate.value) {
    emit('on-update', {
      pk: props.optionItem.pk,
      project: props.optionItem.project,
      types: [...form.types],
      opt_code: form.opt_code.trim() || null,
      opt_name: form.opt_name.trim(),
      opt_desc: form.opt_desc.trim() || null,
      opt_maker: form.opt_maker.trim() || null,
      opt_price: price,
      opt_deposit: toNullableNumber(form.opt_deposit),
      opt_balance: toNullableNumber(form.opt_balance),
    })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const onDeleteOption = () => {
  if (isSuperAuth.value) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}

const modalAction = () => {
  if (props.optionItem.pk) {
    emit('on-delete', props.optionItem.pk)
  }
  refConfirmModal.value.close()
}
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <Multiselect
        v-model="form.types"
        :options="getTypes || []"
        placeholder="타입구분"
        required
        :disabled="!canProjectUpdate"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.opt_code"
        maxlength="20"
        placeholder="품목 코드"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateOption"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.opt_name"
        maxlength="100"
        placeholder="품목 이름"
        required
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateOption"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.opt_desc"
        maxlength="200"
        placeholder="세부 옵션"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateOption"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.opt_maker"
        placeholder="제조사"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateOption"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model.number="form.opt_price"
        placeholder="옵션 가격"
        type="number"
        min="0"
        required
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateOption"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model.number="form.opt_deposit"
        placeholder="계약금"
        type="number"
        min="0"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateOption"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model.number="form.opt_balance"
        placeholder="잔금"
        type="number"
        min="0"
        :disabled="!canProjectUpdate"
        @keydown.enter.prevent="onUpdateOption"
      />
    </CTableDataCell>

    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateOption">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" class="ms-1" @click="onDeleteOption">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 옵션 정보 삭제</template>
    <template #default> 이 유상 옵션 데이터를 삭제 하시겠습니까?</template>
    <template #footer>
      <v-btn size="small" color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
