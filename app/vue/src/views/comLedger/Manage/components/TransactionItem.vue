<script lang="ts" setup>
import {
  computed,
  type ComputedRef,
  inject,
  nextTick,
  onUnmounted,
  type PropType,
  ref,
  watch,
} from 'vue'
import { useRouter } from 'vue-router'
import { cutString, numFormat } from '@/utils/baseMixins'
import { message } from '@/utils/helper'
import { useAccount } from '@/store/pinia/account.ts'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type {
  AccountingEntry,
  AccountPicker,
  BankTransaction,
  CompositeTransactionPatchPayload,
} from '@/store/types/comLedger'
import LedgerAccountPicker from '@/components/LedgerAccount/Picker.vue'
import AffiliateSelectModal from './AffiliateSelectModal.vue'

interface SortAmountValue {
  sort: 1 | 2
  amount: number
}

interface AccountAffiliateValue {
  account: number
  affiliate: number | null
}

type InlineEditValue = string | SortAmountValue | AccountAffiliateValue | null

interface FocusableInputRef {
  focus?: () => void
  select?: () => void
  $el?: HTMLElement | null
}

const props = defineProps({
  transaction: { type: Object as PropType<BankTransaction>, required: true },
  calculated: { type: String, default: '' },
  isHighlighted: { type: Boolean, default: false },
})

const { can, canGlobal, PERM } = usePerms()
const canComLedgerManage = computed(
  () => can(PERM.HQ_LEDGER_MANAGE) || canGlobal(PERM.HQ_LEDGER_MANAGE),
)
const canComLedgerUpdate = computed(
  () => can(PERM.HQ_LEDGER_UPDATE) || canGlobal(PERM.HQ_LEDGER_UPDATE),
)
const canComLedgerEdit = computed(() => canComLedgerUpdate.value || canComLedgerManage.value)

const router = useRouter()
const ledgerStore = useComLedger()

const rowColor = computed(() => (props.isHighlighted ? 'warning' : ''))

const accStore = useAccount()
const superAuth = computed(() => accStore.superAuth)
const allowedPeriod = computed(
  () =>
    superAuth.value ||
    canComLedgerManage.value ||
    (canComLedgerUpdate.value &&
      (!props.calculated || (props.transaction?.deal_date ?? '') > props.calculated)),
)

const comAccounts = inject<ComputedRef<AccountPicker[]>>('comAccounts')

// 선택된 account가 affiliate를 요구하는지 확인
const getAccountById = (accountId: number | null | undefined): AccountPicker | undefined => {
  if (!accountId || !comAccounts?.value) return undefined
  return comAccounts.value.find(acc => acc.value === accountId)
}

const sortType = computed(() => {
  if (props.transaction?.sort === 1) return 'deposit' // 입금
  if (props.transaction.sort === 2) return 'withdraw' // 출금
  return null // 전체
})

// --- 스크롤 제어 헬퍼 ---
const lockBodyScroll = () => {
  const scrollY = window.scrollY
  document.documentElement.style.overflow = 'hidden'
  document.body.style.overflow = 'hidden'
  document.body.style.position = 'fixed'
  document.body.style.top = `-${scrollY}px`
  document.body.style.width = '100%'
}

const unlockBodyScroll = () => {
  const scrollY = document.body.style.top
  const scrollValue = scrollY ? parseInt(scrollY, 10) * -1 : 0
  document.body.style.position = ''
  document.body.style.top = ''
  window.scrollTo(0, scrollValue)
  document.documentElement.style.overflow = ''
  document.body.style.overflow = ''
  document.body.style.width = ''
}

// --- 관계회사 선택 모달 ---
const affiliateModalVisible = ref(false)
const selectedEntryForAffiliate = ref<AccountingEntry | null>(null)
const pendingAccountForAffiliate = ref<number | null>(null)

const isAffiliateModalRequired = computed(() => {
  const accountId =
    pendingAccountForAffiliate.value ?? selectedEntryForAffiliate.value?.account ?? null
  return Boolean(getAccountById(accountId)?.req_affiliate)
})

const openAffiliateModal = (entry: AccountingEntry) => {
  if (!allowedPeriod.value) return
  pendingAccountForAffiliate.value = entry.account
  selectedEntryForAffiliate.value = entry
  affiliateModalVisible.value = true
}

const handleAffiliateSelect = async (affiliateId: number | null) => {
  if (!selectedEntryForAffiliate.value || !props.transaction?.pk) return

  const entry = selectedEntryForAffiliate.value
  const accountToSave = pendingAccountForAffiliate.value || entry.account

  const payload: CompositeTransactionPatchPayload = {
    pk: props.transaction.pk,
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
  } catch {
    // errorHandle in store already displays toast
  } finally {
    editValue.value = null
    selectedEntryForAffiliate.value = null
    pendingAccountForAffiliate.value = null
  }
}

watch(affiliateModalVisible, visible => {
  if (!visible) {
    pendingAccountForAffiliate.value = null
    selectedEntryForAffiliate.value = null
  }
})

// --- 제네릭 인라인 편집을 위한 상태 및 로직 ---
const editingState = computed<{
  type: 'tran' | 'entry'
  pk: number
  field: string
} | null>(() => ledgerStore.sharedEditingState)
const editValue = ref<InlineEditValue>(null)
const inputRef = ref<FocusableInputRef | FocusableInputRef[] | null>(null)
const pickerPosition = computed(() => ledgerStore.sharedPickerPosition)
let isUpdating = false

const accountAffiliateModel = computed<number | null>({
  get: () => {
    const val = editValue.value
    return val && typeof val === 'object' && 'account' in val ? val.account : null
  },
  set: newAccount => {
    const val = editValue.value
    if (val && typeof val === 'object' && 'account' in val && newAccount !== null) {
      val.account = newAccount
    }
  },
})

const sortAmountModel = computed<number | null>({
  get: () => {
    const val = editValue.value
    return val && typeof val === 'object' && 'amount' in val ? val.amount : 0
  },
  set: newAmount => {
    const val = editValue.value
    if (val && typeof val === 'object' && 'amount' in val) {
      val.amount = Number(newAmount) || 0
    }
  },
})

watch(
  editingState,
  async newVal => {
    if (newVal) {
      const { type, pk, field } = newVal
      const isOwnedTran = type === 'tran' && pk === props.transaction?.pk
      const matchedEntry =
        type === 'entry'
          ? props.transaction?.accounting_entries?.find(e => e.pk === pk)
          : undefined

      if (isOwnedTran) {
        if (field === 'note') {
          editValue.value = props.transaction?.note ?? ''
        } else if (field === 'content') {
          editValue.value = props.transaction?.content ?? ''
        } else if (field === 'sort_amount') {
          editValue.value = {
            sort: props.transaction?.sort,
            amount: props.transaction?.amount || 0,
          }
        }
      } else if (matchedEntry) {
        if (field === 'account_affiliate') {
          editValue.value = {
            account: matchedEntry.account,
            affiliate: matchedEntry.affiliate,
          }
        } else if (field === 'trader') {
          editValue.value = matchedEntry.trader ?? ''
        }
      }

      if ((isOwnedTran || matchedEntry) && field !== 'account_affiliate') {
        await nextTick()
        const rawRef = Array.isArray(inputRef.value) ? inputRef.value[0] : inputRef.value
        const domInput =
          rawRef?.$el?.querySelector<HTMLInputElement>('input') ??
          (rawRef?.$el instanceof HTMLInputElement ? rawRef.$el : null) ??
          (rawRef && typeof rawRef.focus === 'function' ? rawRef : null)
        domInput?.focus?.()
        if (domInput && 'select' in domInput && typeof domInput.select === 'function') {
          domInput.select()
        }
      }
    } else {
      editValue.value = null
    }
  },
  { immediate: true },
)

const setEditing = (type: 'tran' | 'entry', pk: number, field: string, value: InlineEditValue) => {
  if (!canComLedgerEdit.value || !allowedPeriod.value) return
  ledgerStore.sharedEditingState = { type, pk, field }
  editValue.value = value
}

const cancelEditing = () => {
  ledgerStore.clearSharedPickerState()
  editValue.value = null
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

  if (!canComLedgerEdit.value) return

  // 현재 항목이 이미 편집 중이라면 → 닫기 (토글)
  if (isEditing('entry', entry.pk, 'account_affiliate')) {
    handlePickerClose()
    return
  }

  // 다른 Picker가 열려있는 상태라면 → 다른 Picker 닫기 (저장 없이)
  if (ledgerStore.sharedEditingState) {
    unlockBodyScroll()
    ledgerStore.clearSharedPickerState()
    return
  }

  // 열려있는 Picker가 없으면 → 새 Picker 열기
  const target = event.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const pickerHeight = 340
  const spaceBelow = window.innerHeight - rect.bottom
  const top =
    spaceBelow < pickerHeight && rect.top > spaceBelow
      ? Math.max(8, rect.top - Math.min(pickerHeight, rect.top - 8))
      : rect.bottom
  const left = Math.max(8, Math.min(rect.left, window.innerWidth - Math.max(rect.width, 280) - 8))

  // 공유 pickerPosition 업데이트
  ledgerStore.sharedPickerPosition = {
    top,
    left,
    width: rect.width,
  }

  // 정산 마감일 이후에도 계정만 단독 수정할 수 있도록 sharedEditingState 직접 설정
  ledgerStore.sharedEditingState = {
    type: 'entry',
    pk: entry.pk,
    field: 'account_affiliate',
  }
  editValue.value = {
    account: entry.account,
    affiliate: entry.affiliate,
  }

  lockBodyScroll()
}

const handlePickerClose = async () => {
  await nextTick()

  const val = editValue.value
  if (editingState.value?.field === 'account_affiliate' && val && typeof val === 'object' && 'account' in val) {
    const selectedAccount = getAccountById(val.account)

    if (!selectedAccount?.req_affiliate && val.affiliate && allowedPeriod.value) {
      val.affiliate = null
    }

    if (selectedAccount?.req_affiliate && !val.affiliate) {
      unlockBodyScroll()
      const entryPk = editingState.value?.pk
      const selectedAccountId = val.account
      const entry = props.transaction?.accounting_entries?.find(e => e.pk === entryPk)
      ledgerStore.clearSharedPickerState()

      if (!allowedPeriod.value) {
        message(
          'warning',
          '알림!',
          '정산 마감일 이전 거래는 관계회사가 필수인 계정으로 변경 시 관계회사 정보를 함께 등록할 수 없습니다.',
        )
        return
      }

      if (entry) {
        nextTick(() => {
          pendingAccountForAffiliate.value = selectedAccountId
          selectedEntryForAffiliate.value = { ...entry, account: selectedAccountId }
          affiliateModalVisible.value = true
        })
      }
      return
    }
  }

  try {
    await handleUpdate()
  } finally {
    unlockBodyScroll()
    ledgerStore.clearSharedPickerState()
  }
}

const handleUpdate = async () => {
  const state = editingState.value
  if (!state || isUpdating || !props.transaction?.pk) return

  const { type, pk, field } = state
  const currentValue = editValue.value

  if (type === 'tran') {
    if (pk !== props.transaction.pk) return
    if (field === 'sort_amount') {
      if (!currentValue || typeof currentValue !== 'object' || !('amount' in currentValue)) {
        ledgerStore.sharedEditingState = null
        return
      }
      const originalSort = props.transaction.sort
      const originalAmount = props.transaction.amount || 0
      const newSort = currentValue.sort
      const newAmount = Number(currentValue.amount) || 0

      if (newSort === originalSort && newAmount === originalAmount) {
        ledgerStore.sharedEditingState = null
        return
      }
    } else {
      const originalValue = (props.transaction[field as keyof BankTransaction] as string) ?? ''
      if (currentValue === originalValue) {
        ledgerStore.sharedEditingState = null
        return
      }
    }
  } else {
    const entry = props.transaction?.accounting_entries?.find(e => e.pk === pk)
    if (!entry) {
      ledgerStore.sharedEditingState = null
      return
    }

    if (field === 'account_affiliate') {
      if (!currentValue || typeof currentValue !== 'object' || !('account' in currentValue)) {
        ledgerStore.sharedEditingState = null
        return
      }
      if (currentValue.account === entry.account && currentValue.affiliate === entry.affiliate) {
        ledgerStore.sharedEditingState = null
        return
      }
    } else {
      const originalValue = (entry[field as keyof AccountingEntry] as string | null) ?? ''
      if (currentValue === originalValue) {
        ledgerStore.sharedEditingState = null
        return
      }
    }
  }

  const payload: CompositeTransactionPatchPayload = { pk: props.transaction.pk }

  if (type === 'tran') {
    if (field === 'sort_amount' && currentValue && typeof currentValue === 'object' && 'amount' in currentValue) {
      payload.sort = currentValue.sort
      payload.amount = Number(currentValue.amount) || 0
    } else if (field === 'note' || field === 'content') {
      payload[field] = String(currentValue ?? '')
    }
  } else {
    if (
      field === 'account_affiliate' &&
      currentValue &&
      typeof currentValue === 'object' &&
      'account' in currentValue
    ) {
      payload.accounting_entries = [
        { pk, account: currentValue.account, affiliate: currentValue.affiliate },
      ]
    } else if (field === 'trader') {
      payload.accounting_entries = [{ pk, trader: String(currentValue ?? '') }]
    }
  }

  isUpdating = true
  try {
    await ledgerStore.patchBankTransaction(payload)
  } catch {
    // errorHandle in store already displays toast
  } finally {
    isUpdating = false
    ledgerStore.sharedEditingState = null
  }
}

onUnmounted(() => {
  const current = ledgerStore.sharedEditingState
  if (!current) return
  const ownsState =
    (current.type === 'tran' && current.pk === props.transaction?.pk) ||
    (current.type === 'entry' &&
      Boolean(props.transaction?.accounting_entries?.some(e => e.pk === current.pk)))
  if (ownsState) {
    unlockBodyScroll()
    ledgerStore.clearSharedPickerState()
  }
})

// --- Collapse/Expand State for Accounting Entries ---
const DEFAULT_VISIBLE_COUNT = 3
const visibleEntryCount = ref<number>(DEFAULT_VISIBLE_COUNT)

const totalEntryCount = computed(() => props.transaction?.accounting_entries?.length || 0)
const canInlineEditAmount = computed(() => allowedPeriod.value && totalEntryCount.value === 0)
const shouldShowExpand = computed(() => totalEntryCount.value > DEFAULT_VISIBLE_COUNT)

const visibleEntries = computed(() => {
  if (!shouldShowExpand.value || visibleEntryCount.value >= totalEntryCount.value) {
    return props.transaction?.accounting_entries
  }
  return props.transaction?.accounting_entries?.slice(0, visibleEntryCount.value)
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
          'editable-cell-hint': allowedPeriod && !isEditing('tran', transaction.pk!, 'note'),
          pointer: allowedPeriod && !isEditing('tran', transaction.pk!, 'note'),
          'p-0': isEditing('tran', transaction.pk!, 'note'),
        }"
        @dblclick="setEditing('tran', transaction.pk!, 'note', transaction.note)"
      >
        <CFormInput
          v-if="isEditing('tran', transaction.pk!, 'note')"
          ref="inputRef"
          :model-value="typeof editValue === 'string' ? editValue : ''"
          @update:model-value="val => (editValue = val)"
          @blur="handleUpdate"
          @keydown.enter="handleUpdate"
          @keydown.esc="cancelEditing"
        />
        <span v-else :title="transaction.note || undefined">
          {{ cutString(transaction.note, 20) }}
          <v-icon
            v-if="allowedPeriod"
            icon="mdi-pencil-outline"
            size="14"
            color="success"
            class="inline-edit-icon"
          />
        </span>
      </CTableDataCell>

      <CTableDataCell>
        <span v-if="transaction.bank_account_name" :title="transaction.bank_account_name">
          {{ cutString(transaction.bank_account_name, 10) }}
        </span>
      </CTableDataCell>

      <!-- Content 인라인 편집 -->
      <CTableDataCell
        :class="{
          truncate: true,
          'editable-cell-hint': allowedPeriod && !isEditing('tran', transaction.pk!, 'content'),
          pointer: allowedPeriod && !isEditing('tran', transaction.pk!, 'content'),
          'p-0': isEditing('tran', transaction.pk!, 'content'),
        }"
        @dblclick="setEditing('tran', transaction.pk!, 'content', transaction.content)"
      >
        <CFormInput
          v-if="isEditing('tran', transaction.pk!, 'content')"
          ref="inputRef"
          :model-value="typeof editValue === 'string' ? editValue : ''"
          @update:model-value="val => (editValue = val)"
          @blur="handleUpdate"
          @keydown.enter="handleUpdate"
          @keydown.esc="cancelEditing"
        />
        <span v-else :title="transaction.content || undefined">
          {{ cutString(transaction.content, 15) }}
          <v-icon
            v-if="allowedPeriod"
            icon="mdi-pencil-outline"
            size="14"
            color="success"
            class="inline-edit-icon"
          />
        </span>
      </CTableDataCell>

      <CTableDataCell
        class="text-end"
        :class="{
          'editable-cell-hint':
            canInlineEditAmount && !isEditing('tran', transaction.pk!, 'sort_amount'),
          pointer: canInlineEditAmount && !isEditing('tran', transaction.pk!, 'sort_amount'),
          'p-0': isEditing('tran', transaction.pk!, 'sort_amount'),
        }"
        @dblclick="
          canInlineEditAmount &&
          setEditing('tran', transaction.pk!, 'sort_amount', {
            sort: transaction.sort,
            amount: transaction.amount || 0,
          })
        "
      >
        <div
          v-if="isEditing('tran', transaction.pk!, 'sort_amount') && editValue"
          class="d-flex align-items-center justify-content-end"
        >
          <v-chip
            :color="transaction.sort === 1 ? 'primary' : 'danger'"
            size="x-small"
            class="me-2"
          >
            {{ transaction.sort === 1 ? '입금' : '출금' }}
          </v-chip>

          <CFormInput
            ref="inputRef"
            v-model.number="sortAmountModel"
            type="number"
            min="0"
            style="width: 120px"
            @blur="handleUpdate"
            @keydown.enter="handleUpdate"
            @keydown.esc="cancelEditing"
          />
        </div>
        <div v-else>
          <span :class="transaction.sort === 1 ? 'text-success strong' : ''">
            {{ transaction.sort === 1 ? '+' : '-' }}{{ numFormat(transaction.amount || 0) }}
          </span>
          <v-icon
            v-if="canInlineEditAmount"
            icon="mdi-pencil-outline"
            size="14"
            color="success"
            class="inline-edit-icon"
          />
        </div>
      </CTableDataCell>

      <CTableDataCell class="text-center">
        <v-icon
          v-if="transaction.is_balanced"
          icon="mdi-check-circle"
          color="success"
          size="small"
        />
        <v-icon v-else icon="mdi-minus-circle" color="danger" size="small" />
      </CTableDataCell>

      <CTableDataCell :colspan="canComLedgerEdit ? 5 : 4" class="p-0">
        <CTable class="m-0 p-0">
          <colgroup>
            <col style="width: 28%" />
            <col style="width: 26%" />
            <col style="width: 16%" />
            <col style="width: 24%" />
            <col v-if="canComLedgerEdit" style="width: 6%" />
          </colgroup>
          <CTableRow v-for="entry in visibleEntries" :key="entry.pk" class="bg-yellow-lighten-5">
            <CTableDataCell
              :class="{
                'account-cell': true,
                'editable-cell-hint':
                  canComLedgerEdit && !isEditing('entry', entry.pk, 'account_affiliate'),
                pointer: canComLedgerEdit && !isEditing('entry', entry.pk, 'account_affiliate'),
              }"
              class="bg-yellow-lighten-4"
              style="position: relative"
            >
              <div
                class="d-flex align-items-center justify-content-between bg-transparent"
                :class="{
                  pointer: canComLedgerEdit && !isEditing('entry', entry.pk, 'account_affiliate'),
                }"
                @click="handleAccountClick(entry, $event)"
              >
                <div class="d-flex align-items-center">
                  <span :title="entry.account_name">{{ cutString(entry.account_name, 12) }}</span>
                  <!-- 관계회사 정보 표시 (이미 설정된 경우) - 클릭 가능 -->
                  <v-tooltip v-if="entry.affiliate && allowedPeriod" location="top">
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-link-variant"
                        color="primary"
                        size="16"
                        class="ms-1 pointer"
                        @click.stop="openAffiliateModal(entry)"
                      />
                    </template>
                    <div class="pa-2">
                      <div class="fw-bold mb-1">관계회사/프로젝트</div>
                      <div class="mb-2">{{ entry.affiliate_display }}</div>
                      <div class="d-flex align-items-center text-amber fw-medium">
                        <v-icon icon="mdi-pencil" size="14" class="me-1" />
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
                        class="ms-1"
                      />
                    </template>
                    <div class="pa-2">
                      <div class="fw-bold mb-1">관계회사/프로젝트</div>
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
                        class="ms-1 pointer"
                        @click.stop="openAffiliateModal(entry)"
                      />
                    </template>
                    <span>관계회사를 선택하세요</span>
                  </v-tooltip>
                </div>
                <v-icon
                  v-if="canComLedgerEdit && !isEditing('entry', entry.pk, 'account_affiliate')"
                  icon="mdi-chevron-down"
                  size="16"
                  color="grey"
                />
              </div>

              <!-- 계정 선택 Picker (Teleport to body) -->
              <Teleport to="body">
                <LedgerAccountPicker
                  v-if="
                    isEditing('entry', entry.pk, 'account_affiliate') && editValue && pickerPosition
                  "
                  v-model="accountAffiliateModel"
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
                allowedPeriod ? 'editable-cell-hint' : '',
                allowedPeriod && !isEditing('entry', entry.pk, 'trader') ? 'pointer' : '',
              ]"
              class="text-truncate"
              @dblclick="setEditing('entry', entry.pk, 'trader', entry.trader ?? '')"
            >
              <CFormInput
                v-if="isEditing('entry', entry.pk, 'trader')"
                ref="inputRef"
                :model-value="typeof editValue === 'string' ? editValue : ''"
                class="bg-transparent"
                @update:model-value="val => (editValue = val)"
                @blur="handleUpdate"
                @keydown.enter="handleUpdate"
                @keydown.esc="cancelEditing"
              />
              <span v-else class="bg-transparent" :title="entry.trader || undefined">
                {{ cutString(entry.trader ?? '', 12) }}
                <v-icon
                  v-if="allowedPeriod"
                  icon="mdi-pencil-outline"
                  size="14"
                  color="success"
                  class="inline-edit-icon"
                />
              </span>
            </CTableDataCell>
            <CTableDataCell
              class="text-end"
              :class="transaction.sort === 1 ? 'text-success strong' : ''"
            >
              {{ transaction.sort === 1 ? '+' : '-' }}{{ numFormat(entry.amount) }}
            </CTableDataCell>
            <CTableDataCell class="ps-3">
              <span :title="entry.evidence_type_display || undefined">
                {{ cutString(entry.evidence_type_display ?? '', 10) }}
              </span>
            </CTableDataCell>
            <CTableDataCell v-if="canComLedgerEdit" class="text-end pe-2">
              <v-icon
                v-if="allowedPeriod"
                icon="mdi-pencil"
                size="18"
                class="pointer edit-icon-hover"
                @click="
                  router.push({
                    name: '본사 거래 내역 - 수정',
                    params: { transId: transaction.pk },
                  })
                "
              />
            </CTableDataCell>
          </CTableRow>

          <!-- Expand/Collapse Controls Row -->
          <CTableRow v-if="shouldShowExpand" class="bg-grey-lighten-4">
            <CTableDataCell :colspan="canComLedgerEdit ? 5 : 4" class="text-center py-2">
              <!-- Expand More Button -->
              <v-btn
                v-if="!isFullyExpanded"
                variant="text"
                size="small"
                color="primary"
                @click="expandMore"
              >
                <v-icon icon="mdi-chevron-down" size="18" class="me-1" />
                더보기 ({{ remainingCount }}개 항목)
              </v-btn>

              <!-- Collapse Button -->
              <v-btn v-else variant="text" size="small" color="grey" @click="collapseAll">
                <v-icon icon="mdi-chevron-up" size="18" class="me-1" />
                접기
              </v-btn>

              <!-- Entry Count Indicator -->
              <span class="text-caption text-grey ms-3">
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
      :affiliate="(selectedEntryForAffiliate as AccountingEntry)?.affiliate"
      :account-name="(selectedEntryForAffiliate as AccountingEntry)?.account_name"
      :required="isAffiliateModalRequired"
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
