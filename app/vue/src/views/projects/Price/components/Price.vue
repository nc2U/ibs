<script lang="ts" setup>
import { computed, inject, onMounted, onUpdated, type PropType, reactive, ref, watch } from 'vue'
import { numFormat } from '@/utils/baseMixins.ts'
import { useAccount } from '@/store/pinia/account'
import type { PayOrder, Price } from '@/store/types/payment'
import { type UnitFloorType } from '@/store/types/project'
import { btnLight } from '@/utils/cssMixins.ts'
import { write_project } from '@/utils/pageAuth'
import type { PriceFilter } from '@/store/pinia/payment.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import PaymentPerInstallment from './PaymentPerInstallment.vue'

const condTexts = inject<{ orderText: string; typeText: string }>('condTexts')

const props = defineProps({
  floor: { type: Object as PropType<UnitFloorType>, required: true },
  pFilters: { type: Object as PropType<PriceFilter>, default: null },
  price: { type: Object as PropType<Price>, default: null },
  payOrders: { type: Array as PropType<PayOrder[]>, default: () => [] },
})

const emit = defineEmits(['on-create', 'on-update', 'on-delete', 'payment-changed'])

const refFormModal = ref()
const refConfirmModal = ref()
const refAlertModal = ref()

const form = reactive({
  price_build: null as number | null,
  price_land: null as number | null,
  price_tax: null as number | null,
  price: null as number | null,
})

watch(form, val => {
  if (!val.price_build) form.price_build = null
  if (!val.price_land) form.price_land = null
  if (!val.price_tax) form.price_tax = null
  if (!val.price) form.price = null
})

watch(props, val => {
  if (val.price) dataSetup()
})

const btnColor = computed(() => (props.price ? 'success' : 'primary'))
const btnTitle = computed(() => (props.price ? '수정' : '등록'))

// PaymentPerInstallment 토글 상태
const showPaymentDetails = ref(false)

// 테이블 총 컬럼 수 (write_project 권한에 따라 달라짐)
const totalColumns = computed(() => {
  return write_project.value ? 7 : 5 // 기본 5개 + 관리 2개 컬럼
})

const formsCheck = computed(() => {
  if (props.price) {
    const a = form.price_build === props.price.price_build
    const b = form.price_land === props.price.price_land
    const c = form.price_tax === props.price.price_tax
    const d = form.price === props.price.price || !props.price
    return a && b && c && d
  } else {
    return !form.price_build && !form.price_land && !form.price_tax && !form.price
  }
})

const onStorePrice = () => {
  if (write_project.value) {
    const payload = {
      ...props.pFilters,
      ...{ unit_floor_type: props.floor?.pk },
      ...form,
    }
    if (!props.price) emit('on-create', payload)
    else {
      const updatePayload = { ...{ pk: props.price.pk }, ...payload }
      emit('on-update', updatePayload)
    }
  } else refAlertModal.value.callModal()
}

const deletePrice = () => {
  if (useAccount().superAuth) refConfirmModal.value.callModal()
  else refAlertModal.value.callModal()
}
const modalAction = () => {
  emit('on-delete', props.price?.pk)
  refConfirmModal.value.close()
  dataReset()
}

const dataSetup = () => {
  if (props.price) {
    form.price_build = props.price.price_build
    form.price_land = props.price.price_land
    form.price_tax = props.price.price_tax
    form.price = props.price.price
  }
}

const dataReset = () => {
  form.price_build = null
  form.price_land = null
  form.price_tax = null
  form.price = null
}

const togglePaymentDetails = () => {
  showPaymentDetails.value = !showPaymentDetails.value
}

const onPaymentChanged = () => {
  // PaymentPerInstallment 데이터 변경 시 상위 컴포넌트에 알림
  emit('payment-changed')
}

onMounted(() => dataSetup())
onUpdated(() => {
  dataReset()
  dataSetup()
})
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
        @keydown.enter="onStorePrice"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.price_land"
        type="number"
        min="0"
        placeholder="타입별 대지가"
        @keydown.enter="onStorePrice"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.price_tax"
        type="number"
        min="0"
        placeholder="타입별 부가세"
        @keydown.enter="onStorePrice"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model.number="form.price"
        type="number"
        min="0"
        placeholder="타입별 공급가격"
        @keydown.enter="onStorePrice"
      />
    </CTableDataCell>
    <CTableDataCell v-if="write_project" class="text-center pt-3">
      <v-btn :color="btnColor" size="x-small" :disabled="formsCheck" @click="onStorePrice">
        {{ btnTitle }}
      </v-btn>
      <v-btn color="warning" size="x-small" :disabled="!price" @click="deletePrice"> 삭제</v-btn>
    </CTableDataCell>
    <CTableDataCell v-if="write_project" class="text-center pt-3">
      <v-btn
        :color="showPaymentDetails ? 'warning' : 'info'"
        size="x-small"
        class="mr-1"
        @click="togglePaymentDetails"
        :disabled="!price"
      >
        {{ showPaymentDetails ? '접기' : '보기' }}
      </v-btn>
      <v-btn color="primary" size="x-small" @click="refFormModal.callModal()"> 추가</v-btn>
    </CTableDataCell>
  </CTableRow>

  <!-- PaymentPerInstallment 확장 행 -->
  <CTableRow v-show="showPaymentDetails && price" class="payment-detail-row">
    <CTableDataCell :colspan="totalColumns" class="pa-0">
      <PaymentPerInstallment
        v-if="price && showPaymentDetails"
        :sales-price-id="price.pk"
        :project-id="pFilters.project as number"
        :pay-orders="payOrders"
        @created="onPaymentChanged"
        @updated="onPaymentChanged"
        @deleted="onPaymentChanged"
      />
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="refFormModal">
    <template #header>특별약정 추가</template>
    <template #default>
      <CForm>
        <CModalBody class="text-body">
          <CRow class="mb-3">
            <CFormLabel for="inputEmail3" class="col-sm-4 col-form-label">기준 공급가</CFormLabel>
            <CCol sm="8" class="pt-2">
              <span class="text-primary bold">{{ numFormat(price.price) }} </span>
              ({{ condTexts?.orderText }} / {{ condTexts?.typeText }} / {{ floor.alias_name }})
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="inputEmail3" class="col-sm-4 col-form-label">지정 납부회차</CFormLabel>
            <CCol sm="8">
              <CFormSelect>
                <option value="">---------</option>
                <option v-for="po in payOrders" :value="po?.pk as number" :key="po?.pk as number">
                  {{ po.pay_name }}
                </option>
              </CFormSelect>
            </CCol>
          </CRow>
          <CRow class="mb-3">
            <CFormLabel for="inputPassword3" class="col-sm-4 col-form-label">
              납부 약정금액
            </CFormLabel>
            <CCol sm="8">
              <CFormInput
                type="number"
                placeholder="특별 지정 납부 약정금액"
                text="일반 납부회차의 경우 기준 공급가 * 회당 납부비율을 적용 하나, 이 데이터 등록 시 예외적으로 이 데이터를 우선 적용함"
              />
            </CCol>
          </CRow>
        </CModalBody>
        <CModalFooter>
          <v-btn :color="btnLight" size="small" @click="refFormModal.close()"> 닫기</v-btn>
          <v-btn color="primary" size="small">확인</v-btn>
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
  background-color: #f8f9fa;
}

.payment-detail-row td {
  border-top: 1px solid #dee2e6;
  border-bottom: 1px solid #dee2e6;
}
</style>
