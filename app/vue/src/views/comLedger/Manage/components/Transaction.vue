<script lang="ts" setup>
import { computed, type ComputedRef, inject, nextTick, type PropType, ref } from 'vue'
import { useRouter } from 'vue-router'
import { cutString, diffDate, numFormat } from '@/utils/baseMixins'
import { write_company_cash } from '@/utils/pageAuth'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import type { AccountPicker, AccountingEntry, BankTransaction } from '@/store/types/comLedger'
import LedgerAccountPicker from '@/components/LedgerAccount/Picker.vue'
import AffiliateSelectModal from './AffiliateSelectModal.vue'

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

const comAccounts = inject<ComputedRef<AccountPicker[]>>('comAccounts')

// 선택된 account가 affiliate를 요구하는지 확인
const getAccountById = (accountId: number | null | undefined): AccountPicker | undefined => {
  if (!accountId || !comAccounts?.value) return undefined
  return comAccounts.value.find(acc => acc.value === accountId)
}

const sortType = computed(() => {
  if (props.transaction.sort === 1) return 'deposit' // 입금
  if (props.transaction.sort === 2) return 'withdraw' // 출금
  return null // 전체
})

// --- 관계회사 선택 모달 ---
const affiliateModalVisible = ref(false)
const selectedEntryForAffiliate = ref<AccountingEntry | null>(null)

const openAffiliateModal = (entry: AccountingEntry) => {
  if (!allowedPeriod.value) return
  selectedEntryForAffiliate.value = entry
  affiliateModalVisible.value = true
}

const handleAffiliateSelect = async (affiliateId: number | null) => {
  if (!selectedEntryForAffiliate.value) return

  const entry = selectedEntryForAffiliate.value

  // 계정 피커에서 관계회사 모달로 넘어온 경우, 계정도 함께 저장
  const accountToSave = editValue.value?.account || entry.account

  const payload: any = {
    pk: props.transaction.pk!,
    accounting_entries: [
      {
        pk: entry.pk,
        account: accountToSave,
        affiliate: affiliateId,
      },
    ],
  }

  try {
    await ledgerStore.patchBankTransaction(payload)
  } finally {
    // 편집 상태 초기화 (Picker는 이미 닫혔으므로 editValue만 초기화)
    editValue.value = null
    selectedEntryForAffiliate.value = null
  }
}

// --- 제네릭 인라인 편집을 위한 상태 및 로직 ---
const editingState = computed(() => ledgerStore.sharedEditingState) // Use computed for reactivity
const editValue = ref<any>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const pickerPosition = computed(() => ledgerStore.sharedPickerPosition) // Use computed for reactivity

const setEditing = (type: 'tran' | 'entry', pk: number, field: string, value: any) => {
  if (!allowedPeriod.value) return
  ledgerStore.sharedEditingState = { type, pk, field } // Update shared state
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

  // 현재 항목이 이미 편집 중이라면 → 닫기 (토글)
  // 이 경우 handlePickerClose()는 상태 초기화와 동시에 handleUpdate()를 호출하여 저장 시도
  if (isEditing('entry', entry.pk!, 'account_affiliate')) {
    handlePickerClose()
    return
  }

  // 다른 Picker가 열려있는 상태라면 → 다른 Picker 닫기 (저장 없이)
  if (ledgerStore.sharedEditingState) {
    // sharedEditingState를 통해 다른 Picker가 열려있는지 확인
    // 다른 Picker의 스크롤 제어 해제 및 상태 초기화
    // (handlePickerClose()를 호출하면 이전 Picker의 내용이 저장될 수 있으므로,
    // 여기서는 저장 없이 상태만 정리해야 함)
    const scrollY = document.body.style.top
    const scrollValue = scrollY ? parseInt(scrollY || '0') * -1 : 0

    document.body.style.position = ''
    document.body.style.top = ''
    window.scrollTo(0, scrollValue)
    document.documentElement.style.overflow = ''
    document.body.style.overflow = ''
    document.body.style.width = ''

    ledgerStore.clearSharedPickerState() // 공유 상태를 즉시 클리어

    // 다른 Picker를 닫고 함수를 종료. 새 Picker는 다음 클릭에 열림.
    return
  }

  // 열려있는 Picker가 없으면 → 새 Picker 열기
  const target = event.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()

  // 공유 pickerPosition 업데이트
  ledgerStore.sharedPickerPosition = {
    top: rect.bottom,
    left: rect.left,
    width: rect.width,
  }

  // setEditing 함수를 통해 공유 editingState 업데이트
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

const handlePickerClose = async () => {
  // v-model 업데이트 완료를 보장하기 위해 nextTick 사용
  await nextTick()

  // 1. 관계회사가 필요한 계정인지 확인
  if (editingState.value?.field === 'account_affiliate' && editValue.value) {
    const selectedAccount = getAccountById(editValue.value.account)

    // 관계회사가 필요 없는 계정으로 변경한 경우 → affiliate를 null로 초기화
    if (!selectedAccount?.req_affiliate && editValue.value.affiliate) {
      editValue.value.affiliate = null
    }

    // 관계회사가 필요한데 설정되지 않은 경우
    if (selectedAccount?.req_affiliate && !editValue.value.affiliate) {
      // 스크롤 복원
      const scrollY = document.body.style.top
      const scrollValue = scrollY ? parseInt(scrollY || '0') * -1 : 0
      document.body.style.position = ''
      document.body.style.top = ''
      window.scrollTo(0, scrollValue)
      document.documentElement.style.overflow = ''
      document.body.style.overflow = ''
      document.body.style.width = ''

      // 현재 편집 중인 entry 찾기 (clearSharedPickerState 전에 pk와 account 저장)
      const entryPk = editingState.value?.pk
      const selectedAccountId = editValue.value.account
      const entry = props.transaction.accounting_entries?.find(e => e.pk === entryPk)

      // Picker 상태 정리 (Picker를 닫음)
      ledgerStore.clearSharedPickerState()

      // Picker가 완전히 닫힌 후 모달 열기
      if (entry) {
        nextTick(() => {
          // 새로 선택한 account를 entry에 반영
          selectedEntryForAffiliate.value = { ...entry, account: selectedAccountId }
          affiliateModalVisible.value = true
        })
      }
      return
    }
  }

  // 2. 변경 사항 저장 (상태가 초기화되기 전에)
  await handleUpdate()

  // 3. 스크롤 복원 - 순서 중요!
  const scrollY = document.body.style.top
  const scrollValue = scrollY ? parseInt(scrollY || '0') * -1 : 0

  // position을 해제하기 전에 스크롤 위치를 먼저 저장
  document.body.style.position = ''
  document.body.style.top = ''

  // 스크롤 복원
  window.scrollTo(0, scrollValue)

  // 나머지 스타일 복원
  document.documentElement.style.overflow = ''
  document.body.style.overflow = ''
  document.body.style.width = ''

  // 4. 마지막으로 공유 상태 초기화
  ledgerStore.clearSharedPickerState()
}

const handleUpdate = async () => {
  if (!editingState.value) return

  const { type, pk, field } = editingState.value

  if (type === 'tran') {
    if (field === 'sort_amount') {
      const originalSort = props.transaction.sort
      const originalAmount = props.transaction.amount || 0
      const newSort = editValue.value.sort
      const newAmount = Number(editValue.value.amount) || 0

      if (newSort === originalSort && newAmount === originalAmount) {
        ledgerStore.sharedEditingState = null
        return
      }
    } else {
      const originalValue = props.transaction[field as keyof BankTransaction]
      if (editValue.value === originalValue) {
        ledgerStore.sharedEditingState = null
        return
      }
    }
  } else {
    const entry = props.transaction.accounting_entries?.find(e => e.pk === pk)
    if (!entry) {
      ledgerStore.sharedEditingState = null // No entry found, cancel editing
      return
    }

    if (field === 'sort_amount') {
      const originalSort = props.transaction.sort
      const originalAmount = props.transaction.amount || 0
      const newSort = editValue.value.sort
      const newAmount = Number(editValue.value.amount) || 0

      if (newSort === originalSort && newAmount === originalAmount) {
        ledgerStore.sharedEditingState = null
        return
      }
    } else if (field === 'account_affiliate') {
      const originalAccount = entry.account
      const originalAffiliate = entry.affiliate
      const newAccount = editValue.value.account
      const newAffiliate = editValue.value.affiliate

      if (newAccount === originalAccount && newAffiliate === originalAffiliate) {
        ledgerStore.sharedEditingState = null
        return
      }
    } else {
      // For other single entry fields
      const originalValue = entry[field as keyof AccountingEntry]
      if (editValue.value === originalValue) {
        ledgerStore.sharedEditingState = null
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
    ledgerStore.sharedEditingState = null
  }
}

// --- Collapse/Expand State for Accounting Entries ---
const DEFAULT_VISIBLE_COUNT = 10
const visibleEntryCount = ref<number>(DEFAULT_VISIBLE_COUNT)

const totalEntryCount = computed(() => props.transaction.accounting_entries?.length || 0)
const shouldShowExpand = computed(() => totalEntryCount.value > DEFAULT_VISIBLE_COUNT)

const visibleEntries = computed(() => {
  if (!shouldShowExpand.value || visibleEntryCount.value >= totalEntryCount.value) {
    return props.transaction.accounting_entries
  }
  return props.transaction.accounting_entries?.slice(0, visibleEntryCount.value)
})

const remainingCount = computed(() => Math.max(0, totalEntryCount.value - visibleEntryCount.value))

const isFullyExpanded = computed(() => visibleEntryCount.value >= totalEntryCount.value)

const expandMore = () => {
  const remaining = remainingCount.value
  if (remaining <= 30) {
    // Show all remaining if less than 30
    visibleEntryCount.value = totalEntryCount.value
  } else if (visibleEntryCount.value < 30) {
    // First expansion: jump to 30
    visibleEntryCount.value = 30
  } else {
    // Subsequent expansions: add 30 more
    visibleEntryCount.value += 30
  }
}

const collapseAll = () => {
  visibleEntryCount.value = DEFAULT_VISIBLE_COUNT
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

      <CTableDataCell class="text-center">
        <v-icon v-if="transaction.is_balanced" icon="mdi-check-circle" color="success" size="sm" />
        <v-icon v-else icon="mdi-minus-circle" color="danger" size="sm" />
      </CTableDataCell>

      <CTableDataCell colspan="6" class="p-0">
        <CTable class="m-0 p-0">
          <colgroup>
            <col style="width: 28%" />
            <col style="width: 26%" />
            <col style="width: 16%" />
            <col style="width: 24%" />
            <col v-if="write_company_cash" style="width: 6%" />
          </colgroup>
          <CTableRow v-for="entry in visibleEntries" :key="entry.pk" class="bg-yellow-lighten-5">
            <CTableDataCell
              :class="{
                'account-cell': true,
                'editable-cell-hint': !isEditing('entry', entry.pk!, 'account_affiliate'),
                pointer: !isEditing('entry', entry.pk!, 'account_affiliate'),
              }"
              class="bg-yellow-lighten-4"
              style="position: relative"
            >
              <div
                class="d-flex align-items-center justify-content-between bg-transparent"
                :class="{ pointer: !isEditing('entry', entry.pk!, 'account_affiliate') }"
                @click="handleAccountClick(entry, $event)"
              >
                <div class="d-flex align-items-center">
                  <span>{{ cutString(entry.account_name, 12) }}</span>
                  <!-- 관계회사 정보 표시 (이미 설정된 경우) - 클릭 가능 -->
                  <v-tooltip v-if="entry.affiliate && allowedPeriod" location="top">
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-link-variant"
                        color="primary"
                        size="16"
                        class="ml-1 pointer"
                        @click.stop="openAffiliateModal(entry)"
                      />
                    </template>
                    <div class="pa-2">
                      <div class="font-weight-bold mb-1">관계회사/프로젝트</div>
                      <div class="mb-2">{{ entry.affiliate_display }}</div>
                      <div class="d-flex align-items-center text-amber font-weight-medium">
                        <v-icon icon="mdi-pencil" size="14" class="mr-1" />
                        클릭하여 변경
                      </div>
                    </div>
                  </v-tooltip>
                  <!-- 관계회사 정보 표시 (읽기 전용) -->
                  <v-tooltip v-else-if="entry.affiliate && !allowedPeriod" location="top">
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
                  <!-- 관계회사 설정 필요 아이콘 (설정 필요하지만 없는 경우) -->
                  <v-tooltip
                    v-else-if="getAccountById(entry.account)?.req_affiliate && allowedPeriod"
                    location="top"
                  >
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-link-variant-plus"
                        color="warning"
                        size="16"
                        class="ml-1 pointer"
                        @click.stop="openAffiliateModal(entry)"
                      />
                    </template>
                    <span>관계회사를 선택하세요</span>
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
            </CTableDataCell>
            <!-- Trader 인라인 편집 -->
            <CTableDataCell
              :class="[
                'editable-cell-hint',
                isEditing('entry', entry.pk!, 'trader') ? '' : 'pointer',
              ]"
              class="text-truncate"
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
                {{ cutString(entry.trader, 12) }}
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

          <!-- Expand/Collapse Controls Row -->
          <CTableRow v-if="shouldShowExpand" class="bg-grey-lighten-4">
            <CTableDataCell colspan="5" class="text-center py-2">
              <!-- Expand More Button -->
              <v-btn
                v-if="!isFullyExpanded"
                variant="text"
                size="small"
                color="primary"
                @click="expandMore"
              >
                <v-icon icon="mdi-chevron-down" size="18" class="mr-1" />
                더보기 ({{ remainingCount }}개 항목)
              </v-btn>

              <!-- Collapse Button -->
              <v-btn v-else variant="text" size="small" color="grey" @click="collapseAll">
                <v-icon icon="mdi-chevron-up" size="18" class="mr-1" />
                접기
              </v-btn>

              <!-- Entry Count Indicator -->
              <span class="text-caption text-grey ml-3">
                {{ visibleEntryCount }} / {{ totalEntryCount }} 표시 중
              </span>
            </CTableDataCell>
          </CTableRow>
        </CTable>
      </CTableDataCell>
    </CTableRow>

    <!-- 관계회사 선택 모달 -->
    <AffiliateSelectModal
      v-model="affiliateModalVisible"
      :affiliate="selectedEntryForAffiliate?.affiliate"
      :account-name="selectedEntryForAffiliate?.account_name"
      @select="handleAffiliateSelect"
    />
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

.dark-theme .bg-yellow-lighten-4 {
  background-color: #403e33 !important;
  color: #fff !important;
}
</style>
