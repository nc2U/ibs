<script lang="ts" setup>
import { computed, type ComputedRef, inject, nextTick, type PropType, ref } from 'vue'
import { useRouter } from 'vue-router'
import { cutString, diffDate, numFormat } from '@/utils/baseMixins'
import { write_company_cash } from '@/utils/pageAuth'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import type { Account, AccountingEntry, BankTransaction } from '@/store/types/comLedger'
import LedgerAccountPicker from '@/components/LedgerAccount/Picker.vue'

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

const comAccounts = inject<ComputedRef<Account[]>>('comAccounts')
const affiliates = inject<ComputedRef<{ value: number; label: string }[]>>('affiliates')

// 선택된 account가 affiliate를 요구하는지 확인
const getAccountById = (accountId: number | null | undefined): Account | undefined => {
  if (!accountId || !comAccounts?.value) return undefined
  return comAccounts.value.find(acc => acc.value === accountId)
}

const sortType = computed(() => {
  if (props.transaction.sort === 1) return 'deposit' // 입금
  if (props.transaction.sort === 2) return 'withdraw' // 출금
  return null // 전체
})

// --- 제네릭 인라인 편집을 위한 상태 및 로직 ---
const editingState = ref<{ type: 'tran' | 'entry'; pk: number; field: string } | null>(null)
const editValue = ref<any>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const pickerPosition = ref<{ top: number; left: number; width: number } | null>(null)

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

const handleAccountClick = (entry: AccountingEntry, event: MouseEvent) => {
  event.stopPropagation()

  // 같은 항목 클릭 → 토글
  if (isEditing('entry', entry.pk!, 'account_affiliate')) {
    handlePickerClose()
    return
  }

  // body의 position이 fixed면 다른 Picker가 열려있음 → 닫고 return
  if (document.body.style.position === 'fixed') {
    // 다른 Picker 닫기 (스크롤 복원)
    const scrollY = document.body.style.top
    const scrollValue = scrollY ? parseInt(scrollY || '0') * -1 : 0

    document.body.style.position = ''
    document.body.style.top = ''
    window.scrollTo(0, scrollValue)
    document.documentElement.style.overflow = ''
    document.body.style.overflow = ''
    document.body.style.width = ''
    return
  }

  // 열려있는 창이 없으면 → 열기
  const target = event.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()

  pickerPosition.value = {
    top: rect.bottom,
    left: rect.left,
    width: rect.width,
  }

  setEditing('entry', entry.pk!, 'account_affiliate', {
    account: entry.account,
    affiliate: entry.affiliate,
  })

  // 스크롤 제한 - body와 html 모두 제어
  const scrollY = window.scrollY
  document.documentElement.style.overflow = 'hidden'
  document.body.style.overflow = 'hidden'
  document.body.style.position = 'fixed'
  document.body.style.top = `-${scrollY}px`
  document.body.style.width = '100%'
}

const handlePickerClose = () => {
  // 스크롤 복원 - 순서 중요!
  const scrollY = document.body.style.top
  const scrollValue = scrollY ? parseInt(scrollY || '0') * -1 : 0

  // 1. position을 해제하기 전에 스크롤 위치를 먼저 저장
  document.body.style.position = ''
  document.body.style.top = ''

  // 2. 스크롤 복원
  window.scrollTo(0, scrollValue)

  // 3. 나머지 스타일 복원
  document.documentElement.style.overflow = ''
  document.body.style.overflow = ''
  document.body.style.width = ''

  pickerPosition.value = null
  handleUpdate()
}

const handleUpdate = async () => {
  console.log('handleUpdate called, editingState:', editingState.value)
  if (!editingState.value) return

  const { type, pk, field } = editingState.value

  if (type === 'tran') {
    if (field === 'sort_amount') {
      const originalSort = props.transaction.sort
      const originalAmount = props.transaction.amount || 0
      const newSort = editValue.value.sort
      const newAmount = Number(editValue.value.amount) || 0

      if (newSort === originalSort && newAmount === originalAmount) {
        editingState.value = null
        return
      }
    } else {
      const originalValue = props.transaction[field as keyof BankTransaction]
      if (editValue.value === originalValue) {
        editingState.value = null
        return
      }
    }
  } else {
    const entry = props.transaction.accounting_entries?.find(e => e.pk === pk)
    if (!entry) {
      editingState.value = null // No entry found, cancel editing
      return
    }

    if (field === 'sort_amount') {
      const originalSort = props.transaction.sort
      const originalAmount = props.transaction.amount || 0
      const newSort = editValue.value.sort
      const newAmount = Number(editValue.value.amount) || 0

      if (newSort === originalSort && newAmount === originalAmount) {
        editingState.value = null
        return
      }
    } else if (field === 'account_affiliate') {
      const originalAccount = entry.account
      const originalAffiliate = entry.affiliate
      const newAccount = editValue.value.account
      const newAffiliate = editValue.value.affiliate

      if (newAccount === originalAccount && newAffiliate === originalAffiliate) {
        editingState.value = null
        return
      }
    } else {
      // For other single entry fields
      const originalValue = entry[field as keyof AccountingEntry]
      if (editValue.value === originalValue) {
        editingState.value = null
        return
      }
    }
  }

  const payload: { pk: number; [key: string]: any } = { pk: props.transaction.pk! }

  if (type === 'tran') {
    if (field === 'sort_amount') {
      payload.sort = editValue.value.sort
      payload.amount = Number(editValue.value.amount) || 0
    } else {
      payload[field] = editValue.value
    }
  } else {
    // type === 'entry'
    if (field === 'account_affiliate') {
      payload.accounting_entries = [
        { pk: pk, account: editValue.value.account, affiliate: editValue.value.affiliate },
      ]
    } else {
      payload.accounting_entries = [{ pk: pk, [field]: editValue.value }]
    }
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
      <CTableDataCell>
        <span class="text-primary">{{ transaction.deal_date }}</span>
      </CTableDataCell>

      <!-- 비고 인라인 편집 -->
      <CTableDataCell
        :class="{
          'editable-cell-hint': !isEditing('tran', transaction.pk!, 'note'),
          pointer: !isEditing('tran', transaction.pk!, 'note'),
          'p-0': isEditing('tran', transaction.pk!, 'note'),
        }"
        @dblclick="setEditing('tran', transaction.pk!, 'note', transaction.note)"
      >
        <CFormInput
          v-if="isEditing('tran', transaction.pk!, 'note')"
          ref="inputRef"
          v-model="editValue"
          @blur="handleUpdate"
          @keydown.enter="handleUpdate"
        />
        <span v-else>
          {{ cutString(transaction.note, 20) }}
          <v-icon icon="mdi-pencil-outline" size="14" color="success" class="inline-edit-icon" />
        </span>
      </CTableDataCell>

      <CTableDataCell>
        <span v-if="transaction.bank_account_name">
          {{ cutString(transaction.bank_account_name, 10) }}
        </span>
      </CTableDataCell>

      <!-- Content 인라인 편집 -->
      <CTableDataCell
        :class="{
          truncate: true,
          'editable-cell-hint': !isEditing('tran', transaction.pk!, 'content'),
          pointer: !isEditing('tran', transaction.pk!, 'content'),
          'p-0': isEditing('tran', transaction.pk!, 'content'),
        }"
        @dblclick="setEditing('tran', transaction.pk!, 'content', transaction.content)"
      >
        <CFormInput
          v-if="isEditing('tran', transaction.pk!, 'content')"
          ref="inputRef"
          v-model="editValue"
          @blur="handleUpdate"
          @keydown.enter="handleUpdate"
        />
        <span v-else>
          {{ cutString(transaction.content, 15) }}
          <v-icon icon="mdi-pencil-outline" size="14" color="success" class="inline-edit-icon" />
        </span>
      </CTableDataCell>

      <CTableDataCell
        class="text-right"
        :class="{
          'editable-cell-hint': !isEditing('tran', transaction.pk!, 'sort_amount'),
          pointer: !isEditing('tran', transaction.pk!, 'sort_amount'),
          'p-0': isEditing('tran', transaction.pk!, 'sort_amount'),
        }"
        @dblclick="
          setEditing('tran', transaction.pk!, 'sort_amount', {
            sort: transaction.sort,
            amount: transaction.amount || 0,
          })
        "
      >
        <div
          v-if="isEditing('tran', transaction.pk!, 'sort_amount')"
          class="d-flex align-items-center justify-content-end"
        >
          <v-btn-toggle v-model="editValue.sort" variant="outlined" density="compact" divided>
            <v-btn :value="1" size="x-small">입금</v-btn>
            <v-btn :value="2" size="x-small">출금</v-btn>
          </v-btn-toggle>

          <CFormInput
            ref="inputRef"
            v-model.number="editValue.amount"
            type="number"
            style="width: 120px; margin-left: 8px"
            @blur="handleUpdate"
            @keydown.enter="handleUpdate"
          />
        </div>
        <div v-else>
          <span :class="transaction.sort === 1 ? 'text-success strong' : ''">
            {{ transaction.sort === 1 ? '+' : '-' }}{{ numFormat(transaction.amount || 0) }}
          </span>
          <v-icon icon="mdi-pencil-outline" size="14" color="success" class="inline-edit-icon" />
        </div>
      </CTableDataCell>

      <CTableDataCell colspan="6" class="p-0">
        <CTable class="m-0 p-0">
          <colgroup>
            <col style="width: 20%" />
            <col style="width: 32%" />
            <col style="width: 16%" />
            <col style="width: 26%" />
            <col v-if="write_company_cash" style="width: 6%" />
          </colgroup>
          <CTableRow
            v-for="entry in transaction.accounting_entries"
            :key="entry.pk"
            class="bg-yellow-lighten-5"
          >
            <CTableDataCell
              :class="{
                'account-cell': true,
                'editable-cell-hint': !isEditing('entry', entry.pk!, 'account_affiliate'),
                pointer: !isEditing('entry', entry.pk!, 'account_affiliate'),
              }"
              style="position: relative"
            >
              <div
                class="d-flex align-items-center justify-content-between bg-transparent"
                :class="{ pointer: !isEditing('entry', entry.pk!, 'account_affiliate') }"
                @click="handleAccountClick(entry, $event)"
              >
                <div class="d-flex align-items-center">
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
                <v-icon
                  v-if="!isEditing('entry', entry.pk!, 'account_affiliate')"
                  icon="mdi-chevron-down"
                  size="16"
                  color="grey"
                />
              </div>

              <!-- 계정 선택 Picker (Teleport to body) -->
              <Teleport to="body">
                <LedgerAccountPicker
                  v-if="
                    isEditing('entry', entry.pk!, 'account_affiliate') &&
                    editValue &&
                    pickerPosition
                  "
                  v-model="editValue.account"
                  :options="comAccounts ?? []"
                  :sort-type="sortType"
                  :visible="true"
                  :position="pickerPosition"
                  @close="handlePickerClose"
                />
              </Teleport>

              <!-- 관계회사 선택 (필요 시) -->
              <div
                v-if="
                  isEditing('entry', entry.pk!, 'account_affiliate') &&
                  editValue &&
                  editValue.account &&
                  getAccountById(editValue.account)?.req_affiliate
                "
                class="affiliate-select mt-1"
              >
                <CFormSelect
                  v-model.number="editValue.affiliate"
                  size="sm"
                  placeholder="관계회사 선택"
                  @change="handleUpdate"
                >
                  <option :value="null">관계회사를 선택하세요</option>
                  <option v-for="aff in affiliates" :value="aff.value" :key="aff.value">
                    {{ aff.label }}
                  </option>
                </CFormSelect>
              </div>
            </CTableDataCell>
            <!-- Trader 인라인 편집 -->
            <CTableDataCell
              :class="[
                'editable-cell-hint',
                isEditing('entry', entry.pk!, 'trader') ? '' : 'pointer',
              ]"
              @dblclick="setEditing('entry', entry.pk!, 'trader', entry.trader)"
            >
              <CFormInput
                v-if="isEditing('entry', entry.pk!, 'trader')"
                ref="inputRef"
                v-model="editValue"
                class="bg-transparent"
                @blur="handleUpdate"
                @keydown.enter="handleUpdate"
              />
              <span v-else class="bg-transparent">
                {{ cutString(entry.trader, 20) }}
                <v-icon
                  icon="mdi-pencil-outline"
                  size="14"
                  color="success"
                  class="inline-edit-icon"
                />
              </span>
            </CTableDataCell>
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

<style lang="scss" scoped>
.editable-cell-hint {
  position: relative;
  align-items: center;
}

.account-cell {
  overflow: visible !important;
}

/* 상위 테이블 요소들도 overflow visible로 설정 */
:deep(.table) {
  overflow: visible !important;
}

:deep(.table tbody) {
  overflow: visible !important;
}

:deep(.table tbody tr) {
  overflow: visible !important;
}

:deep(.table tbody tr td) {
  overflow: visible !important;
}

.inline-edit-icon {
  opacity: 0; /* Default hidden */
  margin-left: 4px;
  transition: opacity 0.2s ease;
}

.editable-cell-hint:hover .inline-edit-icon,
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

.affiliate-select {
  position: relative;
  z-index: 1;
}

.dark-theme .bg-yellow-lighten-5 {
  background-color: #49473a !important;
  color: #fff !important;
}
</style>
