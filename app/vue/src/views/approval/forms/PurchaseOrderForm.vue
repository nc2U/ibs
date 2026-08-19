<script setup lang="ts">
import { computed, onMounted } from 'vue'

export interface PurchaseItem {
  name: string
  spec?: string
  quantity: number
  unit_price: number
  supply_price: number
  vat: number
}

const props = defineProps<{
  modelValue: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: Record<string, any>): void
}>()

const items = computed<PurchaseItem[]>(() => {
  return Array.isArray(props.modelValue.items) ? props.modelValue.items : []
})

const totalSupplyPrice = computed(() => {
  return items.value.reduce((sum, item) => sum + (Number(item.supply_price) || 0), 0)
})

const totalVat = computed(() => {
  return items.value.reduce((sum, item) => sum + (Number(item.vat) || 0), 0)
})

const totalAmount = computed(() => {
  return totalSupplyPrice.value + totalVat.value
})

const addItem = () => {
  const currentItems = [...items.value]
  currentItems.push({
    name: '',
    spec: '',
    quantity: 1,
    unit_price: 0,
    supply_price: 0,
    vat: 0,
  })
  emit('update:modelValue', {
    ...props.modelValue,
    items: currentItems,
    amount: totalAmount.value,
  })
}

const removeItem = (index: number) => {
  const currentItems = [...items.value]
  currentItems.splice(index, 1)
  const sumSupply = currentItems.reduce((sum, item) => sum + (Number(item.supply_price) || 0), 0)
  const sumVat = currentItems.reduce((sum, item) => sum + (Number(item.vat) || 0), 0)
  emit('update:modelValue', {
    ...props.modelValue,
    items: currentItems,
    amount: sumSupply + sumVat,
  })
}

const updateItem = (index: number, field: keyof PurchaseItem, val: any) => {
  const currentItems = [...items.value]
  const target = { ...currentItems[index] }

  if (field === 'quantity') {
    target.quantity = parseInt(val) || 0
    target.supply_price = target.quantity * target.unit_price
    target.vat = Math.round(target.supply_price * 0.1)
  } else if (field === 'unit_price') {
    target.unit_price = parseFloat(val) || 0
    target.supply_price = target.quantity * target.unit_price
    target.vat = Math.round(target.supply_price * 0.1)
  } else {
    (target as any)[field] = val
  }

  currentItems[index] = target
  const sumSupply = currentItems.reduce((sum, item) => sum + (Number(item.supply_price) || 0), 0)
  const sumVat = currentItems.reduce((sum, item) => sum + (Number(item.vat) || 0), 0)

  emit('update:modelValue', {
    ...props.modelValue,
    items: currentItems,
    amount: sumSupply + sumVat,
  })
}

const updateField = (key: string, val: any) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: val,
  })
}

onMounted(() => {
  if (!props.modelValue.items || props.modelValue.items.length === 0) {
    addItem()
  }
})
</script>

<template>
  <div class="purchase-order-form p-3 border rounded bg-light mb-3">
    <h6 class="fw-bold mb-3 text-info">
      <CIcon name="cilCart" class="me-1" />
      구매품의 상세 정보
    </h6>

    <!-- 기본 정보 -->
    <CRow class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label required">구매 목적</CFormLabel>
      <CCol sm="9">
        <CFormInput
          :value="modelValue.purpose ?? ''"
          placeholder="구매 목적 및 사유 (예: 신규 프로젝트 개발용 장비 구매)"
          required
          @input="updateField('purpose', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <CRow class="mb-3">
      <CFormLabel class="col-sm-3 col-form-label">납품 희망일</CFormLabel>
      <CCol sm="3">
        <CFormInput
          type="date"
          :value="modelValue.delivery_due_date ?? ''"
          @input="updateField('delivery_due_date', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
      <CFormLabel class="col-sm-2 col-form-label text-sm-end">납품 장소</CFormLabel>
      <CCol sm="4">
        <CFormInput
          :value="modelValue.delivery_location ?? ''"
          placeholder="예: 본사 4층 개발팀"
          @input="updateField('delivery_location', ($event.target as HTMLInputElement).value)"
        />
      </CCol>
    </CRow>

    <!-- 품목 리스트 그리드 -->
    <div class="mb-3">
      <div class="d-flex justify-content-between align-items-center mb-2">
        <label class="form-label fw-semibold mb-0 required">구매 품목 목록</label>
        <CButton color="info" size="sm" variant="outline" @click="addItem">
          <CIcon name="cilPlus" class="me-1" />품목 추가
        </CButton>
      </div>

      <CTable small bordered responsive class="bg-white mb-2">
        <CTableHead color="light">
          <CTableRow class="text-center">
            <CTableHeaderCell>품명</CTableHeaderCell>
            <CTableHeaderCell style="width: 140px">규격 / 모델명</CTableHeaderCell>
            <CTableHeaderCell style="width: 80px">수량</CTableHeaderCell>
            <CTableHeaderCell style="width: 120px">단가</CTableHeaderCell>
            <CTableHeaderCell style="width: 130px">공급가액</CTableHeaderCell>
            <CTableHeaderCell style="width: 100px">부가세</CTableHeaderCell>
            <CTableHeaderCell style="width: 50px">삭제</CTableHeaderCell>
          </CTableRow>
        </CTableHead>
        <CTableBody>
          <CTableRow v-for="(item, idx) in items" :key="idx">
            <CTableDataCell>
              <CFormInput
                size="sm"
                :value="item.name"
                placeholder="품목명"
                required
                @input="updateItem(idx, 'name', ($event.target as HTMLInputElement).value)"
              />
            </CTableDataCell>
            <CTableDataCell>
              <CFormInput
                size="sm"
                :value="item.spec ?? ''"
                placeholder="규격"
                @input="updateItem(idx, 'spec', ($event.target as HTMLInputElement).value)"
              />
            </CTableDataCell>
            <CTableDataCell>
              <CFormInput
                type="number"
                size="sm"
                class="text-end"
                :value="item.quantity"
                min="1"
                required
                @input="updateItem(idx, 'quantity', ($event.target as HTMLInputElement).value)"
              />
            </CTableDataCell>
            <CTableDataCell>
              <CFormInput
                type="number"
                size="sm"
                class="text-end"
                :value="item.unit_price"
                min="0"
                step="1000"
                required
                @input="updateItem(idx, 'unit_price', ($event.target as HTMLInputElement).value)"
              />
            </CTableDataCell>
            <CTableDataCell class="text-end align-middle fw-semibold">
              {{ (item.supply_price || 0).toLocaleString() }}
            </CTableDataCell>
            <CTableDataCell class="text-end align-middle text-muted">
              {{ (item.vat || 0).toLocaleString() }}
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

      <!-- 합계 요약 -->
      <div class="d-flex justify-content-end align-items-center gap-3 p-2 bg-white border rounded">
        <span class="text-muted">공급가액: <strong>{{ totalSupplyPrice.toLocaleString() }}</strong> 원</span>
        <span class="text-muted">+ 부가세: <strong>{{ totalVat.toLocaleString() }}</strong> 원</span>
        <span class="fs-5 fw-bold text-danger">= 총 합계: {{ totalAmount.toLocaleString() }} 원</span>
      </div>
    </div>
  </div>
</template>
