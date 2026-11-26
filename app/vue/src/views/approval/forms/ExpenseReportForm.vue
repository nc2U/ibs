<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import type { ApprovalContent } from '@/store/types/approval'
import { TableSecondary } from '@/utils/cssMixins'
import {
  EXPENSE_TYPE_OPTIONS,
  asList,
  asStr,
  getLocalToday,
  parseNonNegativeNumberInput,
} from '../utils/approvalMeta'

export interface ExpenseItem {
  date: string
  description: string
  amount: number | ''
  note?: string
}

const props = defineProps<{
  modelValue: ApprovalContent
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: ApprovalContent): void
}>()

const items = computed<ExpenseItem[]>(() => asList<ExpenseItem>(props.modelValue.items))

const paymentDueDate = computed({
  get: () => asStr(props.modelValue.payment_due_date),
  set: (val: string) => updateField('payment_due_date', val),
})

const calcExpenseTotal = (list: ExpenseItem[]) =>
  list.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)

const totalAmount = computed(() => calcExpenseTotal(items.value))

const addItem = () => {
  const currentItems = [...items.value]
  currentItems.push({
    date: getLocalToday(),
    description: '',
    amount: 0,
    note: '',
  })
  emit('update:modelValue', {
    ...props.modelValue,
    items: currentItems,
    amount: calcExpenseTotal(currentItems),
  })
}

const removeItem = (index: number) => {
  const currentItems = [...items.value]
  currentItems.splice(index, 1)
  emit('update:modelValue', {
    ...props.modelValue,
    items: currentItems,
    amount: calcExpenseTotal(currentItems),
  })
}

const updateItem = (index: number, field: keyof ExpenseItem, val: string | number) => {
  const currentItems = [...items.value]
  const current = currentItems[index]
  if (!current) return
  const strVal = String(val)
  const updatedItem: ExpenseItem = { ...current }
  if (field === 'amount') updatedItem.amount = parseNonNegativeNumberInput(strVal)
  else if (field === 'date') updatedItem.date = strVal
  else if (field === 'description') updatedItem.description = strVal
  else if (field === 'note') updatedItem.note = strVal

  currentItems[index] = updatedItem
  emit('update:modelValue', {
    ...props.modelValue,
    items: currentItems,
    amount: calcExpenseTotal(currentItems),
  })
}

const updateField = (key: string, val: unknown) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: val,
  })
}

onMounted(() => {
  if (items.value.length === 0) {
    addItem()
  }
})
</script>

<template>
  <div class="expense-report-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-success">
      <CIcon name="cilMoney" class="me-1" />
      지출결의 상세 명세
    </h6>

    <!-- 지출 기본 정보 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label required">지출 구분</CFormLabel>
      <CCol sm="3">
        <CFormSelect
          :value="asStr(modelValue.expense_type, 'CARD')"
          required
          @change="updateField('expense_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in EXPENSE_TYPE_OPTIONS" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">지급요청일</CFormLabel>
      <CCol sm="4">
        <DatePicker v-model="paymentDueDate" placeholder="지급요청일 선택" />
      </CCol>
    </CRow>

    <!-- 입금 계좌 정보 (계좌이체/세금계산서의 경우) -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label">입금 계좌</CFormLabel>
      <CCol sm="3">
        <CFormInput
          :value="asStr(modelValue.bank_name)"
          placeholder="은행명"
          @input="updateField('bank_name', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CCol sm="3">
        <CFormInput
          :value="asStr(modelValue.account_number)"
          placeholder="계좌번호"
          @input="updateField('account_number', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CCol sm="3">
        <CFormInput
          :value="asStr(modelValue.account_holder)"
          placeholder="예금주명"
          @input="updateField('account_holder', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 지출 내역 품목 테이블 -->
    <div class="mb-3">
      <div class="d-flex justify-content-between align-items-center mb-2">
        <label class="form-label fw-semibold mb-0 required">지출 항목별 내역</label>
        <CButton color="primary" size="sm" variant="outline" @click="addItem">
          <CIcon name="cilPlus" class="me-1" />항목 추가
        </CButton>
      </div>

      <CTable small bordered responsive class="bg-more-white mb-2">
        <CTableHead :color="TableSecondary">
          <CTableRow class="text-center">
            <CTableHeaderCell style="width: 140px">일자</CTableHeaderCell>
            <CTableHeaderCell>사용 내역 / 항목명</CTableHeaderCell>
            <CTableHeaderCell style="width: 150px">금액 (원)</CTableHeaderCell>
            <CTableHeaderCell style="width: 150px">비고</CTableHeaderCell>
            <CTableHeaderCell style="width: 50px">삭제</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow v-for="(item, idx) in items" :key="idx">
            <CTableDataCell>
              <DatePicker
                :model-value="item.date"
                required
                placeholder="일자 선택"
                @update:model-value="updateItem(idx, 'date', $event)"
              />
            </CTableDataCell>
            <CTableDataCell>
              <CFormInput
                size="sm"
                :value="item.description"
                placeholder="예: 부서 회식비, 사무용품 구매"
                required
                @input="updateItem(idx, 'description', ($event.target as HTMLInputElement).value)"
              />
            </CTableDataCell>
            <CTableDataCell>
              <CFormInput
                type="number"
                size="sm"
                class="text-end"
                :value="item.amount ?? 0"
                min="0"
                required
                @input="updateItem(idx, 'amount', ($event.target as HTMLInputElement).value)"
              />
            </CTableDataCell>
            <CTableDataCell>
              <CFormInput
                size="sm"
                :value="item.note ?? ''"
                placeholder="비고"
                @input="updateItem(idx, 'note', ($event.target as HTMLInputElement).value)"
              />
            </CTableDataCell>
            <CTableDataCell class="text-center">
              <CButton
                color="danger"
                variant="ghost"
                size="sm"
                :disabled="items.length <= 1"
                @click="removeItem(idx)"
              >
                <CIcon name="cilTrash" size="sm" />
              </CButton>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>

      <!-- 총 금액 합계 바 -->
      <div class="d-flex justify-content-end align-items-center p-2 bg-more-white border rounded">
        <span class="me-3 fw-semibold">총 지출 결의 금액:</span>
        <span class="fs-5 fw-bold text-danger">{{ totalAmount.toLocaleString() }} 원</span>
      </div>
    </div>
  </div>
</template>
