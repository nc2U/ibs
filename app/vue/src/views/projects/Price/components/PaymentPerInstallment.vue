<script lang="ts" setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import type { PaymentPerInstallment, PayOrder } from '@/store/types/payment'
import { usePayment } from '@/store/pinia/payment'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps<{
  salesPriceId: number
  projectId: number
  payOrders: PayOrder[]
}>()

const emit = defineEmits<{
  created: []
  updated: []
  deleted: []
}>()

const refFormModal = ref()
const refConfirmModal = ref()
const refAlertModal = ref()

const payStore = usePayment()
const {
  paymentPerInstallmentList,
  fetchPaymentPerInstallmentList,
  createPaymentPerInstallment,
  updatePaymentPerInstallment,
  deletePaymentPerInstallment,
} = payStore

// Form data
const form = reactive<Partial<PaymentPerInstallment>>({
  sales_price: props.salesPriceId,
  pay_order: null,
  amount: null,
})

const editMode = ref(false)
const editId = ref<number | null>(null)

// Available pay orders (filtering out 중도금=2, 잔금=3)
const availablePayOrders = computed(() =>
  props.payOrders.filter(order => order.pay_sort && !['2', '3'].includes(order.pay_sort)),
)

// Load data on mount
onMounted(() => {
  loadData()
})

watch(
  () => props.salesPriceId,
  () => {
    if (props.salesPriceId) {
      loadData()
    }
  },
)

const loadData = async () => {
  if (props.salesPriceId) {
    await fetchPaymentPerInstallmentList({ sales_price: props.salesPriceId })
  }
}

const openCreateModal = () => {
  editMode.value = false
  editId.value = null
  resetForm()
  refFormModal.value.modalOpen()
}

const openEditModal = (item: PaymentPerInstallment) => {
  editMode.value = true
  editId.value = item.pk
  form.pay_order = item.pay_order
  form.amount = item.amount
  refFormModal.value.modalOpen()
}

const resetForm = () => {
  form.sales_price = props.salesPriceId
  form.pay_order = null
  form.amount = null
}

const formsCheck = computed(() => {
  return form.pay_order && form.amount && form.amount > 0
})

const modalAction = async () => {
  if (!formsCheck.value) {
    refAlertModal.value.alertOpen('', '필수 항목을 모두 입력해주세요.', 'warning')
    return
  }

  try {
    const payload = {
      ...form,
      pk: editId.value,
      sales_price: props.salesPriceId,
    } as PaymentPerInstallment

    if (editMode.value && editId.value) {
      await updatePaymentPerInstallment(payload)
      emit('updated')
    } else {
      await createPaymentPerInstallment(payload)
      emit('created')
    }

    refFormModal.value.modalClose()
    resetForm()
  } catch (error) {
    console.error('Error saving payment per installment:', error)
  }
}

const confirmDelete = (item: PaymentPerInstallment) => {
  editId.value = item.pk
  refConfirmModal.value.confirmOpen(
    '',
    `'${item.pay_order_info?.pay_name}' 특별 약정금액을 삭제하시겠습니까?`,
    'warning',
  )
}

const deleteAction = async () => {
  if (editId.value) {
    await deletePaymentPerInstallment(editId.value, props.salesPriceId)
    emit('deleted')
    editId.value = null
  }
}

const getPayOrderName = (payOrderId: number) => {
  const payOrder = availablePayOrders.value.find(order => order.pk === payOrderId)
  return payOrder ? payOrder.pay_name : '알 수 없음'
}
</script>

<template>
  <v-card flat>
    <v-card-title class="d-flex justify-space-between align-center py-2">
      <span class="text-subtitle-2">특별 약정금액 관리</span>
      <v-btn
        size="small"
        color="primary"
        @click="openCreateModal"
        :disabled="!availablePayOrders.length"
      >
        추가
      </v-btn>
    </v-card-title>

    <v-divider />

    <v-card-text class="pa-2">
      <div v-if="!availablePayOrders.length" class="text-center py-4 text-grey">
        사용 가능한 납부 회차가 없습니다.
      </div>

      <div v-else-if="!paymentPerInstallmentList.length" class="text-center py-4 text-grey">
        등록된 특별 약정금액이 없습니다.
      </div>

      <v-simple-table v-else dense class="text-caption">
        <template #default>
          <thead>
            <tr>
              <th width="30%">납부 회차</th>
              <th width="40%">약정금액</th>
              <th width="30%">관리</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in paymentPerInstallmentList" :key="item.pk">
              <td>
                {{ item.pay_order_info?.pay_name || getPayOrderName(item.pay_order as number) }}
              </td>
              <td class="text-right">{{ numFormat(item.amount as number) }}원</td>
              <td>
                <v-btn size="x-small" color="warning" class="mr-1" @click="openEditModal(item)">
                  수정
                </v-btn>
                <v-btn size="x-small" color="error" @click="confirmDelete(item)"> 삭제 </v-btn>
              </td>
            </tr>
          </tbody>
        </template>
      </v-simple-table>
    </v-card-text>

    <!-- Form Modal -->
    <FormModal
      ref="refFormModal"
      :title="editMode ? '특별 약정금액 수정' : '특별 약정금액 등록'"
      :width="500"
      :form-check="formsCheck"
      @modal-action="modalAction"
    >
      <template #default>
        <v-row dense>
          <v-col cols="12">
            <v-select
              v-model="form.pay_order"
              label="납부 회차 *"
              :items="availablePayOrders"
              item-title="pay_name"
              item-value="pk"
              outlined
              dense
              hide-details
              :disabled="editMode"
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model.number="form.amount"
              label="약정금액 *"
              type="number"
              outlined
              dense
              hide-details
              suffix="원"
            />
          </v-col>
        </v-row>
      </template>
    </FormModal>

    <!-- Confirm Modal -->
    <ConfirmModal ref="refConfirmModal" @confirm-action="deleteAction" />

    <!-- Alert Modal -->
    <AlertModal ref="refAlertModal" />
  </v-card>
</template>

<style scoped>
.v-simple-table {
  border: 1px solid #e0e0e0;
}

.v-simple-table th {
  background-color: #f5f5f5;
  font-weight: 600;
}

.v-simple-table tbody tr:hover {
  background-color: #f9f9f9;
}
</style>
