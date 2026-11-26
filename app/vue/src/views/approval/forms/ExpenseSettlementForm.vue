<script setup lang="ts">
import { computed, onMounted } from 'vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import type { ApprovalContent } from '@/store/types/approval'
import {
  EXPENSE_CATEGORIES,
  SETTLEMENT_TYPE_OPTIONS,
  asList,
  asStr,
  getLocalToday,
  parseNonNegativeNumberInput,
} from '../utils/approvalMeta'

export interface SettlementItem {
  date: string
  merchant: string
  category: string
  amount: number | ''
  purpose?: string
}

const props = defineProps<{
  modelValue: ApprovalContent
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: ApprovalContent): void
}>()

const items = computed<SettlementItem[]>(() => asList<SettlementItem>(props.modelValue.items))

const calcSettlementTotal = (list: SettlementItem[]) =>
  list.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)

const totalAmount = computed(() => calcSettlementTotal(items.value))

const updateField = (key: string, val: unknown) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: val,
  })
}

const addItem = () => {
  const currentItems = [...items.value]
  currentItems.push({
    date: getLocalToday(),
    merchant: '',
    category: '복리후생비(식대/음료)',
    amount: 0,
    purpose: '',
  })
  const newTotal = calcSettlementTotal(currentItems)
  emit('update:modelValue', {
    ...props.modelValue,
    items: currentItems,
    amount: newTotal,
    total_amount: newTotal,
  })
}

const removeItem = (index: number) => {
  const currentItems = [...items.value]
  currentItems.splice(index, 1)
  const newTotal = calcSettlementTotal(currentItems)
  emit('update:modelValue', {
    ...props.modelValue,
    items: currentItems,
    amount: newTotal,
    total_amount: newTotal,
  })
}

const updateItem = (index: number, field: keyof SettlementItem, val: string | number) => {
  const currentItems = [...items.value]
  const current = currentItems[index]
  if (!current) return
  const strVal = String(val)
  const updatedItem: SettlementItem = { ...current }
  if (field === 'amount') updatedItem.amount = parseNonNegativeNumberInput(strVal)
  else if (field === 'date') updatedItem.date = strVal
  else if (field === 'merchant') updatedItem.merchant = strVal
  else if (field === 'category') updatedItem.category = strVal
  else if (field === 'purpose') updatedItem.purpose = strVal

  currentItems[index] = updatedItem
  const newTotal = calcSettlementTotal(currentItems)
  emit('update:modelValue', {
    ...props.modelValue,
    items: currentItems,
    amount: newTotal,
    total_amount: newTotal,
  })
}

onMounted(() => {
  const initial: ApprovalContent = { ...props.modelValue }
  const today = getLocalToday()
  let changed = false

  if (!asStr(initial.settlement_type)) {
    initial.settlement_type = 'CORP_CARD'
    changed = true
  }
  if (!asStr(initial.target_month)) {
    initial.target_month = today.substring(0, 7) // YYYY-MM
    changed = true
  }
  if (!Array.isArray(initial.items) || initial.items.length === 0) {
    initial.items = [
      {
        date: today,
        merchant: '',
        category: '복리후생비(식대/음료)',
        amount: 0,
        purpose: '',
      },
    ]
    changed = true
  }

  if (changed) {
    emit('update:modelValue', initial)
  }
})
</script>

<template>
  <div class="expense-settlement-form p-3 border rounded bg-more-light mb-3">
    <h6 class="fw-bold mb-3 text-primary">
      <CIcon name="cilCreditCard" class="me-1" />
      경비 정산 기본 정보
    </h6>

    <!-- 정산 구분 & 귀속 연월 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">정산 구분</CFormLabel>
      <CCol sm="4">
        <CFormSelect
          :value="asStr(modelValue.settlement_type, 'CORP_CARD')"
          required
          @change="updateField('settlement_type', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="t in SETTLEMENT_TYPE_OPTIONS" :key="t.value" :value="t.value">
            {{ t.label }}
          </option>
        </CFormSelect>
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label required text-sm-end">귀속 연월</CFormLabel>
      <CCol sm="4">
        <CFormInput
          type="month"
          :value="asStr(modelValue.target_month)"
          required
          @input="updateField('target_month', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 법인카드 정보 (법인카드 정산 시) -->
    <CRow v-if="modelValue.settlement_type === 'CORP_CARD'" class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label">법인카드 정보</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="asStr(modelValue.card_number)"
          placeholder="사용 카드명 및 카드번호 뒤 4자리 (예: 국민 법인카드 5678)"
          @input="updateField('card_number', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 개인 환급 계좌 (개인경비 환급 청구 시) -->
    <CRow v-else-if="modelValue.settlement_type === 'PERSONAL_EXPENSE'" class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">환급 입금계좌</CFormLabel>
      <CCol sm="3">
        <CFormInput
          :value="asStr(modelValue.bank_name)"
          placeholder="은행명"
          required
          @input="updateField('bank_name', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CCol sm="4">
        <CFormInput
          :value="asStr(modelValue.account_number)"
          placeholder="계좌번호"
          required
          @input="updateField('account_number', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CCol sm="3">
        <CFormInput
          :value="asStr(modelValue.account_holder)"
          placeholder="예금주명"
          required
          @input="updateField('account_holder', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 정산 사유 / 설명 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-2 col-form-label required">정산 개요 / 사유</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="asStr(modelValue.reason)"
          placeholder="정산 사유 및 주요 사용 목적 (예: 2026년 8월 마케팅팀 법인카드 사용 내역 정산의 건)"
          required
          @input="updateField('reason', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 세부 영수증 사용 내역 그리드 -->
    <div class="card mb-3 border">
      <div class="card-header d-flex justify-content-between align-items-center bg-more-white py-2">
        <span class="fw-bold text-body">
          <CIcon name="cilList" class="me-1 text-primary" />
          세부 영수증 / 사용 내역 (총 {{ items.length }}건)
        </span>
        <CButton color="primary" size="sm" variant="outline" @click="addItem">
          <CIcon name="cilPlus" class="me-1" />항목 추가
        </CButton>
      </div>
      <div class="card-body p-2">
        <div class="table-responsive">
          <table class="table table-bordered table-sm mb-0 align-middle bg-more-white">
            <thead class="bg-more-light text-center small">
              <tr>
                <th style="width: 125px">사용일자</th>
                <th style="width: 160px">계정과목 (구분)</th>
                <th style="width: 180px">가맹점 / 사용처</th>
                <th style="width: 140px">금액 (원)</th>
                <th>사용 목적 / 참석자</th>
                <th style="width: 40px">삭제</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in items" :key="idx">
                <td>
                  <DatePicker
                    :model-value="item.date"
                    required
                    placeholder="일자 선택"
                    @update:model-value="updateItem(idx, 'date', $event)"
                  />
                </td>
                <td>
                  <CFormSelect
                    size="sm"
                    :value="item.category"
                    @change="
                      updateItem(idx, 'category', ($event.target as HTMLSelectElement).value)
                    "
                  >
                    <option v-for="cat in EXPENSE_CATEGORIES" :key="cat" :value="cat">
                      {{ cat }}
                    </option>
                  </CFormSelect>
                </td>
                <td>
                  <CFormInput
                    size="sm"
                    :value="item.merchant"
                    placeholder="가맹점명 (예: 스타벅스)"
                    required
                    @input="updateItem(idx, 'merchant', ($event.target as HTMLInputElement).value)"
                  />
                </td>
                <td>
                  <CFormInput
                    type="number"
                    size="sm"
                    class="text-end fw-semibold"
                    :value="item.amount ?? 0"
                    min="0"
                    required
                    @input="updateItem(idx, 'amount', ($event.target as HTMLInputElement).value)"
                  />
                </td>
                <td>
                  <CFormInput
                    size="sm"
                    :value="item.purpose ?? ''"
                    placeholder="용도 및 참석자 (예: 프로젝트 회의 다과, 4명)"
                    @input="updateItem(idx, 'purpose', ($event.target as HTMLInputElement).value)"
                  />
                </td>
                <td class="text-center">
                  <CButton
                    color="danger"
                    size="sm"
                    variant="ghost"
                    class="p-0"
                    :disabled="items.length <= 1"
                    @click="removeItem(idx)"
                  >
                    ×
                  </CButton>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 총 금액 합계 바 -->
        <div
          class="d-flex justify-content-end align-items-center p-2 mt-2 bg-more-light border rounded"
        >
          <span class="me-2 fw-semibold">총 정산 합계 금액:</span>
          <span class="fs-5 fw-bold text-danger">{{ totalAmount.toLocaleString() }} 원</span>
        </div>
      </div>
    </div>

    <!-- 비고 및 증빙 첨부 안내 -->
    <CRow class="mb-2">
      <CFormLabel class="col-sm-2 col-form-label">비고 / 증빙 안내</CFormLabel>
      <CCol sm="10">
        <CFormInput
          :value="asStr(modelValue.note)"
          placeholder="특이사항 또는 실물 영수증 제출 안내 (예: 종이영수증 총무팀 전달 완료)"
          @input="updateField('note', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>
  </div>
</template>
