<script lang="ts" setup>
import {
  computed,
  type ComputedRef,
  inject,
  nextTick,
  onUnmounted,
  ref,
  watch,
} from 'vue'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms.ts'
import { cutString, numFormat } from '@/utils/baseMixins'
import { message } from '@/utils/helper'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import type { AccountPicker } from '@/store/types/comLedger.ts'
import type {
  CompositeProBankTransPatchPayload,
  ProAccountingEntry,
  ProBankTrans,
} from '@/store/types/proLedger.ts'
import LedgerAccountPicker from '@/components/LedgerAccount/Picker.vue'
import BaseSelectModal from './BaseSelectModal.vue'

interface SortAmountValue {
  sort: 1 | 2
  amount: number
}

interface AccountContractValue {
  account: number
  contract: number | null
  contractor: number | null
}

type InlineEditValue = string | SortAmountValue | AccountContractValue | null

interface FocusableInputRef {
  focus?: () => void
  select?: () => void
  $el?: HTMLElement | null
}

interface Props {
  proTrans: ProBankTrans
  project?: number | null
  calculated?: string
  isHighlighted?: boolean
  isImprest?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  project: null,
  calculated: '',
  isHighlighted: false,
  isImprest: false,
})

const accStore = useAccount()
const superAuth = computed(() => accStore.superAuth)

const { can, canGlobal, PERM } = usePerms()
const targetProject = computed(() => props.project ?? props.proTrans?.project ?? undefined)
const canLedgerUpdate = computed(() =>
  targetProject.value ? can(PERM.LEDGER_UPDATE, targetProject.value) : can(PERM.LEDGER_UPDATE),
)
const canLedgerManage = computed(
  () =>
    (targetProject.value
      ? can(PERM.LEDGER_MANAGE, targetProject.value)
      : can(PERM.LEDGER_MANAGE)) || canGlobal(PERM.LEDGER_MANAGE),
)
const canLedgerEdit = computed(() => canLedgerUpdate.value || canLedgerManage.value)

const router = useRouter()
const proLedgerStore = useProLedger()

const rowColor = computed(() => (props.isHighlighted ? 'warning' : ''))
const editRouteName = computed(() =>
  props.isImprest ? '운영비 내역 관리 - 수정' : '거래 내역 관리 - 수정',
)

// 백엔드 정산 마감 정책과 일치: deal_date <= calculated 이면 관리자/ledger.manage만 전체 수정 가능
const allowedPeriod = computed(
  () =>
    superAuth.value ||
    canLedgerManage.value ||
    (canLedgerUpdate.value &&
      (!props.calculated || (props.proTrans?.deal_date ?? '') > props.calculated)),
)

const proAccounts = inject<ComputedRef<AccountPicker[]>>('proAccounts')

// 선택된 account가 contract/contractor를 요구하는지 확인
const getAccountById = (accountId: number | null | undefined): AccountPicker | undefined => {
  if (!accountId || !proAccounts?.value) return undefined
  return proAccounts.value.find(acc => acc.value === accountId)
}

const sortType = computed(() => {
  if (props.proTrans?.sort === 1) return 'deposit' // 입금
  if (props.proTrans.sort === 2) return 'withdraw' // 출금
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

// --- 계약/계약자 정보 선택 모달 (통합) ---
const selectModalVisible = ref(false)
const selectModalType = ref<'contract' | 'contractor'>('contract')
const selectedEntryForSelect = ref<ProAccountingEntry | null>(null)
const pendingAccountForModal = ref<number | null>(null)

const openSelectModal = (entry: ProAccountingEntry, type: 'contract' | 'contractor') => {
  if (!allowedPeriod.value) return
  pendingAccountForModal.value = entry.account
  selectedEntryForSelect.value = entry
  selectModalType.value = type
  selectModalVisible.value = true
}

const handleSelect = async (id: number | null) => {
  if (!selectedEntryForSelect.value || !props.proTrans?.pk) return

  const entry = selectedEntryForSelect.value
  const accountToSave = pendingAccountForModal.value || entry.account
  const type = selectModalType.value

  const payload: CompositeProBankTransPatchPayload = {
    pk: props.proTrans.pk,
    accounting_entries: [
      {
        pk: entry.pk,
        account: accountToSave,
        [type]: id,
      },
    ],
  }

  try {
    await proLedgerStore.patchProBankTrans(payload)
  } finally {
    editValue.value = null
    selectedEntryForSelect.value = null
    pendingAccountForModal.value = null
  }
}

watch(selectModalVisible, visible => {
  if (!visible) {
    pendingAccountForModal.value = null
    selectedEntryForSelect.value = null
  }
})

// --- 제네릭 인라인 편집을 위한 상태 및 로직 ---
const editingState = computed<{
  type: 'tran' | 'entry'
  pk: number
  field: string
} | null>(() => proLedgerStore.sharedEditingState)
const editValue = ref<InlineEditValue>(null)
const inputRef = ref<FocusableInputRef | FocusableInputRef[] | null>(null)
const pickerPosition = computed(() => proLedgerStore.sharedPickerPosition)
let isUpdating = false

const accountContractModel = computed<number | null>({
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
      const isOwnedTran = type === 'tran' && pk === props.proTrans?.pk
      const matchedEntry =
        type === 'entry'
          ? (props.proTrans?.accounting_entries as ProAccountingEntry[])?.find(e => e.pk === pk)
          : undefined

      if (isOwnedTran) {
        if (field === 'note') {
          editValue.value = props.proTrans?.note ?? ''
        } else if (field === 'content') {
          editValue.value = props.proTrans?.content ?? ''
        } else if (field === 'sort_amount') {
          editValue.value = {
            sort: props.proTrans?.sort,
            amount: props.proTrans?.amount || 0,
          }
        }
      } else if (matchedEntry) {
        if (field === 'account_contract') {
          editValue.value = {
            account: matchedEntry.account,
            contract: matchedEntry.contract,
            contractor: matchedEntry.contractor,
          }
        } else if (field === 'trader') {
          editValue.value = matchedEntry.trader ?? ''
        }
      }

      if ((isOwnedTran || matchedEntry) && field !== 'account_contract') {
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
  if (!allowedPeriod.value) return
  proLedgerStore.sharedEditingState = { type, pk, field }
  editValue.value = value
}

const cancelEditing = () => {
  proLedgerStore.clearSharedPickerState()
  editValue.value = null
}

const isEditing = (type: 'tran' | 'entry', pk: number, field: string) => {
  return (
    editingState.value?.type === type &&
    editingState.value?.pk === pk &&
    editingState.value?.field === field
  )
}

const handleAccountClick = (entry: ProAccountingEntry, event: MouseEvent) => {
  event.stopPropagation()

  if (!canLedgerEdit.value) return

  // 현재 항목이 이미 편집 중이라면 → 닫기 (토글)
  if (isEditing('entry', entry.pk, 'account_contract')) {
    handlePickerClose()
    return
  }

  // 다른 Picker가 열려있는 상태라면 → 다른 Picker 닫기 (저장 없이)
  if (proLedgerStore.sharedEditingState) {
    unlockBodyScroll()
    proLedgerStore.clearSharedPickerState()
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

  proLedgerStore.sharedPickerPosition = {
    top,
    left,
    width: rect.width,
  }

  // 정산 마감일 이후에도 계정 단독 수정은 허용할 수 있도록 sharedEditingState 직접 설정
  proLedgerStore.sharedEditingState = {
    type: 'entry',
    pk: entry.pk,
    field: 'account_contract',
  }
  editValue.value = {
    account: entry.account,
    contract: entry.contract,
    contractor: entry.contractor,
  }

  lockBodyScroll()
}

// 스크롤 복원 + 모달 열기 (공통 로직)
const restoreScrollAndOpenModal = (type: 'contract' | 'contractor') => {
  unlockBodyScroll()

  const entryPk = editingState.value?.pk
  const val = editValue.value
  const selectedAccountId =
    val && typeof val === 'object' && 'account' in val ? val.account : null
  const entry = (props.proTrans?.accounting_entries as ProAccountingEntry[])?.find(
    e => e.pk === entryPk,
  )

  proLedgerStore.clearSharedPickerState()

  if (entry && selectedAccountId) {
    nextTick(() => {
      pendingAccountForModal.value = selectedAccountId
      selectedEntryForSelect.value = { ...entry, account: selectedAccountId }
      selectModalType.value = type
      selectModalVisible.value = true
    })
  }
}

const handlePickerClose = async () => {
  await nextTick()

  const val = editValue.value
  if (
    editingState.value?.field === 'account_contract' &&
    val &&
    typeof val === 'object' &&
    'account' in val
  ) {
    const selectedAccount = getAccountById(val.account)

    if (!selectedAccount?.requires_contract && val.contract && allowedPeriod.value) {
      val.contract = null
    }
    if (!selectedAccount?.is_related_contractor && val.contractor && allowedPeriod.value) {
      val.contractor = null
    }

    if (selectedAccount?.requires_contract && !val.contract) {
      if (!allowedPeriod.value) {
        unlockBodyScroll()
        proLedgerStore.clearSharedPickerState()
        message(
          'warning',
          '알림!',
          '정산 마감일 이전 거래는 계약이 필수인 계정으로 변경 시 계약 정보를 함께 등록할 수 없습니다.',
        )
        return
      }
      restoreScrollAndOpenModal('contract')
      return
    }

    if (selectedAccount?.is_related_contractor && !val.contractor) {
      if (!allowedPeriod.value) {
        unlockBodyScroll()
        proLedgerStore.clearSharedPickerState()
        message(
          'warning',
          '알림!',
          '정산 마감일 이전 거래는 계약자가 필수인 계정으로 변경 시 계약자 정보를 함께 등록할 수 없습니다.',
        )
        return
      }
      restoreScrollAndOpenModal('contractor')
      return
    }
  }

  try {
    await handleUpdate()
  } finally {
    unlockBodyScroll()
    proLedgerStore.clearSharedPickerState()
  }
}

// --- Collapse/Expand State for Accounting Entries ---
const DEFAULT_VISIBLE_COUNT = 3
const visibleEntryCount = ref<number>(DEFAULT_VISIBLE_COUNT)

const totalEntryCount = computed(() => props.proTrans?.accounting_entries?.length || 0)
const shouldShowExpand = computed(() => totalEntryCount.value > DEFAULT_VISIBLE_COUNT)

const visibleEntries = computed(() => {
  if (!shouldShowExpand.value || visibleEntryCount.value >= totalEntryCount.value) {
    return props.proTrans?.accounting_entries
  }
  return props.proTrans?.accounting_entries?.slice(0, visibleEntryCount.value)
})

const remainingCount = computed(() => Math.max(0, totalEntryCount.value - visibleEntryCount.value))

const isFullyExpanded = computed(() => visibleEntryCount.value >= totalEntryCount.value)

const expandMore = () => {
  const remaining = remainingCount.value
  if (remaining <= 30) {
    visibleEntryCount.value = totalEntryCount.value
  } else if (visibleEntryCount.value < 30) {
    visibleEntryCount.value = 30
  } else {
    visibleEntryCount.value += 30
  }
}

const collapseAll = () => {
  visibleEntryCount.value = DEFAULT_VISIBLE_COUNT
}

const handleUpdate = async () => {
  const state = editingState.value
  if (!state || isUpdating || !props.proTrans?.pk) return

  const { type, pk, field } = state
  const currentValue = editValue.value

  if (type === 'tran') {
    if (pk !== props.proTrans.pk) return
    if (field === 'sort_amount') {
      if (!currentValue || typeof currentValue !== 'object' || !('amount' in currentValue)) {
        proLedgerStore.sharedEditingState = null
        return
      }
      const originalSort = props.proTrans.sort
      const originalAmount = props.proTrans.amount || 0
      const newSort = currentValue.sort
      const newAmount = Number(currentValue.amount) || 0

      if (newSort === originalSort && newAmount === originalAmount) {
        proLedgerStore.sharedEditingState = null
        return
      }
    } else {
      const originalValue = (props.proTrans[field as keyof ProBankTrans] as string) ?? ''
      if (currentValue === originalValue) {
        proLedgerStore.sharedEditingState = null
        return
      }
    }
  } else {
    const entry = (props.proTrans?.accounting_entries as ProAccountingEntry[])?.find(
      e => e.pk === pk,
    )
    if (!entry) {
      proLedgerStore.sharedEditingState = null
      return
    }

    if (field === 'account_contract') {
      if (!currentValue || typeof currentValue !== 'object' || !('account' in currentValue)) {
        proLedgerStore.sharedEditingState = null
        return
      }
      const accountUnchanged = currentValue.account === entry.account
      const contractUnchanged = !allowedPeriod.value || currentValue.contract === entry.contract
      const contractorUnchanged =
        !allowedPeriod.value || currentValue.contractor === entry.contractor
      if (accountUnchanged && contractUnchanged && contractorUnchanged) {
        proLedgerStore.sharedEditingState = null
        return
      }
    } else {
      const originalValue = (entry[field as keyof ProAccountingEntry] as string | null) ?? ''
      if (currentValue === originalValue) {
        proLedgerStore.sharedEditingState = null
        return
      }
    }
  }

  const payload: CompositeProBankTransPatchPayload = { pk: props.proTrans.pk }

  if (type === 'tran') {
    if (
      field === 'sort_amount' &&
      currentValue &&
      typeof currentValue === 'object' &&
      'amount' in currentValue
    ) {
      payload.sort = currentValue.sort
      payload.amount = Number(currentValue.amount) || 0
    } else if (field === 'note' || field === 'content') {
      payload[field] = String(currentValue ?? '')
    }
  } else if (
    field === 'account_contract' &&
    currentValue &&
    typeof currentValue === 'object' &&
    'account' in currentValue
  ) {
    // 마감된 거래에서는 account만 전송하여 백엔드 계정 단독 변경 예외(is_only_account_changed)와 정합
    payload.accounting_entries = allowedPeriod.value
      ? [
          {
            pk,
            account: currentValue.account,
            contract: currentValue.contract,
            contractor: currentValue.contractor,
          },
        ]
      : [{ pk, account: currentValue.account }]
  } else if (field === 'trader') {
    payload.accounting_entries = [{ pk, trader: String(currentValue ?? '') }]
  }

  isUpdating = true
  try {
    await proLedgerStore.patchProBankTrans(payload)
  } finally {
    isUpdating = false
    proLedgerStore.sharedEditingState = null
  }
}

onUnmounted(() => {
  const current = proLedgerStore.sharedEditingState
  if (!current) return
  const ownsState =
    (current.type === 'tran' && current.pk === props.proTrans?.pk) ||
    (current.type === 'entry' &&
      Boolean(props.proTrans?.accounting_entries?.some(e => e.pk === current.pk)))
  if (ownsState) {
    unlockBodyScroll()
    proLedgerStore.clearSharedPickerState()
  }
})
</script>

<template>
  <template v-if="proTrans">
    <CTableRow class="align-top" :color="rowColor" :data-cash-id="proTrans.pk">
      <CTableDataCell>
        <span class="text-primary">{{ proTrans.deal_date }}</span>
      </CTableDataCell>

      <!-- 비고 인라인 편집 -->
      <CTableDataCell
        :class="{
          'editable-cell-hint': allowedPeriod && !isEditing('tran', proTrans.pk!, 'note'),
          pointer: allowedPeriod && !isEditing('tran', proTrans.pk!, 'note'),
          'p-0': isEditing('tran', proTrans.pk!, 'note'),
        }"
        @dblclick="setEditing('tran', proTrans.pk!, 'note', proTrans.note ?? '')"
      >
        <CFormInput
          v-if="isEditing('tran', proTrans.pk!, 'note')"
          ref="inputRef"
          :model-value="typeof editValue === 'string' ? editValue : ''"
          @update:model-value="val => (editValue = val)"
          @blur="handleUpdate"
          @keydown.enter="handleUpdate"
          @keydown.esc="cancelEditing"
        />
        <span v-else>
          {{ cutString(proTrans.note, 20) }}
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
        <span v-if="proTrans.bank_account_name">
          {{ cutString(proTrans.bank_account_name, 10) }}
        </span>
      </CTableDataCell>

      <!-- Content 인라인 편집 -->
      <CTableDataCell
        :class="{
          truncate: true,
          'editable-cell-hint': allowedPeriod && !isEditing('tran', proTrans.pk!, 'content'),
          pointer: allowedPeriod && !isEditing('tran', proTrans.pk!, 'content'),
          'p-0': isEditing('tran', proTrans.pk!, 'content'),
        }"
        @dblclick="setEditing('tran', proTrans.pk!, 'content', proTrans.content ?? '')"
      >
        <CFormInput
          v-if="isEditing('tran', proTrans.pk!, 'content')"
          ref="inputRef"
          :model-value="typeof editValue === 'string' ? editValue : ''"
          @update:model-value="val => (editValue = val)"
          @blur="handleUpdate"
          @keydown.enter="handleUpdate"
          @keydown.esc="cancelEditing"
        />
        <span v-else>
          {{ cutString(proTrans.content, 15) }}
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
          'editable-cell-hint': allowedPeriod && !isEditing('tran', proTrans.pk!, 'sort_amount'),
          pointer: allowedPeriod && !isEditing('tran', proTrans.pk!, 'sort_amount'),
          'p-0': isEditing('tran', proTrans.pk!, 'sort_amount'),
        }"
        @dblclick="
          setEditing('tran', proTrans.pk!, 'sort_amount', {
            sort: proTrans.sort,
            amount: proTrans.amount || 0,
          })
        "
      >
        <div
          v-if="isEditing('tran', proTrans.pk!, 'sort_amount') && editValue"
          class="d-flex align-items-center justify-content-end"
        >
          <v-chip :color="proTrans.sort === 1 ? 'primary' : 'danger'" size="x-small" class="me-2">
            {{ proTrans.sort === 1 ? '입금' : '출금' }}
          </v-chip>

          <CFormInput
            ref="inputRef"
            v-model.number="sortAmountModel"
            type="number"
            style="width: 120px"
            @blur="handleUpdate"
            @keydown.enter="handleUpdate"
            @keydown.esc="cancelEditing"
          />
        </div>
        <div v-else>
          <span :class="proTrans.sort === 1 ? 'text-success strong' : ''">
            {{ proTrans.sort === 1 ? '+' : '-' }}{{ numFormat(proTrans.amount || 0) }}
          </span>
          <v-icon
            v-if="allowedPeriod"
            icon="mdi-pencil-outline"
            size="14"
            color="success"
            class="inline-edit-icon"
          />
        </div>
      </CTableDataCell>

      <CTableDataCell class="text-center">
        <v-icon v-if="proTrans.is_balanced" icon="mdi-check-circle" color="success" size="sm" />
        <v-icon v-else icon="mdi-minus-circle" color="danger" size="sm" />
      </CTableDataCell>

      <CTableDataCell :colspan="canLedgerEdit ? 5 : 4" class="p-0">
        <CTable class="m-0 p-0">
          <colgroup>
            <col style="width: 28%" />
            <col style="width: 26%" />
            <col style="width: 16%" />
            <col style="width: 24%" />
            <col v-if="canLedgerEdit" style="width: 6%" />
          </colgroup>
          <CTableRow
            v-for="entry in visibleEntries"
            :key="entry.pk"
            :class="isImprest ? 'bg-amber-lighten-5' : 'bg-lime-lighten-5'"
          >
            <CTableDataCell
              :class="[
                'account-cell',
                isImprest ? 'bg-amber-lighten-4' : 'bg-lime-lighten-4',
                {
                  'editable-cell-hint':
                    canLedgerEdit && !isEditing('entry', entry.pk, 'account_contract'),
                  pointer: canLedgerEdit && !isEditing('entry', entry.pk, 'account_contract'),
                },
              ]"
              style="position: relative"
            >
              <div
                class="d-flex align-items-center justify-content-between bg-transparent"
                :class="{
                  pointer: canLedgerEdit && !isEditing('entry', entry.pk, 'account_contract'),
                }"
                @click="handleAccountClick(entry, $event)"
              >
                <div class="d-flex align-items-center">
                  <span>{{ cutString(entry.account_name, 12) }}</span>
                  <!-- 계약정보 표시 (편집 가능) -->
                  <v-tooltip v-if="entry.contract && allowedPeriod" location="top">
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-book-open"
                        color="indigo-lighten-2"
                        size="16"
                        class="ms-1 pointer"
                        @click.stop="openSelectModal(entry, 'contract')"
                      />
                    </template>
                    <div class="pa-2">
                      <div class="fw-bold mb-1">관련 계약정보</div>
                      <div class="mb-2">{{ entry.contract_display }}</div>
                      <div class="d-flex align-items-center text-amber fw-medium">
                        <v-icon icon="mdi-pencil" size="14" class="me-1" />
                        클릭하여 변경
                      </div>
                    </div>
                  </v-tooltip>
                  <!-- 계약정보 표시 (읽기 전용) -->
                  <v-tooltip v-else-if="entry.contract && !allowedPeriod" location="top">
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-book-open"
                        color="indigo-lighten-2"
                        size="16"
                        class="ms-1"
                      />
                    </template>
                    <div class="pa-2">
                      <div class="fw-bold mb-1">관련 계약정보</div>
                      <div>{{ entry.contract_display }}</div>
                    </div>
                  </v-tooltip>
                  <!-- 계약정보 설정 필요 아이콘 -->
                  <v-tooltip
                    v-else-if="getAccountById(entry.account)?.requires_contract && allowedPeriod"
                    location="top"
                  >
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-book-open"
                        color="warning"
                        size="16"
                        class="ms-1 pointer"
                        @click.stop="openSelectModal(entry, 'contract')"
                      />
                    </template>
                    <span>계약정보를 선택하세요</span>
                  </v-tooltip>

                  <!-- 계약자 정보 표시 (편집 가능) -->
                  <v-tooltip v-if="entry.contractor && allowedPeriod" location="top">
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-account-cog"
                        color="purple-lighten-2"
                        size="16"
                        class="ms-1 pointer"
                        @click.stop="openSelectModal(entry, 'contractor')"
                      />
                    </template>
                    <div class="pa-2">
                      <div class="fw-bold mb-1">관련 계약자</div>
                      <div class="mb-2">{{ entry.contractor_display }}</div>
                      <div class="d-flex align-items-center text-amber fw-medium">
                        <v-icon icon="mdi-pencil" size="14" class="me-1" />
                        클릭하여 변경
                      </div>
                    </div>
                  </v-tooltip>
                  <!-- 계약자 정보 표시 (읽기 전용) -->
                  <v-tooltip v-else-if="entry.contractor && !allowedPeriod" location="top">
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-account-cog"
                        color="purple-lighten-2"
                        size="16"
                        class="ms-1"
                      />
                    </template>
                    <div class="pa-2">
                      <div class="fw-bold mb-1">관련 계약자</div>
                      <div>{{ entry.contractor_display }}</div>
                    </div>
                  </v-tooltip>
                  <!-- 계약자 설정 필요 아이콘 -->
                  <v-tooltip
                    v-else-if="
                      getAccountById(entry.account)?.is_related_contractor && allowedPeriod
                    "
                    location="top"
                  >
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-account-cog"
                        color="warning"
                        size="16"
                        class="ms-1 pointer"
                        @click.stop="openSelectModal(entry, 'contractor')"
                      />
                    </template>
                    <span>계약자를 선택하세요</span>
                  </v-tooltip>
                </div>
                <v-icon
                  v-if="canLedgerEdit && !isEditing('entry', entry.pk, 'account_contract')"
                  icon="mdi-chevron-down"
                  size="16"
                  color="grey"
                />
              </div>

              <!-- 계정 선택 Picker (Teleport to body) -->
              <Teleport to="body">
                <LedgerAccountPicker
                  v-if="
                    isEditing('entry', entry.pk, 'account_contract') && editValue && pickerPosition
                  "
                  v-model="accountContractModel"
                  :options="proAccounts ?? []"
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
              <span v-else class="bg-transparent">
                {{ cutString(entry.trader, 12) }}
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
              :class="proTrans.sort === 1 ? 'text-success strong' : ''"
            >
              {{ proTrans.sort === 1 ? '+' : '-' }}{{ numFormat(entry.amount) }}
            </CTableDataCell>
            <CTableDataCell class="ps-3">
              {{ cutString(entry.evidence_type_display, 10) }}
            </CTableDataCell>
            <CTableDataCell v-if="canLedgerEdit" class="text-end pe-2">
              <v-icon
                v-if="allowedPeriod"
                icon="mdi-pencil"
                size="18"
                @click="
                  router.push({
                    name: editRouteName,
                    params: { transId: proTrans.pk },
                  })
                "
                class="pointer edit-icon-hover"
              />
            </CTableDataCell>
          </CTableRow>

          <!-- Expand/Collapse Controls Row -->
          <CTableRow v-if="shouldShowExpand" class="bg-grey-lighten-4">
            <CTableDataCell :colspan="canLedgerEdit ? 5 : 4" class="text-center py-2">
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

              <v-btn v-else variant="text" size="small" color="grey" @click="collapseAll">
                <v-icon icon="mdi-chevron-up" size="18" class="me-1" />
                접기
              </v-btn>

              <span class="text-caption text-grey ms-3">
                {{ visibleEntryCount }} / {{ totalEntryCount }} 표시 중
              </span>
            </CTableDataCell>
          </CTableRow>
        </CTable>
      </CTableDataCell>
    </CTableRow>

    <!-- 계약정보/계약자 선택 모달 -->
    <BaseSelectModal
      v-model="selectModalVisible"
      :type="selectModalType"
      :contract="selectedEntryForSelect?.contract"
      :contractor="selectedEntryForSelect?.contractor"
      :account-name="selectedEntryForSelect?.account_name"
      @select="handleSelect"
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

.contract-select {
  position: relative;
  z-index: 1;
}

.dark-theme .bg-lime-lighten-5 {
  background-color: #525342 !important;
  color: #fff !important;
}

.dark-theme .bg-lime-lighten-4 {
  background-color: #424337 !important;
  color: #fff !important;
}

.dark-theme .bg-amber-lighten-5 {
  background-color: #4c4a43 !important;
  color: #fff !important;
}

.dark-theme .bg-amber-lighten-4 {
  background-color: #43413c !important;
  color: #fff !important;
}

.dark-theme .bg-grey-lighten-4 {
  background-color: #2f3349 !important;
  color: #fff !important;
}
</style>
