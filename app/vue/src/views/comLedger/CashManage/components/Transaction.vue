<script lang="ts" setup>
import { computed, inject, ref, nextTick, type PropType } from 'vue'
import { useRouter } from 'vue-router'
import { cutString, diffDate, numFormat } from '@/utils/baseMixins'
import { write_company_cash } from '@/utils/pageAuth'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import type { BankTransaction, AccountingEntry } from '@/store/types/comLedger'
import { CTableRow } from '@coreui/vue'

const props = defineProps({
  transaction: { type: Object as PropType<BankTransaction>, required: true },
  calculated: { type: String, default: '2000-01-01' },
  isHighlighted: { type: Boolean, default: false },
})

const router = useRouter()
const ledgerStore = useComLedger()

const rowColor = computed(() => (props.isHighlighted ? 'warning' : ''))

const superAuth = inject('superAuth')
const allowedPeriod = computed(
  () =>
    (superAuth as any).value ||
    (write_company_cash && diffDate(props.transaction.deal_date, new Date(props.calculated)) <= 10),
)

// --- 제네릭 인라인 편집을 위한 상태 및 로직 ---
const editingState = ref<{ type: 'tran' | 'entry'; pk: number; field: string } | null>(null)
const editValue = ref<any>(null)
const inputRef = ref<HTMLInputElement | null>(null)

const setEditing = (type: 'tran' | 'entry', pk: number, field: string, value: any) => {
  if (!allowedPeriod.value) return
  editingState.value = { type, pk, field }
  editValue.value = value
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const isEditing = (type: 'tran' | 'entry', pk: number, field: string) => {
  return (
    editingState.value?.type === type &&
    editingState.value?.pk === pk &&
    editingState.value?.field === field
  )
}

const handleUpdate = async () => {
  if (!editingState.value) return

  const { type, pk, field } = editingState.value
  let originalValue: any

  if (type === 'tran') {
    originalValue = props.transaction[field as keyof BankTransaction]
  } else {
    const entry = props.transaction.accounting_entries?.find(e => e.pk === pk)
    if (entry) originalValue = entry[field as keyof AccountingEntry]
  }

  if (editValue.value === originalValue) {
    editingState.value = null
    return
  }

  const payload: { pk: number; [key: string]: any } = { pk: props.transaction.pk }

  if (type === 'tran') {
    payload[field] = editValue.value
  } else {
    payload.accounting_entries = [{ pk: pk, [field]: editValue.value }]
  }

  try {
    await ledgerStore.patchBankTransaction(payload)
  } finally {
    editingState.value = null
  }
}
</script>

<template>
  <template v-if="transaction">
    <CTableRow class="align-top" :color="rowColor" :data-cash-id="transaction.pk">
      <CTableDataCell style="padding-top: 12px">
        <span class="text-primary">{{ transaction.deal_date }}</span>
      </CTableDataCell>

      <!-- 비고 인라인 편집 -->
      <CTableDataCell
        :class="['editable-cell-hint', isEditing('tran', transaction.pk!, 'note') ? '' : 'pointer']"
        :style="
          isEditing('tran', transaction.pk!, 'note') ? 'padding-top: 10px' : 'padding-top: 12px'
        "
        @dblclick="setEditing('tran', transaction.pk!, 'note', transaction.note)"
      >
        <CFormInput
          v-if="isEditing('tran', transaction.pk!, 'note')"
          ref="inputRef"
          v-model="editValue"
          @blur="handleUpdate"
          @keydown.enter="handleUpdate"
          type="text"
          size="sm"
        />
        <span v-else>
          {{ cutString(transaction.note, 20) }}
          <v-icon icon="mdi-pencil-outline" size="14" color="success" class="inline-edit-icon" />
        </span>
      </CTableDataCell>

      <CTableDataCell style="padding-top: 12px">
        <span v-if="transaction.bank_account_name">
          {{ cutString(transaction.bank_account_name, 10) }}
        </span>
      </CTableDataCell>

      <!-- Content 인라인 편집 -->
      <CTableDataCell
        :class="[
          'truncate',
          'editable-cell-hint',
          isEditing('tran', transaction.pk!, 'content') ? '' : 'pointer',
        ]"
        :style="
          isEditing('tran', transaction.pk!, 'content') ? 'padding-top: 10px' : 'padding-top: 12px'
        "
        @dblclick="setEditing('tran', transaction.pk!, 'content', transaction.content)"
      >
        <CFormInput
          v-if="isEditing('tran', transaction.pk!, 'content')"
          ref="inputRef"
          v-model="editValue"
          @blur="handleUpdate"
          @keydown.enter="handleUpdate"
          type="text"
          size="sm"
        />
        <span v-else>
          {{ cutString(transaction.content, 15) }}
          <v-icon icon="mdi-pencil-outline" size="14" color="success" class="inline-edit-icon" />
        </span>
      </CTableDataCell>

      <CTableDataCell
        class="text-right"
        :class="transaction.sort === 1 ? 'text-success strong' : ''"
        style="padding-top: 12px"
      >
        {{ transaction.sort === 1 ? '+' : '-' }}{{ numFormat(transaction.amount || 0) }}
      </CTableDataCell>

      <CTableDataCell colspan="6" class="bg-yellow-lighten-5">
        <CTable small class="m-0 p-0">
          <colgroup>
            <col style="width: 20%" />
            <col style="width: 32%" />
            <col style="width: 16%" />
            <col style="width: 26%" />
            <col v-if="write_company_cash" style="width: 6%" />
          </colgroup>
          <CTableRow v-for="entry in transaction.accounting_entries" :key="entry.pk">
            <CTableDataCell>
              <div class="d-flex align-items-center bg-transparent">
                <span>{{ entry.account_name }}</span>
                <v-tooltip v-if="entry.affiliate" location="top">
                  <template v-slot:activator="{ props: tooltipProps }">
                    <v-icon
                      v-bind="tooltipProps"
                      icon="mdi-link-variant"
                      color="primary"
                      size="16"
                      class="ml-1"
                    />
                  </template>
                  <div class="pa-2">
                    <div class="font-weight-bold mb-1">관계회사/프로젝트</div>
                    <div>{{ entry.affiliate_display }}</div>
                  </div>
                </v-tooltip>
              </div>
            </CTableDataCell>
            <CTableDataCell> {{ cutString(entry.trader, 20) }} </CTableDataCell>
            <CTableDataCell
              class="text-right"
              :class="transaction.sort === 1 ? 'text-success strong' : ''"
            >
              {{ transaction.sort === 1 ? '+' : '-' }}{{ numFormat(entry.amount) }}
            </CTableDataCell>
            <CTableDataCell class="pl-3">
              {{ cutString(entry.evidence_type_display, 10) }}
            </CTableDataCell>
            <CTableDataCell v-if="write_company_cash" class="text-right pr-2">
              <v-icon
                v-if="allowedPeriod"
                icon="mdi-pencil"
                size="18"
                @click="
                  router.push({
                    name: '본사 거래 내역 - 수정',
                    params: { transId: transaction.pk },
                  })
                "
                class="pointer edit-icon-hover"
              />
            </CTableDataCell>
          </CTableRow>
        </CTable>
      </CTableDataCell>
    </CTableRow>
  </template>
</template>

<style scoped>
.editable-cell-hint {
  position: relative;
  align-items: center;
}
.inline-edit-icon {
  opacity: 0; /* Default hidden */
  margin-left: 4px;
  transition: opacity 0.2s ease;
}
.editable-cell-hint:hover .inline-edit-icon, /* Show on hover of the td with editable-cell-hint */
.inline-datepicker:hover .inline-edit-icon {
  opacity: 1;
}

/* 기본적으로 수정 아이콘 숨김 */
.edit-icon-hover {
  opacity: 0;
  transition: opacity 0.2s ease;
  background-color: transparent !important;
}

/* 내부 테이블 행에 hover 시 아이콘 표시 */
.table tbody tr:hover .edit-icon-hover {
  opacity: 1;
}

.dark-theme .bg-yellow-lighten-5 {
  background-color: #49473a !important;
  color: #fff !important;
}
</style>
