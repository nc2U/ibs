<script lang="ts" setup>
import { computed, onBeforeMount, provide, reactive, ref, watch } from 'vue'
import { isValidate, message } from '@/utils/helper.ts'
import { getToday, numFormat } from '@/utils/baseMixins.ts'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import { usePerms } from '@/composables/usePerms'
import type { ParseResult } from '@/composables/useExcelUpload'
import { useExcelUpload } from '@/composables/useExcelUpload'
import { type BulkParseResult, useBulkTransExcel } from '@/composables/useBulkTransExcel'
import { bgLight, TableSecondary } from '@/utils/cssMixins.ts'
import type {
  BankTransaction,
  CompositeAccountingEntryPayload,
  CompositeTransactionPayload,
  CompositeTransactionPatchPayload,
} from '@/store/types/comLedger'
import BankTransactionRow, { type BankTransactionData } from './BankTransactionRow.vue'
import BulkTransUploadDialog from '@/views/proLedger/Manage/components/BulkTransUploadDialog.vue'
import ExcelUploadDialog from '@/components/LedgerAccount/ExcelUploadDialog.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import AccountManage from './AccountManage.vue'
import JournalRow, { type NewEntryForm } from './JournalRow.vue'
import BankAcc from './BankAcc.vue'

class ClientValidationError extends Error {}

const props = defineProps({
  company: { type: Number, default: null },
})

const { canGlobal, PERM } = usePerms()
const canComLedgerCreate = computed(() => canGlobal(PERM.HQ_LEDGER_CREATE))
const canComLedgerUpdate = computed(() => canGlobal(PERM.HQ_LEDGER_UPDATE))
const canComLedgerDelete = computed(() => canGlobal(PERM.HQ_LEDGER_DELETE))
const canComLedgerManage = computed(() => canGlobal(PERM.HQ_LEDGER_MANAGE))
const canComLedgerEdit = computed(() =>
  isCreateMode.value
    ? canComLedgerCreate.value || canComLedgerManage.value
    : canComLedgerUpdate.value || canComLedgerManage.value,
)
const canComLedgerRemove = computed(() => canComLedgerDelete.value || canComLedgerManage.value)

const confirmModal = ref()
const leaveConfirmModal = ref()
const alertModal = ref()
const refAccountManage = ref()
const refBankAcc = ref()

const [route, router] = [useRoute(), useRouter()]

const transId = computed(() => Number(route.params.transId) || null)
const isCreateMode = computed(() => !transId.value)
const isSaving = ref(false)
const skipLeaveGuard = ref(false)
let pendingLeaveResolve: ((allowed: boolean) => void) | null = null

const ledgerStore = useComLedger()
const transferFeePk = computed(() => ledgerStore.transferFeePk)
const transaction = computed(() => ledgerStore.bankTransaction as BankTransaction | null)
provide('transferFeePk', transferFeePk)
provide(
  'affiliates',
  computed(() => ledgerStore.affiliates),
)
provide(
  'comAccounts',
  computed(() => ledgerStore.comAccounts),
)

const accountMap = computed(() => {
  const map = new Map<number, (typeof ledgerStore.comAccounts)[number]>()
  for (const acc of ledgerStore.comAccounts) {
    map.set(acc.value, acc)
  }
  return map
})

watch(
  () => props.company,
  async (newVal, oldVal) => {
    if (!oldVal || newVal === oldVal) return
    if (isCreateMode.value) initializeCreateForm()
    else await router.push({ name: '본사 거래 내역' })
  },
)

// 은행 거래 폼 데이터 (수정 모드 및 단일 생성 폴백용)
interface BankTransactionForm {
  deal_date: string
  note: string
  bank_account: number | null | ''
  content: string
  sort: 1 | 2
  amount: number | null
}

const validated = ref(false)
provide('validated', validated)
const bankForm = reactive<BankTransactionForm>({
  deal_date: getToday(),
  sort: 2,
  amount: null,
  content: '',
  note: '',
  bank_account: '',
})

// 수정 가능한 폼 데이터 (기존 데이터 + 새로운 데이터)
const editableEntries = ref<NewEntryForm[]>([])
const initialEditSnapshot = ref<string>('')

// 다중 은행 거래 데이터 (신규 모드용)
const bankTransactions = ref<BankTransactionData[]>([])
let nextTransUid = 1
const createNewTransaction = (data?: Partial<BankTransactionData>): BankTransactionData => ({
  uid: nextTransUid++,
  bankForm: data?.bankForm || {
    deal_date: getToday(),
    note: '',
    bank_account: '',
    content: '',
    sort: 2,
    amount: null,
  },
  entries: data?.entries || [{}],
})

const serializeEditState = () =>
  JSON.stringify({
    bankForm: { ...bankForm },
    entries: editableEntries.value.map(e => ({
      pk: e.pk ?? null,
      account: e.account ?? null,
      trader: e.trader ?? '',
      amount: e.amount ?? null,
      affiliate: e.affiliate ?? null,
      evidence_type: e.evidence_type ?? '',
    })),
  })

// 폼 초기화 함수들
const initializeCreateForm = () => {
  Object.assign(bankForm, {
    deal_date: getToday(),
    bank_account: '',
    amount: null,
    sort: 2,
    content: '',
    note: '',
  })
  editableEntries.value = [{}]
  initialEditSnapshot.value = ''
  bankTransactions.value = [createNewTransaction()]
}

const initializeEditForm = () => {
  if (!transaction.value) return

  Object.assign(bankForm, {
    deal_date: transaction.value.deal_date,
    note: transaction.value.note ?? '',
    bank_account: transaction.value.bank_account,
    content: transaction.value.content ?? '',
    sort: transaction.value.sort,
    amount: transaction.value.amount,
  })

  if (transaction.value.accounting_entries?.length) {
    editableEntries.value = transaction.value.accounting_entries.map(entry => ({
      pk: entry.pk,
      account: entry.account,
      trader: entry.trader ?? '',
      amount: entry.amount,
      affiliate: entry.affiliate ?? null,
      evidence_type: entry.evidence_type ?? '',
    }))
  } else {
    editableEntries.value = [{}]
  }

  initialEditSnapshot.value = serializeEditState()
}

// Watch transaction data to reinitialize form when loaded
watch(
  () => transaction.value,
  val => {
    if (val && !isCreateMode.value) {
      initializeEditForm()
    }
  },
)

// 표시할 행 목록
const displayRows = computed(() => editableEntries.value)

// 은행 거래 금액 (신규 모드: 전체 거래건 합계, 수정 모드: 단일 거래 금액)
const bankAmount = computed(() => {
  if (isCreateMode.value) {
    return bankTransactions.value.reduce((sum, t) => sum + (Number(t.bankForm.amount) || 0), 0)
  }
  return bankForm.amount || 0
})

// 거래 구분 이름
const sortName = computed(() => {
  if (isCreateMode.value) return ''
  return transaction.value?.sort_name || ''
})

// 분류 금액 합계 계산
const totalEntryAmount = computed(() => {
  if (isCreateMode.value) {
    return bankTransactions.value.reduce(
      (sum, t) => sum + t.entries.reduce((s, row) => s + (Number(row.amount) || 0), 0),
      0,
    )
  }
  return editableEntries.value.reduce((sum, row) => sum + (Number(row.amount) || 0), 0)
})

// 차액 계산 - bankAmount 사용
const difference = computed(() => bankAmount.value - totalEntryAmount.value)

// 금액 일치 여부
const isBalanced = computed(() => difference.value === 0)

// 은행 계좌 목록
const formBankAccounts = computed(() => {
  const activeBanks = ledgerStore.getComBanks

  if (isCreateMode.value) {
    // 신규 등록 시에는 활성 계좌만 표시
    return activeBanks
  }

  // 수정 모드일 때
  const currentBankId = transaction.value?.bank_account
  if (!currentBankId) {
    return activeBanks // 거래에 계좌 정보가 없는 경우
  }

  const isBankInActiveList = activeBanks.some(b => b.value === currentBankId)
  if (isBankInActiveList) {
    return activeBanks // 현재 거래 계좌가 활성 목록에 이미 있으면 그대로 반환
  }

  // 현재 거래 계좌가 활성 목록에 없는 경우 (비활성/숨김 상태)
  // 전체 계좌 목록에서 찾아서 추가
  const currentBank = ledgerStore.allComBankList.find(b => b.pk === currentBankId)
  if (currentBank) {
    const currentBankOption = {
      value: currentBank.pk,
      label: `${currentBank.alias_name} (비활성/숨김)`,
    }
    // 비활성 계좌를 목록 맨 위에 추가하고, 나머지는 활성 계좌 목록
    return [currentBankOption, ...activeBanks]
  }

  return activeBanks // 혹시 전체 목록에도 없으면 활성 목록만 반환
})

// === 엑셀: 1건의 은행거래에 대한 다수 회계 계정 입력 ===
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadDialogVisible = ref(false)
const parseResult = ref<ParseResult | null>(null)
const { parseExcelFile, downloadTemplate } = useExcelUpload()

// 업로드/다운로드 대상 거래건 (신규 모드: 행 index, 수정 모드: 단일 거래건)
const uploadTargetIndex = ref<number>(0)
const targetEntries = computed<NewEntryForm[]>(() =>
  isCreateMode.value
    ? (bankTransactions.value[uploadTargetIndex.value]?.entries ?? [])
    : editableEntries.value,
)
const targetAmount = computed(() =>
  isCreateMode.value
    ? bankTransactions.value[uploadTargetIndex.value]?.bankForm.amount || 0
    : bankForm.amount || 0,
)

// ID → 이름 변환 (엑셀 표기/매칭용)
const resolveEntryNames = (entry: NewEntryForm) => {
  const account = ledgerStore.comAccounts.find(acc => acc.value === entry.account)
  const affiliate = ledgerStore.affiliates.find(a => a.value === entry.affiliate)
  return { account_name: account?.label || '', affiliate_name: affiliate?.label || '' }
}

// Download template handler
const handleDownloadTemplate = (index = 0) => {
  uploadTargetIndex.value = index
  const entries = targetEntries.value.map(entry => ({
    ...resolveEntryNames(entry),
    description: '', // Not used in NewEntryForm
    trader: entry.trader || '',
    amount: entry.amount || 0,
    evidence_type: entry.evidence_type || '',
  }))

  downloadTemplate({ amount: targetAmount.value, entries }, 'company')
}

// Upload click handler
const handleUploadClick = (index = 0) => {
  uploadTargetIndex.value = index
  fileInputRef.value?.click()
}

const showAlertModal = (title: string, body: string, color = 'warning') => {
  alertModal.value?.callModal(title, body, 'mdi-alert-circle', color)
}

const isLegacyXlsFile = (file: File) => file.name.toLowerCase().endsWith('.xls')

// File change handler
const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) return

  if (isLegacyXlsFile(file)) {
    showAlertModal(
      '파일 형식 안내',
      '.xls(구형 엑셀) 파일은 지원되지 않습니다.\nExcel에서 .xlsx 형식으로 다시 저장한 후 업로드해 주세요.',
    )
    target.value = ''
    return
  }

  try {
    // Prepare existing entries for matching - resolve IDs to names
    const existingEntries = targetEntries.value.map(entry => ({
      pk: entry.pk,
      account: entry.account ?? undefined,
      ...resolveEntryNames(entry),
      description: '', // Not used in AccountingEntry
      trader: entry.trader || '',
      amount: entry.amount || 0,
      evidence_type: entry.evidence_type || '',
      affiliate: entry.affiliate ?? undefined, // Convert null to undefined
    }))

    // Parse Excel file with matching
    await parseExcelFile(
      file,
      ledgerStore.comAccounts,
      existingEntries,
      targetAmount.value,
      'company',
      ledgerStore.affiliates,
    ).then(result => {
      parseResult.value = result
      uploadDialogVisible.value = true
    })
  } catch (error) {
    console.error('Excel parsing error:', error)
    showAlertModal('엑셀 파싱 오류', '엑셀 파일 파싱 중 오류가 발생했습니다.', 'danger')
  } finally {
    // Reset file input
    target.value = ''
  }
}

// Confirm upload handler
const handleUploadConfirm = () => {
  if (!parseResult.value) return

  const toEntry = (p: ParseResult['entriesToCreate'][number]): NewEntryForm => ({
    pk: undefined,
    account: p.account ?? null,
    trader: p.trader,
    amount: p.amount,
    evidence_type: p.evidence_type as NewEntryForm['evidence_type'],
    affiliate: p.affiliate ?? null,
  })

  if (isCreateMode.value) {
    // 신규 모드: 저장된 항목(pk)이 없으므로 업로드된 유효 항목으로 전체 교체
    const list = targetEntries.value
    const uploaded = [...parseResult.value.entriesToUpdate, ...parseResult.value.entriesToCreate]
      .filter(p => p.isValid)
      .sort((a, b) => a.rowNumber - b.rowNumber)
      .map(toEntry)
    if (uploaded.length) list.splice(0, list.length, ...uploaded)
  } else {
    // Step 1: Update existing entries (preserve pk)
    parseResult.value.entriesToUpdate.forEach(parsedEntry => {
      if (!parsedEntry.isValid) return // Skip invalid

      const existingEntry = editableEntries.value.find(e => e.pk === parsedEntry.existingPk)

      if (existingEntry) {
        // Update fields (keep pk)
        existingEntry.account = parsedEntry.account ?? null
        existingEntry.trader = parsedEntry.trader
        existingEntry.amount = parsedEntry.amount
        existingEntry.evidence_type = parsedEntry.evidence_type as NewEntryForm['evidence_type']
        existingEntry.affiliate = parsedEntry.affiliate ?? null
      }
    })

    // Step 2: Create new entries (no pk)
    parseResult.value.entriesToCreate.forEach(parsedEntry => {
      if (!parsedEntry.isValid) return // Skip invalid
      editableEntries.value.push(toEntry(parsedEntry))
    })

    // Step 3: Delete entries (remove from array)
    parseResult.value.entriesToDelete.forEach(entryToDelete => {
      const index = editableEntries.value.findIndex(e => e.pk === entryToDelete.pk)
      if (index !== -1) {
        editableEntries.value.splice(index, 1)
      }
    })
  }

  uploadDialogVisible.value = false
  parseResult.value = null
}

// === 엑셀: 다수 은행거래 + 회계 계정 대량 입력 (신규 모드 전용) ===
const bulkFileInputRef = ref<HTMLInputElement | null>(null)
const bulkDialogVisible = ref(false)
const bulkResult = ref<BulkParseResult | null>(null)
const { downloadBulkTemplate, parseBulkFile, parseBulkText } = useBulkTransExcel()

const getExistingForDeduplication = () => {
  const dbExisting = ledgerStore.bankTransactionList.map(t => ({
    deal_date: t.deal_date,
    amount: t.amount,
    sort: t.sort,
    content: t.content,
  }))
  const formExisting = bankTransactions.value
    .filter(t => t.bankForm.amount && t.bankForm.deal_date)
    .map(t => ({
      deal_date: t.bankForm.deal_date,
      amount: t.bankForm.amount || 0,
      sort: t.bankForm.sort,
      content: t.bankForm.content || '',
    }))
  return [...dbExisting, ...formExisting]
}

const handleBulkDownload = () =>
  downloadBulkTemplate({
    bankAccounts: formBankAccounts.value,
    accounts: ledgerStore.comAccounts,
    systemType: 'company',
  })

const handleBulkUploadClick = () => bulkFileInputRef.value?.click()

const handleBulkFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  if (isLegacyXlsFile(file)) {
    showAlertModal(
      '파일 형식 안내',
      '.xls(구형 엑셀) 파일은 지원되지 않습니다.\nExcel에서 .xlsx 또는 .csv 형식으로 저장한 후 업로드해 주세요.',
    )
    target.value = ''
    return
  }

  try {
    bulkResult.value = await parseBulkFile(file, {
      bankAccounts: formBankAccounts.value,
      accounts: ledgerStore.comAccounts,
      contracts: ledgerStore.affiliates,
      systemType: 'company',
      existingTransactions: getExistingForDeduplication(),
    })
    bulkDialogVisible.value = true
  } catch (error) {
    console.error('Bulk excel parsing error:', error)
    showAlertModal(
      '엑셀 파싱 오류',
      error instanceof Error ? error.message : '엑셀 파일 파싱 중 오류가 발생했습니다.',
      'danger',
    )
  } finally {
    target.value = ''
  }
}

const handleBulkPaste = async () => {
  try {
    const text = await navigator.clipboard.readText()
    if (!text || !text.trim()) {
      alertModal.value?.callModal(
        '클립보드 안내',
        '클립보드에 복사된 텍스트 데이터가 없습니다.\n인터넷 뱅킹 거래 내역을 복사한 후 다시 시도해 주세요.',
        'mdi-information-outline',
        'info',
      )
      return
    }
    bulkResult.value = await parseBulkText(text, {
      bankAccounts: formBankAccounts.value,
      accounts: ledgerStore.comAccounts,
      contracts: ledgerStore.affiliates,
      systemType: 'company',
      existingTransactions: getExistingForDeduplication(),
    })
    bulkDialogVisible.value = true
  } catch (error) {
    console.error('Clipboard paste error:', error)
    alertModal.value?.callModal(
      '클립보드 오류',
      error instanceof Error
        ? error.message
        : '클립보드 데이터를 읽는 중 오류가 발생했습니다. 브라우저의 클립보드 접근 권한을 확인해 주세요.',
      'mdi-alert-circle',
      'danger',
    )
  }
}

// 현재 폼에 사용자가 입력한 내용이 있는지 (빈 기본 거래건 1개는 '없음'으로 간주)
const hasEnteredTransactions = computed(() =>
  bankTransactions.value.some(
    t =>
      t.bankForm.amount ||
      t.bankForm.content ||
      t.entries.some(e => e.amount || e.account || e.trader),
  ),
)

const handleBulkConfirm = ({ replace }: { replace: boolean }) => {
  if (!bulkResult.value) return

  const imported: BankTransactionData[] = bulkResult.value.transactions
    .filter(t => t.isValid)
    .map(t =>
      createNewTransaction({
        bankForm: {
          deal_date: t.bankForm.deal_date,
          bank_account: t.bankForm.bank_account,
          amount: t.bankForm.amount,
          sort: t.bankForm.sort,
          content: t.bankForm.content,
          note: t.bankForm.note,
        },
        entries: t.entries.map(e => ({
          account: e.account,
          trader: e.trader,
          amount: e.amount,
          evidence_type: e.evidence_type,
          affiliate: e.contract,
        })),
      }),
    )

  if (imported.length) {
    bankTransactions.value = replace ? imported : [...bankTransactions.value, ...imported]
  }
  bulkDialogVisible.value = false
  bulkResult.value = null
}

const addRow = () => {
  editableEntries.value.push({})
}

const removeEntry = (index: number) => {
  if (editableEntries.value.length === 1) {
    editableEntries.value[index].amount = 0
  } else {
    editableEntries.value.splice(index, 1)
  }
}

const insertTransferFeeEntry = (index: number) => {
  if (transferFeePk.value === undefined) {
    showAlertModal('계정 안내', '이체수수료 계정이 설정되지 않았습니다.')
    return
  }

  const currentRow = editableEntries.value[index]
  const baseAmount =
    currentRow.amount !== undefined && currentRow.amount !== null && currentRow.amount > 0
      ? Number(currentRow.amount)
      : Number(bankForm.amount) || 0

  currentRow.amount = Math.max(0, baseAmount - 500)

  const currentTrader = currentRow.trader?.trim() || ''

  const newEntry: NewEntryForm = {
    pk: undefined,
    account: transferFeePk.value,
    trader: `[${currentTrader}]-이체수수료`,
    amount: 500,
    affiliate: null,
    evidence_type: '0',
  }

  editableEntries.value.splice(index + 1, 0, newEntry)
}

// ========== 다중 거래건 관련 메서드 ==========
const addBankTransaction = () => {
  bankTransactions.value.push(createNewTransaction())
}

const removeBankTransaction = (index: number) => {
  if (bankTransactions.value.length > 1) {
    bankTransactions.value.splice(index, 1)
  }
}

const updateBankTransaction = (index: number, newData: BankTransactionData) => {
  bankTransactions.value[index] = newData
}

// 대체(출금) 거래 자동 추가
const handleTransferWithdraw = (sourceData: BankTransactionData) => {
  const sourceAccount = ledgerStore.comAccounts.find(
    acc => acc.value === sourceData.entries[0].account,
  )

  if (!sourceAccount || sourceAccount.category !== 'transfer') return

  const depositTransferAccount = ledgerStore.comAccounts.find(
    acc => acc.is_cate_only === false && acc.category === 'transfer' && acc.direction === '입금',
  )

  if (!depositTransferAccount) {
    showAlertModal('계정 안내', '대체(입금) 계정을 찾을 수 없습니다.')
    return
  }

  bankTransactions.value.push(
    createNewTransaction({
      bankForm: {
        deal_date: sourceData.bankForm.deal_date,
        note: sourceData.bankForm.note,
        bank_account: null,
        content: sourceData.bankForm.content,
        sort: 1,
        amount: sourceData.bankForm.amount,
      },
      entries: [
        {
          account: depositTransferAccount.value,
          trader: sourceData.entries[0].trader || '',
          amount: sourceData.bankForm.amount || undefined,
          affiliate: null,
          evidence_type: '',
        },
      ],
    }),
  )
}

const isEntryRowValid = (entries: NewEntryForm[]): boolean => {
  if (!entries.length) return false
  const hasPositiveEntry = entries.some(e => (e.amount || 0) > 0)
  if (!hasPositiveEntry) return false
  return entries.every(e => {
    const amount = e.amount ?? 0
    if (amount < 0) return false
    if (amount > 0) {
      if (!e.account) return false
      const acc = accountMap.value.get(e.account)
      if (acc?.req_affiliate && !e.affiliate) return false
      return true
    }
    return !e.account
  })
}

const mapEntriesToPayload = (entries: NewEntryForm[]): CompositeAccountingEntryPayload[] =>
  entries
    .filter(e => (e.amount || 0) > 0 && !!e.account)
    .map(entry => ({
      ...(entry.pk ? { pk: entry.pk } : {}),
      account: entry.account as number,
      affiliate: entry.affiliate ?? null,
      amount: Number(entry.amount) || 0,
      trader: entry.trader ?? '',
      evidence_type: entry.evidence_type === '' || !entry.evidence_type ? null : entry.evidence_type,
    }))

const validateTransactionSet = (
  txForm: BankTransactionForm,
  entries: NewEntryForm[],
  labelPrefix = '',
) => {
  if (!props.company) {
    throw new ClientValidationError('회사 정보가 선택되지 않았습니다.')
  }

  if (
    !txForm.deal_date ||
    !txForm.bank_account ||
    !txForm.amount ||
    txForm.amount <= 0 ||
    !txForm.content?.trim()
  ) {
    throw new ClientValidationError(
      `${labelPrefix}거래일자, 거래계좌, 금액(0 초과), 적요는 필수 입력 항목입니다.`,
    )
  }

  if (entries.some(e => (e.amount ?? 0) < 0)) {
    throw new ClientValidationError(`${labelPrefix}분류 금액은 0 이상이어야 합니다.`)
  }

  const positiveEntries = entries.filter(e => (e.amount || 0) > 0)
  if (positiveEntries.length === 0) {
    throw new ClientValidationError(`${labelPrefix}최소 하나 이상의 분류 항목이 필요합니다.`)
  }

  if (positiveEntries.some(e => !e.account)) {
    throw new ClientValidationError(
      `${labelPrefix}분류 금액이 입력된 모든 항목에 회계 계정을 선택해야 합니다.`,
    )
  }

  if (
    positiveEntries.some(e => {
      const acc = e.account ? accountMap.value.get(e.account) : undefined
      return Boolean(acc?.req_affiliate && !e.affiliate)
    })
  ) {
    throw new ClientValidationError(
      `${labelPrefix}관계회사/프로젝트가 필수인 계정에 관계회사를 선택해 주세요.`,
    )
  }

  const entryTotal = entries.reduce((sum, e) => sum + (Number(e.amount) || 0), 0)
  if (Number(txForm.amount) !== entryTotal) {
    throw new ClientValidationError(`${labelPrefix}거래 금액과 분류 금액이 일치하지 않습니다.`)
  }
}

// 유효성 검사 (단일/수정 모드)
const validateForm = () => {
  validateTransactionSet(bankForm, editableEntries.value)
}

// 신규 거래 데이터 생성
const buildCreatePayload = (): CompositeTransactionPayload => {
  validateForm()

  return {
    company: props.company,
    deal_date: bankForm.deal_date,
    bank_account: Number(bankForm.bank_account),
    amount: Number(bankForm.amount),
    sort: bankForm.sort,
    content: bankForm.content,
    note: bankForm.note,
    accounting_entries: mapEntriesToPayload(editableEntries.value),
  }
}

// 수정 거래 데이터 생성
const buildUpdatePayload = (): CompositeTransactionPatchPayload => {
  if (!transaction.value?.pk) {
    throw new ClientValidationError('수정할 거래 데이터가 없습니다.')
  }

  validateForm()

  return {
    pk: transaction.value.pk,
    company: props.company,
    deal_date: bankForm.deal_date,
    bank_account: Number(bankForm.bank_account),
    amount: Number(bankForm.amount),
    sort: bankForm.sort,
    content: bankForm.content,
    note: bankForm.note,
    accounting_entries: mapEntriesToPayload(editableEntries.value),
  }
}

// 다중 거래건 저장 처리
const saveMultipleTransactions = async () => {
  if (!props.company) {
    throw new ClientValidationError('회사 정보가 선택되지 않았습니다.')
  }

  for (let i = 0; i < bankTransactions.value.length; i++) {
    const trans = bankTransactions.value[i]
    validateTransactionSet(trans.bankForm, trans.entries, `${i + 1}번째 거래: `)
  }

  let savedCount = 0
  try {
    for (const trans of bankTransactions.value) {
      const payload: CompositeTransactionPayload = {
        company: props.company,
        deal_date: trans.bankForm.deal_date,
        bank_account: Number(trans.bankForm.bank_account),
        amount: Number(trans.bankForm.amount),
        sort: trans.bankForm.sort,
        content: trans.bankForm.content,
        note: trans.bankForm.note,
        accounting_entries: mapEntriesToPayload(trans.entries),
      }
      await ledgerStore.createBankTransaction(payload, { skipRefresh: true, silent: true })
      savedCount++
    }
    await ledgerStore.fetchBankTransactionList(ledgerStore.bankTransactionFilter)
    message()
  } catch (err) {
    if (savedCount > 0) {
      bankTransactions.value.splice(0, savedCount)
      await ledgerStore.fetchBankTransactionList(ledgerStore.bankTransactionFilter)
    }
    throw err
  }
}

// 저장 처리
const saveTransaction = async (event: Event) => {
  const isFormInvalid = isValidate(event) || !isFormValid.value
  if (isFormInvalid) {
    validated.value = true
    event.preventDefault()
    event.stopPropagation()
  } else {
    if (isSaving.value) return

    try {
      isSaving.value = true

      if (isCreateMode.value) {
        if (bankTransactions.value.length > 0) {
          await saveMultipleTransactions()
        } else {
          const payload = buildCreatePayload()
          await ledgerStore.createBankTransaction(payload)
        }
      } else {
        const payload = buildUpdatePayload()
        await ledgerStore.updateBankTransaction(payload)
      }

      skipLeaveGuard.value = true
      await router.push({ name: '본사 거래 내역' })
    } catch (error: unknown) {
      skipLeaveGuard.value = false
      console.error('저장 실패:', error)
      if (error instanceof ClientValidationError) {
        showAlertModal('저장 오류', error.message, 'danger')
      }
    } finally {
      isSaving.value = false
    }
  }
}

const delTransaction = async () => {
  const pk = transaction.value?.pk
  confirmModal.value?.close()
  if (!pk) return

  try {
    await ledgerStore.deleteBankTransaction(pk)
    skipLeaveGuard.value = true
    await router.replace({ name: '본사 거래 내역' })
  } catch {
    skipLeaveGuard.value = false
  }
}

const accCallModal = () => {
  if (props.company) refBankAcc.value?.callModal()
}

const loadEditTransaction = async (id: number) => {
  await ledgerStore.fetchBankTransaction(id)
  initializeEditForm()
}

onBeforeMount(async () => {
  if (isCreateMode.value) {
    initializeCreateForm()
  } else if (transId.value) {
    await loadEditTransaction(transId.value)
  }
})

watch(transId, async (newId, oldId) => {
  if (newId === oldId) return
  if (!newId) {
    initializeCreateForm()
  } else {
    await loadEditTransaction(newId)
  }
})

// 거래건별 금액 일치 확인 헬퍼 함수
const isTransactionBalanced = (
  bankAmountVal: number | null,
  entries: { amount?: number | null }[],
): boolean => {
  if (!bankAmountVal || bankAmountVal <= 0) return false
  const totalEntries = entries.reduce((sum, e) => sum + (Number(e.amount) || 0), 0)
  return bankAmountVal === totalEntries
}

// 폼 유효성 검사 상태
const isFormValid = computed(() => {
  if (!props.company) return false

  if (isCreateMode.value) {
    if (bankTransactions.value.length === 0) return false

    return bankTransactions.value.every(trans => {
      const hasRequiredFields = Boolean(
        trans.bankForm.deal_date &&
          trans.bankForm.bank_account &&
          trans.bankForm.amount &&
          trans.bankForm.amount > 0 &&
          trans.bankForm.content?.trim(),
      )
      return (
        hasRequiredFields &&
        isEntryRowValid(trans.entries) &&
        isTransactionBalanced(trans.bankForm.amount, trans.entries)
      )
    })
  } else {
    const hasRequiredFields = Boolean(
      bankForm.deal_date &&
        bankForm.bank_account &&
        bankForm.amount &&
        bankForm.amount > 0 &&
        bankForm.content?.trim(),
    )
    return hasRequiredFields && isEntryRowValid(editableEntries.value) && isBalanced.value
  }
})

// 저장 버튼 비활성화 상태
const isSaveDisabled = computed(() => isSaving.value)

// 네비게이션 가드
const hasUnsavedChanges = computed(() => {
  if (isCreateMode.value) {
    return (
      hasEnteredTransactions.value ||
      bankForm.amount !== null ||
      bankForm.content !== '' ||
      editableEntries.value.some(e => e.amount)
    )
  }
  return Boolean(initialEditSnapshot.value && serializeEditState() !== initialEditSnapshot.value)
})

const resolveLeaveConfirm = (allowed: boolean) => {
  if (!pendingLeaveResolve) return
  const resolve = pendingLeaveResolve
  pendingLeaveResolve = null
  resolve(allowed)
}

const confirmLeaveAction = () => {
  resolveLeaveConfirm(true)
  leaveConfirmModal.value?.close()
}

onBeforeRouteLeave(async () => {
  if (skipLeaveGuard.value || !hasUnsavedChanges.value) {
    return true
  }
  return await new Promise<boolean>(resolve => {
    pendingLeaveResolve = resolve
    leaveConfirmModal.value?.callModal()
  })
})
</script>

<template>
  <CForm
    class="needs-validation"
    novalidate
    :validated="validated"
    @submit.prevent="saveTransaction"
  >
    <CRow
      class="text-end py-2 mb-1 mx-1"
      :class="isCreateMode ? 'bg-light-blue-lighten-5' : 'bg-light-green-lighten-5'"
    >
      <CCol class="text-start">
        <template v-if="isCreateMode">
          <span class="text-primary strong">신규 거래 등록 중...</span>
        </template>
        <template v-else>
          {{ transaction?.deal_date }} ∙ {{ transaction?.bank_account_name }} ∙
          {{ transaction?.content }}
          <span class="ms-2 text-success strong">분할 중...</span>
        </template>
      </CCol>
      <CCol lg="auto">
        <span> 거래내역 금액: {{ sortName }} {{ numFormat(bankAmount, 0, '0') }} </span>
        ∙
        <span>분류 금액 합계: {{ sortName }} {{ numFormat(totalEntryAmount, 0, '0') }}</span> ∙
        <span class="strong me-3" :class="{ 'text-danger': !isBalanced }">
          차액: {{ sortName }} {{ numFormat(Math.abs(difference), 0, '0') }}
        </span>

        <v-btn
          type="submit"
          :color="isCreateMode ? 'primary' : 'success'"
          size="small"
          :disabled="isSaveDisabled"
          :loading="isSaving"
        >
          {{
            isSaving ? (isCreateMode ? '생성 중...' : '저장 중...') : isCreateMode ? '생성' : '저장'
          }}
        </v-btn>
        <v-btn
          size="small"
          variant="flat"
          :disabled="isSaving"
          @click="router.push({ name: '본사 거래 내역' })"
        >
          취소
        </v-btn>
      </CCol>
    </CRow>

    <hr class="mb-0" />
    <CTable class="mb-5">
      <colgroup>
        <col style="width: 8%" />
        <col style="width: 12%" />
        <col style="width: 8%" />
        <col style="width: 12%" />
        <col style="width: 10%" />

        <col style="width: 16%" />
        <col style="width: 12%" />
        <col style="width: 8%" />
        <col style="width: 11%" />
        <col v-if="canComLedgerEdit" style="width: 3%" />
      </colgroup>

      <CTableHead class="sticky-table-head">
        <CTableRow :color="TableSecondary" class="sticky-header-row-1">
          <CTableHeaderCell class="ps-3" colspan="5">
            은행거래내역
            <!-- 신규 모드: 다수 은행거래 + 회계 계정 엑셀 대량 입력 -->
            <template v-if="isCreateMode">
              <span class="text-grey mx-2">|</span>
              <span class="text-caption me-1">대량 입력</span>
              <v-icon
                icon="mdi-download"
                size="16"
                color="info"
                class="me-2 pointer"
                @click="handleBulkDownload"
                v-tooltip="'IBS 표준 대량 입력 템플릿 다운로드'"
              />
              <v-icon
                icon="mdi-upload"
                size="16"
                color="success"
                class="pointer"
                @click="handleBulkUploadClick"
                v-tooltip="'IBS 템플릿 엑셀 업로드 (1회 최대 60건 / 250행)'"
              />
              <v-icon
                icon="mdi-bank-transfer"
                size="16"
                color="teal"
                class="ms-2 pointer"
                @click="handleBulkUploadClick"
                v-tooltip="'은행 원본 엑셀/CSV 업로드 (국민/신한/우리/하나/기업/농협 등 다운로드 파일 바로 등록)'"
              />
              <v-icon
                icon="mdi-content-paste"
                size="16"
                color="primary"
                class="ms-2 pointer"
                @click="handleBulkPaste"
                v-tooltip="'인터넷 뱅킹 거래내역 복사 데이터(클립보드) 바로 붙여넣기'"
              />
              <input
                ref="bulkFileInputRef"
                type="file"
                accept=".xlsx,.csv"
                style="display: none"
                @change="handleBulkFileChange"
              />
            </template>
          </CTableHeaderCell>
          <CTableHeaderCell class="ps-0" :colspan="canComLedgerEdit ? 4 : 3">
            <span class="text-grey me-2">|</span> 분류 내역
            <span v-if="isCreateMode" class="text-caption text-grey ms-1">
              (거래건별 엑셀 입력은 각 행의 아이콘 사용)
            </span>
          </CTableHeaderCell>
          <CTableHeaderCell class="px-0">
            <!-- 수정 모드: 단일 거래건의 회계 계정 템플릿 -->
            <template v-if="!isCreateMode">
              <!-- Download Template -->
              <v-icon
                icon="mdi-download"
                size="16"
                color="info"
                class="me-2 pointer"
                @click="handleDownloadTemplate()"
                v-tooltip="'회계 계정 정보 템플릿 다운로드'"
              />

              <!-- Upload Excel -->
              <v-icon
                icon="mdi-upload"
                size="16"
                color="success"
                class="pointer"
                @click="handleUploadClick()"
                v-tooltip="'회계 계정 정보 엑셀 업로드'"
              />
            </template>

            <!-- Hidden file input (분류 내역 업로드: 신규/수정 공통) -->
            <input
              ref="fileInputRef"
              type="file"
              accept=".xlsx"
              style="display: none"
              @change="handleFileChange"
            />
          </CTableHeaderCell>
        </CTableRow>

        <CTableRow :color="TableSecondary" class="sticky-header-row-2">
          <CTableHeaderCell scope="col">거래일자</CTableHeaderCell>
          <CTableHeaderCell scope="col">메모</CTableHeaderCell>
          <CTableHeaderCell scope="col">
            거래계좌
            <a href="#" @click.prevent="accCallModal">
              <CIcon name="cilCog" />
            </a>
          </CTableHeaderCell>
          <CTableHeaderCell scope="col">적요</CTableHeaderCell>
          <CTableHeaderCell scope="col">입출금액</CTableHeaderCell>
          <CTableHeaderCell scope="col">
            계정
            <a href="#" @click.prevent="refAccountManage?.callModal()">
              <CIcon name="cilCog" />
            </a>
          </CTableHeaderCell>
          <CTableHeaderCell scope="col">거래처</CTableHeaderCell>
          <CTableHeaderCell scope="col">분류 금액</CTableHeaderCell>
          <CTableHeaderCell scope="col">지출증빙</CTableHeaderCell>
          <CTableHeaderCell v-if="canComLedgerEdit" scope="col"></CTableHeaderCell>
        </CTableRow>
      </CTableHead>

      <CTableBody>
        <!-- 신규 모드: 다수 거래건 입력 (BankTransactionRow 사용) -->
        <template v-if="isCreateMode">
          <BankTransactionRow
            v-for="(trans, idx) in bankTransactions"
            :key="trans.uid ?? `trans-${idx}`"
            :transaction="trans"
            :index="idx"
            :bank-accounts="formBankAccounts"
            :com-accounts="ledgerStore.comAccounts"
            :affiliates="ledgerStore.affiliates"
            @update:transaction="updateBankTransaction(idx, $event)"
            @remove="removeBankTransaction(idx)"
            @detect-transfer-withdraw="handleTransferWithdraw"
            @download-template="handleDownloadTemplate(idx)"
            @upload-entries="handleUploadClick(idx)"
            @alert="(title, msg) => showAlertModal(title, msg)"
          />

          <!-- 거래건 추가 버튼 행 -->
          <CTableRow :class="bgLight">
            <CTableDataCell colspan="10" class="text-center py-2">
              <v-btn size="small" color="primary" variant="outlined" @click="addBankTransaction">
                <v-icon icon="mdi-plus" class="me-1" />
                은행거래건 추가
              </v-btn>
              <small class="text-muted ms-3">
                (현재 {{ bankTransactions.length }}건의 거래를 입력 중입니다)
              </small>
            </CTableDataCell>
          </CTableRow>
        </template>

        <!-- 수정 모드: 기존 단일 거래건 입력 -->
        <template v-else>
          <CTableRow class="sticky-bank-row">
            <!-- 거래일자 -->
            <CTableDataCell>
              <DatePicker v-model="bankForm.deal_date" required />
            </CTableDataCell>

            <!-- 메모 -->
            <CTableDataCell>
              <CFormInput v-model="bankForm.note" placeholder="메모" maxlength="50" />
            </CTableDataCell>

            <!-- 거래계좌 -->
            <CTableDataCell>
              <CFormSelect
                :model-value="bankForm.bank_account ? String(bankForm.bank_account) : ''"
                required
                @update:model-value="val => (bankForm.bank_account = val ? Number(val) : '')"
              >
                <option value="">---------</option>
                <option v-for="ba in formBankAccounts" :key="ba.value" :value="ba.value">
                  {{ ba.label }}
                </option>
              </CFormSelect>
            </CTableDataCell>

            <!-- 적요 -->
            <CTableDataCell>
              <CFormInput v-model="bankForm.content" placeholder="적요" maxlength="100" required />
            </CTableDataCell>

            <!-- 입출금액 -->
            <CTableDataCell class="text-end">
              <div class="d-flex align-items-center justify-content-end">
                <CFormSelect
                  :model-value="String(bankForm.sort)"
                  style="width: 70px"
                  required
                  class="me-2"
                  @update:model-value="val => (bankForm.sort = Number(val) as 1 | 2)"
                >
                  <option :value="1">입금</option>
                  <option :value="2">출금</option>
                </CFormSelect>
                <CFormInput
                  v-model.number="bankForm.amount"
                  type="number"
                  min="0"
                  placeholder="금액"
                  required
                  style="width: 120px"
                  class="text-end"
                />
                <v-btn density="compact" rounded="1" size="22" class="ms-2 pointer" @click="addRow">
                  <v-icon icon="mdi-plus" color="success" />
                </v-btn>
              </div>
            </CTableDataCell>

            <CTableDataCell :colspan="canComLedgerEdit ? 5 : 4" class="p-0">
              <JournalRow
                :sort="bankForm.sort"
                :display-rows="displayRows"
                :trans-amount="bankForm.amount"
                @update:entries="val => (editableEntries = val)"
                @remove-entry="removeEntry"
                @insert-transfer-fee="insertTransferFeeEntry"
                @alert="(title, msg) => showAlertModal(title, msg)"
              />
            </CTableDataCell>
          </CTableRow>
        </template>
      </CTableBody>
    </CTable>

    <CRow v-if="!isCreateMode" class="text-end px-2">
      <CCol>
        <v-btn
          color="warning"
          size="small"
          :disabled="!canComLedgerRemove"
          @click="confirmModal?.callModal()"
        >
          삭제
        </v-btn>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="confirmModal">
    <template #header>본사 거래 내역 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 입출금 거래 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="delTransaction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="leaveConfirmModal" @close="resolveLeaveConfirm(false)">
    <template #header>페이지 이동 확인</template>
    <template #default>
      저장하지 않은 변경사항이 있습니다. 페이지를 떠나시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="confirmLeaveAction">나가기</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="alertModal" />

  <AccountManage ref="refAccountManage" />

  <BankAcc ref="refBankAcc" />

  <ExcelUploadDialog
    v-model="uploadDialogVisible"
    :parse-result="parseResult"
    :transaction-amount="targetAmount"
    system-type="company"
    @confirm="handleUploadConfirm"
  />

  <BulkTransUploadDialog
    v-model="bulkDialogVisible"
    v-model:result="bulkResult"
    :has-existing="hasEnteredTransactions"
    :bank-accounts="formBankAccounts"
    :accounts="ledgerStore.comAccounts"
    related-label="관계회사(프로젝트)"
    @confirm="handleBulkConfirm"
  />
</template>
