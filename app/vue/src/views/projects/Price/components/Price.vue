<script lang="ts" setup>
import { computed, inject, type PropType, reactive, ref, watch } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { useAccount } from '@/store/pinia/account'
import type {
  PaymentPerInstallment as PayInstallType,
  PaymentPerInstallmentPayload,
  PayOrder,
  Price,
  PriceFilter,
} from '@/store/types/payment'
import type { UnitFloorType } from '@/store/types/project'
import { usePayment } from '@/store/pinia/payment'
import { usePerms } from '@/composables/usePerms'
import PaymentPerInstallment from './PaymentPerInstallment.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import FormModal from '@/components/Modals/FormModal.vue'

const condTexts = inject<{ orderText: string; typeText: string }>('condTexts')

const props = defineProps({
  floor: { type: Object as PropType<UnitFloorType>, required: true },
  pFilters: { type: Object as PropType<PriceFilter>, default: null },
  price: { type: Object as PropType<Price>, default: null },
  payOrders: { type: Array as PropType<PayOrder[]>, default: () => [] },
})

const emit = defineEmits<{
  (e: 'on-create', payload: Price): void
  (e: 'on-update', payload: Price): void
  (e: 'on-delete', pk: number): void
  (e: 'payment-changed'): void
}>()

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))
const isSuperAuth = computed(() => useAccount().superAuth)

const refFormModal = ref()
const refConfirmModal = ref()
const refAlertModal = ref()

const form = reactive({
  price_build: null as number | '' | null,
  price_land: null as number | '' | null,
  price_tax: null as number | '' | null,
  price: null as number | '' | null,
})

const toNullableNumber = (val: number | '' | null | undefined) =>
  val !== null && val !== undefined && val !== '' ? Number(val) : null

const confirmModalType = ref<'price' | 'payment'>('price')

const payStore = usePayment()
const { createPaymentPerInstallment, updatePaymentPerInstallment, deletePaymentPerInstallment } =
  payStore

const dataSetup = () => {
  if (props.price) {
    form.price_build = props.price.price_build ?? null
    form.price_land = props.price.price_land ?? null
    form.price_tax = props.price.price_tax ?? null
    form.price = props.price.price ?? null
  } else {
    dataReset()
  }
}

const dataReset = () => {
  form.price_build = null
  form.price_land = null
  form.price_tax = null
  form.price = null
}

watch(
  () => props.price,
  () => dataSetup(),
  { deep: true, immediate: true },
)

const onComponentPriceChange = () => {
  const b = toNullableNumber(form.price_build)
  const l = toNullableNumber(form.price_land)
  const t = toNullableNumber(form.price_tax)
  if (b !== null || l !== null || t !== null) {
    form.price = (b || 0) + (l || 0) + (t || 0)
  } else {
    form.price = null
  }
}

const areNumbersEqual = (a: number | '' | null | undefined, b: number | '' | null | undefined) =>
  toNullableNumber(a) === toNullableNumber(b)

const isUnchanged = computed(() => {
  if (!props.price) return false
  const a = areNumbersEqual(form.price_build, props.price.price_build)
  const b = areNumbersEqual(form.price_land, props.price.price_land)
  const c = areNumbersEqual(form.price_tax, props.price.price_tax)
  const d = areNumbersEqual(form.price, props.price.price)
  return a && b && c && d
})

const isFormValid = computed(() => {
  return (
    form.price !== null && form.price !== undefined && form.price !== '' && Number(form.price) > 0
  )
})

const formsCheck = computed(() => {
  if (!canProjectUpdate.value) return true
  if (!isFormValid.value) return true
  if (props.price) return isUnchanged.value
  return false
})

const btnColor = computed(() => (props.price ? 'success' : 'primary'))
const btnTitle = computed(() => (props.price ? '수정' : '등록'))

// PaymentPerInstallment 토글 상태
const showPaymentDetails = ref(false)

// 테이블 총 컬럼 수 (canProjectUpdate 권한에 따라 달라짐)
const totalColumns = computed(() => (canProjectUpdate.value ? 9 : 7))

const onStorePrice = () => {
  if (formsCheck.value) return

  if (canProjectUpdate.value) {
    const payload: Price = {
      project: Number(props.pFilters?.project),
      order_group: Number(props.pFilters?.order_group),
      unit_type: Number(props.pFilters?.unit_type),
      unit_floor_type: props.floor.pk,
      price_build: toNullableNumber(form.price_build),
      price_land: toNullableNumber(form.price_land),
      price_tax: toNullableNumber(form.price_tax),
      price: Number(form.price),
    }
    if (!props.price) emit('on-create', payload)
    else {
      emit('on-update', { pk: props.price.pk, ...payload })
    }
  } else refAlertModal.value.callModal()
}

const deletePrice = () => {
  if (isSuperAuth.value) {
    confirmModalType.value = 'price'
    refConfirmModal.value.callModal(
      '공급가격 삭제',
      '해당 데이터를 삭제하면 이후 복구할 수 없습니다. 이 공급가격 정보를 삭제 하시겠습니까?',
      '',
      'warning',
      '삭제',
      'warning',
    )
  } else {
    refAlertModal.value.callModal()
  }
}

const modalAction = async () => {
  try {
    if (confirmModalType.value === 'price') {
      if (props.price?.pk) {
        emit('on-delete', props.price.pk)
      }
    } else if (confirmModalType.value === 'payment' && paymentEditId.value) {
      await deletePaymentPerInstallment(paymentEditId.value, props.price?.pk as number)
      refPaymentPerInstallment.value?.loadData()
      emit('payment-changed')
    }
    refConfirmModal.value.close()
  } catch (error) {
    console.error('Delete operation failed:', error)
  }
}

// -------------------------------------------------------- //

const refPaymentPerInstallment = ref()

// PaymentPerInstallment form
const paymentForm = reactive<Partial<PaymentPerInstallmentPayload>>({
  sales_price: undefined,
  pay_order: null,
  amount: null,
})

const paymentEditMode = ref(false)
const paymentEditId = ref<number | null>(null)

// 현재 Price 레코드에서 사용된 pay_order ID들 (로컬 상태)
const localUsedPayOrderIds = ref<number[]>([])

const togglePaymentDetails = () => (showPaymentDetails.value = !showPaymentDetails.value)

// PaymentPerInstallment 관련 함수들
const availablePayOrders = computed(() => {
  const filteredOrders = props.payOrders.filter(
    order => order.pay_sort && !['2', '3'].includes(order.pay_sort),
  )

  if (paymentEditMode.value) return filteredOrders

  return filteredOrders.filter(order => order.pk && !localUsedPayOrderIds.value.includes(order.pk))
})

const handleUsedPayOrdersChanged = (usedIds: number[]) => {
  localUsedPayOrderIds.value = usedIds
}

const handlePaymentCreate = () => {
  if (!canProjectUpdate.value) {
    refAlertModal.value.callModal()
    return
  }
  paymentEditMode.value = false
  paymentEditId.value = null
  resetPaymentForm()
  refFormModal.value.callModal()
}

const handlePaymentEdit = (item: PayInstallType) => {
  if (!canProjectUpdate.value) {
    refAlertModal.value.callModal()
    return
  }
  paymentEditMode.value = true
  paymentEditId.value = item.pk
  paymentForm.pay_order = item.pay_order
  paymentForm.amount = item.amount
  refFormModal.value.callModal()
}

const handlePaymentDelete = (item: PayInstallType) => {
  if (!isSuperAuth.value) {
    refAlertModal.value.callModal()
    return
  }
  confirmModalType.value = 'payment'
  paymentEditId.value = item.pk
  refConfirmModal.value.callModal(
    '특별 약정금액 삭제',
    `'${item.pay_order_info?.pay_name}' 특별 약정금액을 삭제하시겠습니까?`,
    '',
    'warning',
    '삭제',
    'warning',
  )
}

const resetPaymentForm = () => {
  paymentForm.sales_price = props.price?.pk || undefined
  paymentForm.pay_order = null
  paymentForm.amount = null
}

const paymentFormsCheck = computed(() => {
  const amt = paymentForm.amount as number | '' | null | undefined
  return (
    Boolean(paymentForm.pay_order) &&
    amt !== null &&
    amt !== undefined &&
    amt !== '' &&
    Number(amt) > 0
  )
})

const handlePaymentModalAction = async () => {
  if (!paymentFormsCheck.value || !canProjectUpdate.value) return

  try {
    if (paymentEditMode.value && paymentEditId.value) {
      const payload: PaymentPerInstallmentPayload = {
        pk: paymentEditId.value,
        sales_price: props.price?.pk as number,
        pay_order: paymentForm.pay_order as number,
        amount: paymentForm.amount as number,
      }
      await updatePaymentPerInstallment(payload)
    } else {
      const payload: PaymentPerInstallmentPayload = {
        sales_price: props.price?.pk as number,
        pay_order: paymentForm.pay_order as number,
        amount: paymentForm.amount as number,
      }
      await createPaymentPerInstallment(payload)
    }

    refFormModal.value.close()
    paymentEditMode.value = false
    paymentEditId.value = null
    resetPaymentForm()

    refPaymentPerInstallment.value?.loadData()
    emit('payment-changed')
  } catch (error: unknown) {
    const errData = (error as { response?: { data?: { non_field_errors?: string[] } } })?.response
      ?.data
    if (errData?.non_field_errors?.length) {
      const errorMessage = errData.non_field_errors[0]
      if (errorMessage.includes('고유해야 합니다')) {
        refAlertModal.value.callModal(
          '중복 등록 오류',
          '해당 납부 회차에 대한 특별 약정금액이 이미 존재합니다.',
        )
      } else refAlertModal.value.callModal('오류', errorMessage, '', 'danger')
    } else {
      refAlertModal.value.callModal(
        '오류',
        '특별 약정금액 처리 중 오류가 발생했습니다.',
        '',
        'danger',
      )
    }
  }
}
</script>

<template>
  <CTableRow>
    <CTableDataCell class="text-center">
      {{ condTexts?.orderText }}
    </CTableDataCell>
    <CTableDataCell class="text-center">
      {{ condTexts?.typeText }}
    </CTableDataCell>
    <CTableDataCell>
      {{ floor.alias_name }}
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model.number="form.price_build"
        type="number"
        min="0"
        placeholder="타입별 건물가"
        :disabled="!canProjectUpdate"
        @update:model-value="onComponentPriceChange"
        @keydown.enter.prevent="onStorePrice"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.price_land"
        type="number"
        min="0"
        placeholder="타입별 대지가"
        :disabled="!canProjectUpdate"
        @update:model-value="onComponentPriceChange"
        @keydown.enter.prevent="onStorePrice"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.price_tax"
        type="number"
        min="0"
        placeholder="타입별 부가세"
        :disabled="!canProjectUpdate"
        @update:model-value="onComponentPriceChange"
        @keydown.enter.prevent="onStorePrice"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.price"
        type="number"
        min="0"
        placeholder="타입별 공급가격"
        :disabled="!canProjectUpdate"
        required
        @keydown.enter.prevent="onStorePrice"
      />
    </CTableDataCell>
    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn :color="btnColor" size="x-small" :disabled="formsCheck" @click="onStorePrice">
        {{ btnTitle }}
      </v-btn>
      <v-btn color="warning" size="x-small" class="ms-1" :disabled="!price" @click="deletePrice">
        삭제
      </v-btn>
    </CTableDataCell>
    <CTableDataCell v-if="canProjectUpdate" class="text-center pt-3">
      <v-btn
        :color="showPaymentDetails ? 'secondary' : 'info'"
        size="x-small"
        class="me-1"
        :disabled="!price"
        @click="togglePaymentDetails"
      >
        {{ showPaymentDetails ? '접기' : '보기' }}
      </v-btn>
      <v-btn
        color="primary"
        size="x-small"
        :disabled="!price || !availablePayOrders.length"
        @click="handlePaymentCreate"
      >
        추가
      </v-btn>
    </CTableDataCell>
  </CTableRow>

  <!-- PaymentPerInstallment 확장 행 -->
  <CTableRow v-show="showPaymentDetails && price" class="payment-detail-row">
    <CTableDataCell :colspan="totalColumns" class="pa-0">
      <PaymentPerInstallment
        ref="refPaymentPerInstallment"
        v-if="price && showPaymentDetails"
        :key="`payment-per-installment-${price.pk}`"
        :project-id="pFilters.project as number"
        :sales-price-id="price.pk as number"
        :pay-orders="payOrders"
        @create-requested="handlePaymentCreate"
        @edit-requested="handlePaymentEdit"
        @delete-requested="handlePaymentDelete"
        @used-pay-orders-changed="handleUsedPayOrdersChanged"
      />
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="refFormModal">
    <template #header>
      {{ paymentEditMode ? '특별 약정금액 수정' : '특별 약정금액 등록' }}
    </template>
    <template #default>
      <CForm>
        <CModalBody class="text-body">
          <CRow class="mb-3">
            <CFormLabel class="col-sm-4 col-form-label">기준 공급가</CFormLabel>
            <CCol sm="8" class="pt-2">
              <span class="text-primary bold">{{ numFormat(price?.price || 0) }} </span>
              ({{ condTexts?.orderText }} / {{ condTexts?.typeText }} / {{ floor.alias_name }})
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel class="col-sm-4 col-form-label">지정 납부회차 *</CFormLabel>
            <CCol sm="8">
              <CFormSelect v-model="paymentForm.pay_order" :disabled="paymentEditMode">
                <option value="">---------</option>
                <option
                  v-for="po in availablePayOrders"
                  :value="po?.pk as number"
                  :key="po?.pk as number"
                >
                  {{ po.pay_name }}
                </option>
              </CFormSelect>
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel class="col-sm-4 col-form-label">납부 약정금액 *</CFormLabel>
            <CCol sm="8">
              <CFormInput
                v-model.number="paymentForm.amount"
                type="number"
                min="0"
                placeholder="특별 지정 납부 약정금액"
                text="일반 납부회차의 경우 기준 공급가 * 회당 납부비율을 적용 하나, 이 데이터 등록 시 예외적으로 이 데이터를 우선 적용함"
              />
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn
            color="primary"
            size="small"
            :disabled="!paymentFormsCheck"
            @click="handlePaymentModalAction"
          >
            확인
          </v-btn>
          <v-btn color="light" size="small" @click="refFormModal.close()" flat> 닫기</v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 공급가격 삭제</template>
    <template #default>
      해당 데이터를 삭제하면 이후 복구할 수 없습니다. 이 공급가격 정보를 삭제 하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>

<style scoped>
.payment-detail-row {
  background-color: var(--bs-tertiary-bg);
}

.payment-detail-row td {
  border-top: 1px solid var(--bs-border-color);
  border-bottom: 1px solid var(--bs-border-color);
}
</style>
