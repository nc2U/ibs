<script lang="ts" setup>
import { computed, type ComputedRef, inject, nextTick, type PropType, ref } from 'vue'
import { useRouter } from 'vue-router'
import { cutString, diffDate, numFormat } from '@/utils/baseMixins'
import { write_project_cash } from '@/utils/pageAuth'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import type { AccountPicker } from '@/store/types/comLedger.ts'
import type { ProAccountingEntry, ProBankTrans } from '@/store/types/proLedger.ts'
import LedgerAccountPicker from '@/components/LedgerAccount/Picker.vue'
import BaseSelectModal from './BaseSelectModal.vue'

const props = defineProps({
  proTrans: { type: Object as PropType<ProBankTrans>, required: true },
  calculated: { type: String, default: '2000-01-01' },
  isHighlighted: { type: Boolean, default: false },
})

const router = useRouter()
const proLedgerStore = useProLedger()

const rowColor = computed(() => (props.isHighlighted ? 'warning' : ''))

const superAuth = inject('superAuth')
const allowedPeriod = computed(
  () =>
    (superAuth as any).value ||
    (write_project_cash && diffDate(props.proTrans.deal_date, new Date(props.calculated)) <= 10),
)

const proAccounts = inject<ComputedRef<AccountPicker[]>>('proAccounts')

// 선택된 account가 contract를 요구하는지 확인
const getAccountById = (accountId: number | null | undefined): AccountPicker | undefined => {
  if (!accountId || !proAccounts?.value) return undefined
  return proAccounts.value.find(acc => acc.value === accountId)
}

const sortType = computed(() => {
  if (props.proTrans.sort === 1) return 'deposit' // 입금
  if (props.proTrans.sort === 2) return 'withdraw' // 출금
  return null // 전체
})

// --- 계약/계약자 정보 선택 모달 (통합) ---
const selectModalVisible = ref(false)
const selectModalType = ref<'contract' | 'contractor'>('contract')
const selectedEntryForSelect = ref<ProAccountingEntry | null>(null)

const openSelectModal = (entry: ProAccountingEntry, type: 'contract' | 'contractor') => {
  if (!allowedPeriod.value) return
  selectedEntryForSelect.value = entry
  selectModalType.value = type
  selectModalVisible.value = true
}

const handleSelect = async (id: number | null) => {
  if (!selectedEntryForSelect.value) return

  const entry = selectedEntryForSelect.value
  const accountToSave = editValue.value?.account || entry.account
  const type = selectModalType.value

  const payload: any = {
    pk: props.proTrans.pk!,
    accounting_entries: [
      {
        pk: entry.pk,
        account: accountToSave,
        [type]: id, // 'contract' 또는 'contractor'
      },
    ],
  }

  try {
    await proLedgerStore.patchProBankTrans(payload)
  } finally {
    editValue.value = null
    selectedEntryForSelect.value = null
  }
}

// --- 제네릭 인라인 편집을 위한 상태 및 로직 ---
const editingState = computed(() => proLedgerStore.sharedEditingState) // Use computed for reactivity
const editValue = ref<any>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const pickerPosition = computed(() => proLedgerStore.sharedPickerPosition) // Use computed for reactivity

const setEditing = (type: 'tran' | 'entry', pk: number, field: string, value: any) => {
  if (!allowedPeriod.value) return
  proLedgerStore.sharedEditingState = { type, pk, field } // Update shared state
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

const handleAccountClick = (entry: ProAccountingEntry, event: MouseEvent) => {
  event.stopPropagation()

  // 현재 항목이 이미 편집 중이라면 → 닫기 (토글)
  // 이 경우 handlePickerClose()는 상태 초기화와 동시에 handleUpdate()를 호출하여 저장 시도
  if (isEditing('entry', entry.pk!, 'account_contract')) {
    handlePickerClose()
    return
  }

  // 다른 Picker가 열려있는 상태라면 → 다른 Picker 닫기 (저장 없이)
  if (proLedgerStore.sharedEditingState) {
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

    proLedgerStore.clearSharedPickerState() // 공유 상태를 즉시 클리어

    // 다른 Picker를 닫고 함수를 종료. 새 Picker는 다음 클릭에 열림.
    return
  }

  // 열려있는 Picker가 없으면 → 새 Picker 열기
  const target = event.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()

  // 공유 pickerPosition 업데이트
  proLedgerStore.sharedPickerPosition = {
    top: rect.bottom,
    left: rect.left,
    width: rect.width,
  }

  // setEditing 함수를 통해 공유 editingState 업데이트
  setEditing('entry', entry.pk!, 'account_contract', {
    account: entry.account,
    contract: entry.contract,
    contractor: entry.contractor,
  })

  // 스크롤 제한 - body와 html 모두 제어
  const scrollY = window.scrollY
  document.documentElement.style.overflow = 'hidden'
  document.body.style.overflow = 'hidden'
  document.body.style.position = 'fixed'
  document.body.style.top = `-${scrollY}px`
  document.body.style.width = '100%'
}

// 스크롤 복원 + 모달 열기 (공통 로직)
const restoreScrollAndOpenModal = (type: 'contract' | 'contractor') => {
  const scrollY = document.body.style.top
  const scrollValue = scrollY ? parseInt(scrollY || '0') * -1 : 0

  document.body.style.position = ''
  document.body.style.top = ''
  window.scrollTo(0, scrollValue)
  document.documentElement.style.overflow = ''
  document.body.style.overflow = ''
  document.body.style.width = ''

  const entryPk = editingState.value?.pk
  const selectedAccountId = editValue.value.account
  const entry = props.proTrans.accounting_entries?.find(e => e.pk === entryPk)

  proLedgerStore.clearSharedPickerState()

  if (entry) {
    nextTick(() => {
      selectedEntryForSelect.value = { ...entry, account: selectedAccountId }
      selectModalType.value = type
      selectModalVisible.value = true
    })
  }
}

const handlePickerClose = async () => {
  await nextTick()

  if (editingState.value?.field === 'account_contract' && editValue.value) {
    const selectedAccount = getAccountById(editValue.value.account)

    // 계약정보가 필요 없는 계정으로 변경한 경우 → contract를 null로 초기화
    if (!selectedAccount?.requires_contract && editValue.value.contract) {
      editValue.value.contract = null
    }

    // 계약자 정보가 필요 없는 계정으로 변경한 경우 → contractor를 null로 초기화
    if (!selectedAccount?.is_related_contractor && editValue.value.contractor) {
      editValue.value.contractor = null
    }

    // 계약정보가 필요한데 설정되지 않은 경우
    if (selectedAccount?.requires_contract && !editValue.value.contract) {
      restoreScrollAndOpenModal('contract')
      return
    }

    // 계약자 정보가 필요한데 설정되지 않은 경우
    if (selectedAccount?.is_related_contractor && !editValue.value.contractor) {
      restoreScrollAndOpenModal('contractor')
      return
    }
  }

  await handleUpdate()

  // 스크롤 복원
  const scrollY = document.body.style.top
  const scrollValue = scrollY ? parseInt(scrollY || '0') * -1 : 0

  document.body.style.position = ''
  document.body.style.top = ''
  window.scrollTo(0, scrollValue)
  document.documentElement.style.overflow = ''
  document.body.style.overflow = ''
  document.body.style.width = ''

  proLedgerStore.clearSharedPickerState()
}

// --- Collapse/Expand State for Accounting Entries ---
const DEFAULT_VISIBLE_COUNT = 10
const visibleEntryCount = ref<number>(DEFAULT_VISIBLE_COUNT)

const totalEntryCount = computed(() => props.proTrans.accounting_entries?.length || 0)
const shouldShowExpand = computed(() => totalEntryCount.value > DEFAULT_VISIBLE_COUNT)

const visibleEntries = computed(() => {
  if (!shouldShowExpand.value || visibleEntryCount.value >= totalEntryCount.value) {
    return props.proTrans.accounting_entries
  }
  return props.proTrans.accounting_entries?.slice(0, visibleEntryCount.value)
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

const handleUpdate = async () => {
  if (!editingState.value) return

  const { type, pk, field } = editingState.value

  if (type === 'tran') {
    if (field === 'sort_amount') {
      const originalSort = props.proTrans.sort
      const originalAmount = props.proTrans.amount || 0
      const newSort = editValue.value.sort
      const newAmount = Number(editValue.value.amount) || 0

      if (newSort === originalSort && newAmount === originalAmount) {
        proLedgerStore.sharedEditingState = null
        return
      }
    } else {
      const originalValue = props.proTrans[field as keyof ProBankTrans]
      if (editValue.value === originalValue) {
        proLedgerStore.sharedEditingState = null
        return
      }
    }
  } else {
    const entry = props.proTrans.accounting_entries?.find(e => e.pk === pk)
    if (!entry) {
      proLedgerStore.sharedEditingState = null // No entry found, cancel editing
      return
    }

    if (field === 'sort_amount') {
      const originalSort = props.proTrans.sort
      const originalAmount = props.proTrans.amount || 0
      const newSort = editValue.value.sort
      const newAmount = Number(editValue.value.amount) || 0

      if (newSort === originalSort && newAmount === originalAmount) {
        proLedgerStore.sharedEditingState = null
        return
      }
    } else if (field === 'account_contract') {
      const originalAccount = entry.account
      const originalContract = entry.contract
      const originalContractor = entry.contractor
      const newAccount = editValue.value.account
      const newContract = editValue.value.contract
      const newContractor = editValue.value.contractor

      if (
        newAccount === originalAccount &&
        newContract === originalContract &&
        newContractor === originalContractor
      ) {
        proLedgerStore.sharedEditingState = null
        return
      }
    } else {
      // For other single entry fields
      const originalValue = entry[field as keyof ProAccountingEntry]
      if (editValue.value === originalValue) {
        proLedgerStore.sharedEditingState = null
        return
      }
    }
  }

  const payload: { pk: number; [key: string]: any } = { pk: props.proTrans.pk! }

  if (type === 'tran') {
    if (field === 'sort_amount') {
      payload.sort = editValue.value.sort
      payload.amount = Number(editValue.value.amount) || 0
    } else {
      payload[field] = editValue.value
    }
  } else {
    // type === 'entry'
    if (field === 'account_contract') {
      payload.accounting_entries = [
        {
          pk: pk,
          account: editValue.value.account,
          contract: editValue.value.contract,
          contractor: editValue.value.contractor,
        },
      ]
    } else {
      payload.accounting_entries = [{ pk: pk, [field]: editValue.value }]
    }
  }

  try {
    await proLedgerStore.patchProBankTrans(payload)
  } finally {
    proLedgerStore.sharedEditingState = null
  }
}
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
          'editable-cell-hint': !isEditing('tran', proTrans.pk!, 'note'),
          pointer: !isEditing('tran', proTrans.pk!, 'note'),
          'p-0': isEditing('tran', proTrans.pk!, 'note'),
        }"
        @dblclick="setEditing('tran', proTrans.pk!, 'note', proTrans.note)"
      >
        <CFormInput
          v-if="isEditing('tran', proTrans.pk!, 'note')"
          ref="inputRef"
          v-model="editValue"
          @blur="handleUpdate"
          @keydown.enter="handleUpdate"
        />
        <span v-else>
          {{ cutString(proTrans.note, 20) }}
          <v-icon icon="mdi-pencil-outline" size="14" color="success" class="inline-edit-icon" />
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
          'editable-cell-hint': !isEditing('tran', proTrans.pk!, 'content'),
          pointer: !isEditing('tran', proTrans.pk!, 'content'),
          'p-0': isEditing('tran', proTrans.pk!, 'content'),
        }"
        @dblclick="setEditing('tran', proTrans.pk!, 'content', proTrans.content)"
      >
        <CFormInput
          v-if="isEditing('tran', proTrans.pk!, 'content')"
          ref="inputRef"
          v-model="editValue"
          @blur="handleUpdate"
          @keydown.enter="handleUpdate"
        />
        <span v-else>
          {{ cutString(proTrans.content, 15) }}
          <v-icon icon="mdi-pencil-outline" size="14" color="success" class="inline-edit-icon" />
        </span>
      </CTableDataCell>

      <CTableDataCell
        class="text-right"
        :class="{
          'editable-cell-hint': !isEditing('tran', proTrans.pk!, 'sort_amount'),
          pointer: !isEditing('tran', proTrans.pk!, 'sort_amount'),
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
          v-if="isEditing('tran', proTrans.pk!, 'sort_amount')"
          class="d-flex align-items-center justify-content-end"
        >
          <v-btn-toggle
            v-model="editValue.sort"
            variant="elevated"
            color="success"
            density="compact"
            divided
          >
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
          <span :class="proTrans.sort === 1 ? 'text-success strong' : ''">
            {{ proTrans.sort === 1 ? '+' : '-' }}{{ numFormat(proTrans.amount || 0) }}
          </span>
          <v-icon icon="mdi-pencil-outline" size="14" color="success" class="inline-edit-icon" />
        </div>
      </CTableDataCell>

      <CTableDataCell class="text-center">
        <v-icon v-if="proTrans.is_balanced" icon="mdi-check-circle" color="success" size="sm" />
        <v-icon v-else icon="mdi-minus-circle" color="danger" size="sm" />
      </CTableDataCell>

      <CTableDataCell colspan="6" class="p-0">
        <CTable class="m-0 p-0">
          <colgroup>
            <col style="width: 28%" />
            <col style="width: 26%" />
            <col style="width: 16%" />
            <col style="width: 24%" />
            <col v-if="write_project_cash" style="width: 6%" />
          </colgroup>
          <CTableRow v-for="entry in visibleEntries" :key="entry.pk" class="bg-amber-lighten-5">
            <CTableDataCell
              :class="{
                'account-cell': true,
                'editable-cell-hint': !isEditing('entry', entry.pk!, 'account_contract'),
                pointer: !isEditing('entry', entry.pk!, 'account_contract'),
              }"
              class="bg-amber-lighten-4"
              style="position: relative"
            >
              <div
                class="d-flex align-items-center justify-content-between bg-transparent"
                :class="{ pointer: !isEditing('entry', entry.pk!, 'account_contract') }"
                @click="handleAccountClick(entry, $event)"
              >
                <div class="d-flex align-items-center">
                  <span>{{ cutString(entry.account_name, 12) }}</span>
                  <!-- 계약정보 정보 표시 (이미 설정된 경우) - 클릭 가능 -->
                  <v-tooltip v-if="entry.contract && allowedPeriod" location="top">
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-book-open"
                        color="indigo-lighten-2"
                        size="16"
                        class="ml-1 pointer"
                        @click.stop="openSelectModal(entry, 'contract')"
                      />
                    </template>
                    <div class="pa-2">
                      <div class="font-weight-bold mb-1">관련 계약정보</div>
                      <div class="mb-2">{{ entry.contract_display }}</div>
                      <div class="d-flex align-items-center text-amber font-weight-medium">
                        <v-icon icon="mdi-pencil" size="14" class="mr-1" />
                        클릭하여 변경
                      </div>
                    </div>
                  </v-tooltip>
                  <!-- 계약 정보 표시 (읽기 전용) -->
                  <v-tooltip v-else-if="entry.contract && !allowedPeriod" location="top">
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-book-open"
                        color="indigo-lighten-2"
                        size="16"
                        class="ml-1"
                      />
                    </template>
                    <div class="pa-2">
                      <div class="font-weight-bold mb-1">관련 계약정보</div>
                      <div>{{ entry.contract_display }}</div>
                    </div>
                  </v-tooltip>
                  <!-- 계약정보 설정 필요 아이콘 (설정 필요하지만 없는 경우) -->
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
                        class="ml-1 pointer"
                        @click.stop="openSelectModal(entry, 'contract')"
                      />
                    </template>
                    <span>계약정보를 선택하세요</span>
                  </v-tooltip>

                  <!-- 계약자 정보 표시 (이미 설정된 경우) - 클릭 가능 -->
                  <v-tooltip v-if="entry.contractor && allowedPeriod" location="top">
                    <template v-slot:activator="{ props: tooltipProps }">
                      <v-icon
                        v-bind="tooltipProps"
                        icon="mdi-account-cog"
                        color="purple-lighten-2"
                        size="16"
                        class="ml-1 pointer"
                        @click.stop="openSelectModal(entry, 'contractor')"
                      />
                    </template>
                    <div class="pa-2">
                      <div class="font-weight-bold mb-1">관련 계약자</div>
                      <div class="mb-2">{{ entry.contractor_display }}</div>
                      <div class="d-flex align-items-center text-amber font-weight-medium">
                        <v-icon icon="mdi-pencil" size="14" class="mr-1" />
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
                        class="ml-1"
                      />
                    </template>
                    <div class="pa-2">
                      <div class="font-weight-bold mb-1">관련 계약자</div>
                      <div>{{ entry.contractor_display }}</div>
                    </div>
                  </v-tooltip>
                  <!-- 계약자 설정 필요 아이콘 (설정 필요하지만 없는 경우) -->
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
                        class="ml-1 pointer"
                        @click.stop="openSelectModal(entry, 'contractor')"
                      />
                    </template>
                    <span>계약자를 선택하세요</span>
                  </v-tooltip>
                </div>
                <v-icon
                  v-if="!isEditing('entry', entry.pk!, 'account_contract')"
                  icon="mdi-chevron-down"
                  size="16"
                  color="grey"
                />
              </div>

              <!-- 계정 선택 Picker (Teleport to body) -->
              <Teleport to="body">
                <LedgerAccountPicker
                  v-if="
                    isEditing('entry', entry.pk!, 'account_contract') && editValue && pickerPosition
                  "
                  v-model="editValue.account"
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
              :class="proTrans.sort === 1 ? 'text-success strong' : ''"
            >
              {{ proTrans.sort === 1 ? '+' : '-' }}{{ numFormat(entry.amount) }}
            </CTableDataCell>
            <CTableDataCell class="pl-3">
              {{ cutString(entry.evidence_type_display, 10) }}
            </CTableDataCell>
            <CTableDataCell v-if="write_project_cash" class="text-right pr-2">
              <v-icon
                v-if="allowedPeriod"
                icon="mdi-pencil"
                size="18"
                @click="
                  router.push({
                    name: '운영 계좌 내역 - 수정',
                    params: { transId: proTrans.pk },
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

.dark-theme .bg-amber-lighten-5 {
  background-color: #4c4a43 !important;
  color: #fff !important;
}

.dark-theme .bg-amber-lighten-4 {
  background-color: #43413c !important;
  color: #fff !important;
}
</style>
