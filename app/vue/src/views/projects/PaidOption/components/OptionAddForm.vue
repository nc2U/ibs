<script lang="ts" setup>
import { ref, reactive, inject, computed, watch } from 'vue'
import { isValidate } from '@/utils/helper'
import { usePerms } from '@/composables/usePerms'
import type { OptionItem } from '@/store/types/project'
import Multiselect from '@/components/MultiSelect/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

export interface TypeOption {
  value: number
  label: string
}

const props = defineProps({ disabled: Boolean })
const emit = defineEmits<{
  (e: 'on-submit', payload: Omit<OptionItem, 'pk' | 'project'>): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const getTypes = inject<TypeOption[]>('getTypes')

const refAlertModal = ref()
const refConfirmModal = ref()

const toNullableNumber = (val: number | '' | null | undefined): number | null =>
  val !== null && val !== undefined && val !== '' ? Number(val) : null

const validated = ref(false)
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

watch(
  () => props.disabled,
  newVal => {
    if (newVal) resetForm()
  },
)

// 계약금 + 잔금의 합계가 옵션가격과 일치해야 함 (둘 다 입력된 경우)
const isDepositBalanceValid = computed(() => {
  const price = toNullableNumber(form.opt_price)
  const deposit = toNullableNumber(form.opt_deposit)
  const balance = toNullableNumber(form.opt_balance)
  if (price !== null && deposit !== null && balance !== null) {
    return deposit + balance === price
  }
  return true
})

const isFormValid = computed(() => {
  const hasTypes = form.types.length > 0
  const hasName = Boolean(form.opt_name.trim())
  const price = toNullableNumber(form.opt_price)
  const deposit = toNullableNumber(form.opt_deposit)
  const balance = toNullableNumber(form.opt_balance)
  const hasPrice = price !== null && price >= 0
  const depositValid = deposit === null || deposit >= 0
  const balanceValid = balance === null || balance >= 0

  return (
    hasTypes && hasName && hasPrice && depositValid && balanceValid && isDepositBalanceValid.value
  )
})

const onSubmit = (event: Event) => {
  if (canProjectUpdate.value) {
    if (isValidate(event) || !isFormValid.value) {
      validated.value = true
    } else {
      refConfirmModal.value.callModal()
    }
  } else {
    refAlertModal.value.callModal()
    resetForm()
  }
}

const modalAction = () => {
  const price = toNullableNumber(form.opt_price)
  if (price === null) return

  emit('on-submit', {
    types: [...form.types],
    opt_code: form.opt_code.trim() || null,
    opt_name: form.opt_name.trim(),
    opt_desc: form.opt_desc.trim() || null,
    opt_maker: form.opt_maker.trim() || null,
    opt_price: price,
    opt_deposit: toNullableNumber(form.opt_deposit),
    opt_balance: toNullableNumber(form.opt_balance),
  })
  validated.value = false
  refConfirmModal.value.close()
  resetForm()
}

const resetForm = () => {
  form.types = []
  form.opt_code = ''
  form.opt_name = ''
  form.opt_desc = ''
  form.opt_maker = ''
  form.opt_price = null
  form.opt_deposit = null
  form.opt_balance = null
  validated.value = false
}
</script>

<template>
  <CForm novalidate class="needs-validation" :validated="validated" @submit.prevent="onSubmit">
    <CRow class="p-2">
      <CCol lg="6" xl="3">
        <CRow>
          <CCol lg="12" xl="7" class="mb-2">
            <Multiselect
              v-model="form.types"
              :options="getTypes || []"
              placeholder="타입구분"
              required
              :invalid="validated && form.types.length === 0"
              :disabled="disabled"
            />
            <div v-if="validated && form.types.length === 0" class="text-danger small mt-1">
              적용 타입을 선택하세요.
            </div>
          </CCol>

          <CCol lg="12" xl="5" class="mb-2">
            <CFormInput
              v-model="form.opt_code"
              maxlength="20"
              placeholder="품목 코드"
              :disabled="disabled"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="6" xl="3">
        <CRow>
          <CCol lg="12" xl="6" class="mb-2">
            <CFormInput
              v-model="form.opt_name"
              maxlength="100"
              placeholder="품목 이름"
              required
              :disabled="disabled"
            />
            <CFormFeedback invalid> 유상 옵션 품목 이름을 입력하세요.</CFormFeedback>
          </CCol>

          <CCol lg="12" xl="6" class="mb-2">
            <CFormInput
              v-model="form.opt_desc"
              maxlength="200"
              placeholder="세부 옵션"
              :disabled="disabled"
            />
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="12" xl="5">
        <CRow>
          <CCol lg="6" xl="3" class="mb-2">
            <CFormInput v-model="form.opt_maker" placeholder="제조사" :disabled="disabled" />
          </CCol>
          <CCol lg="6" xl="3" class="mb-2">
            <CFormInput
              v-model.number="form.opt_price"
              placeholder="옵션 가격"
              type="number"
              min="0"
              required
              :disabled="disabled"
            />
            <CFormFeedback invalid> 유상 옵션 금액을 입력하세요.</CFormFeedback>
          </CCol>

          <CCol lg="6" xl="3" class="mb-2">
            <CFormInput
              v-model.number="form.opt_deposit"
              placeholder="계약금"
              type="number"
              min="0"
              :disabled="disabled"
            />
          </CCol>

          <CCol lg="6" xl="3" class="mb-2">
            <CFormInput
              v-model.number="form.opt_balance"
              placeholder="잔금"
              type="number"
              min="0"
              :disabled="disabled"
            />
            <div v-if="!isDepositBalanceValid" class="text-danger small mt-1">
              계약금 + 잔금의 합계가 옵션 가격과 일치해야 합니다.
            </div>
          </CCol>
        </CRow>
      </CCol>

      <CCol lg="12" xl="1">
        <CCol lg="12" class="d-grid gap-2 d-lg-block mb-3 text-center">
          <v-btn color="primary" type="submit" :disabled="disabled || !isFormValid">
            옵션추가
          </v-btn>
        </CCol>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 옵션 정보 등록</template>
    <template #default> 이 유상 옵션 정보 등록을 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
