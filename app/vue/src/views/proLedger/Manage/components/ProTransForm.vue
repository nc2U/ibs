<script lang="ts" setup>
import { computed, onBeforeMount, reactive, ref, watch, provide } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { isValidate } from '@/utils/helper.ts'
import { getToday, numFormat } from '@/utils/baseMixins.ts'
import { useExcelUpload, type ParseResult } from '@/composables/useExcelUpload'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import { useContract } from '@/store/pinia/contract.ts'
import { usePayment } from '@/store/pinia/payment.ts'
import { bgLight, TableSecondary } from '@/utils/cssMixins.ts'
import type {
  CompositeProAccountingEntryPayload,
  CompositeProBankTransPayload,
  ProBankTrans,
  ProjectBank,
} from '@/store/types/proLedger.ts'
import { type BulkParseResult, useBulkTransExcel } from '@/composables/useBulkTransExcel'
import BankTransactionRow, { type BankTransactionData } from './BankTransactionRow.vue'
import BulkTransUploadDialog from './BulkTransUploadDialog.vue'
import ExcelUploadDialog from '@/components/LedgerAccount/ExcelUploadDialog.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import NoAuth from '@/views/_Accounts/NoAuth.vue'
import AccountManage from './AccountManage.vue'
import ProAccountEntry, { type NewEntryForm } from './ProAccountEntry.vue'
import BankAcc from './BankAcc.vue'

interface Props {
  project?: number | null
  isImprest?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  project: null,
  isImprest: false,
})

const accStore = useAccount()
const { can, canGlobal, PERM } = usePerms()
const proLedgerStore = useProLedger()
const contractStore = useContract()
const paymentStore = usePayment()

const canLedgerCreate = computed(() =>
  props.project ? can(PERM.LEDGER_CREATE, props.project) : can(PERM.LEDGER_CREATE),
)
const canLedgerUpdate = computed(() =>
  props.project ? can(PERM.LEDGER_UPDATE, props.project) : can(PERM.LEDGER_UPDATE),
)
const canLedgerDelete = computed(() =>
  props.project ? can(PERM.LEDGER_DELETE, props.project) : can(PERM.LEDGER_DELETE),
)
const canLedgerManage = computed(
  () =>
    canLedgerCreate.value ||
    canLedgerUpdate.value ||
    (props.project ? can(PERM.LEDGER_MANAGE, props.project) : can(PERM.LEDGER_MANAGE)) ||
    canGlobal(PERM.LEDGER_MANAGE),
)

const confirmModal = ref()
const leaveConfirmModal = ref()
const alertModal = ref()
const refAccountManage = ref()
const refBankAcc = ref()

const [route, router] = [useRoute(), useRouter()]

const transId = computed(() => Number(route.params.transId) || null)
const isCreateMode = computed(() => !transId.value)
const listRouteName = computed(() => (props.isImprest ? '운영비 내역 관리' : '거래 내역 관리'))
const canAccessForm = computed(() =>
  isCreateMode.value ? canLedgerCreate.value : canLedgerUpdate.value,
)
const isSaving = ref(false)
const skipLeaveGuard = ref(false)

const payOrderOptions = computed(() =>
  paymentStore.payOrderList.map(po => ({
    value: po.pk as number,
    label: po.alias_name || po.pay_name || po.str_display || `회차 ${po.pk}`,
  })),
)
const transferFeePk = computed(() => proLedgerStore.transferFeePk)
const transaction = computed(() => proLedgerStore.proBankTrans as ProBankTrans | null)

provide(
  'getContracts',
  computed(() => contractStore.getContracts),
)
provide(
  'getAllContractors',
  computed(() => contractStore.getAllContractors),
)
provide(
  'proAccounts',
  computed(() => proLedgerStore.proAccounts),
)
provide('transferFeePk', transferFeePk)

const fetchFormData = async (projId: number) => {
  const tasks: Promise<unknown>[] = [
    proLedgerStore.fetchProBankAccList(projId),
    proLedgerStore.fetchAllProBankAccList(projId),
    contractStore.fetchAllContracts(projId),
    contractStore.fetchAllContractors(projId),
  ]
  if (!proLedgerStore.proAccountList.length) {
    tasks.push(proLedgerStore.fetchProjectAccounts())
  }
  if (!props.isImprest) {
    tasks.push(paymentStore.fetchPayOrderList(projId))
  }
  await Promise.all(tasks)
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

// 은행 거래 폼 데이터 (수정 모드용)
interface ProBankTransForm {
  deal_date: string
  note: string
  bank_account: number | null | ''
  content: string
  sort: 1 | 2
  amount: number | null
}

const validated = ref(false)
provide('validated', validated)
const bankForm = reactive<ProBankTransForm>({
  deal_date: getToday(),
  sort: 2,
  amount: null,
  content: '',
  note: '',
  bank_account: '',
})

// 수정 가능한 폼 데이터 - 수정 모드용
const editableEntries = ref<NewEntryForm[]>([])

// 신규 생성 모드용: 다수 은행거래건 배열
const bankTransactions = ref<BankTransactionData[]>([])
let nextTransUid = 1
const createNewTransaction = (data?: Partial<BankTransactionData>): BankTransactionData => ({
  uid: nextTransUid++,
  bankForm: data?.bankForm || {
    deal_date: getToday(),
    bank_account: '',
    amount: null,
    sort: 2,
    content: '',
    note: '',
  },
  entries: data?.entries || [{}],
})

const initializeCreateForm = () => {
  bankTransactions.value = [createNewTransaction()]

  Object.assign(bankForm, {
    deal_date: getToday(),
    bank_account: '',
    amount: null,
    sort: 2,
    content: '',
    note: '',
  })
  editableEntries.value = [{}]
}

const initializeEditForm = () => {
  if (!transaction.value) return

  Object.assign(bankForm, {
    deal_date: transaction.value.deal_date,
    note: transaction.value.note,
    bank_account: transaction.value.bank_account,
    content: transaction.value.content,
    sort: transaction.value.sort,
    amount: transaction.value.amount,
  })

  if (transaction.value.accounting_entries) {
    editableEntries.value = transaction.value.accounting_entries.map(entry => ({
      pk: entry.pk,
      account: entry.account,
      trader: entry.trader,
      amount: entry.amount,
      contract: entry.contract,
      contractor: entry.contractor,
      evidence_type: entry.evidence_type,
      installment_order: entry.contract_payment?.installment_order ?? null,
    }))
  } else {
    editableEntries.value = [{}]
  }
}

watch(
  () => props.project,
  async (val, oldVal) => {
    if (!val || val === oldVal) return
    if (isCreateMode.value) {
      await fetchFormData(val)
      if (oldVal) initializeCreateForm()
    } else if (oldVal) {
      skipLeaveGuard.value = true
      await router.push({ name: listRouteName.value })
    }
  },
)

// 표시할 행 목록
const displayRows = computed(() => editableEntries.value)
const onEditableEntriesUpdate = (rows: NewEntryForm[]) => {
  editableEntries.value = rows
}

// 은행 거래 금액
const bankAmount = computed(() => bankForm.amount || 0)

// 거래 구분 이름
const sortName = computed(() => {
  return isCreateMode.value
    ? bankForm.sort === 1
      ? '입금'
      : '출금'
    : transaction.value?.sort_name || ''
})

// 분류 금액 합계 계산
const totalEntryAmount = computed(() => {
  return editableEntries.value.reduce((sum, row) => {
    const amount = Number(row.amount) || 0
    return sum + amount
  }, 0)
})

const difference = computed(() => bankAmount.value - totalEntryAmount.value)
const isBalanced = computed(() => difference.value === 0)

// 은행 계좌 목록 (Imprest 모드에서는 운영비 계좌 우선, 수정 모드 비활성/타 계좌 폴백 포함)
const formBankAccounts = computed(() => {
  const activeBanks = props.isImprest
    ? proLedgerStore.getImprestProBanks
    : proLedgerStore.getProBanks

  if (isCreateMode.value) {
    return activeBanks
  }

  const currentBankId = transaction.value?.bank_account
  if (!currentBankId) return activeBanks

  if (activeBanks.some(b => b.value === currentBankId)) {
    return activeBanks
  }

  const currentBank = proLedgerStore.allProBankList.find(b => b.pk === currentBankId)
  if (currentBank) {
    return [
      {
        value: currentBank.pk,
        label: `${currentBank.alias_name} (비활성/숨김)`,
      },
      ...activeBanks,
    ]
  }

  return activeBanks
})

// === 엑셀: 1건의 은행거래에 대한 다수 회계 계정 입력 ===
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadDialogVisible = ref(false)
const parseResult = ref<ParseResult | null>(null)
const { parseExcelFile, downloadTemplate } = useExcelUpload()

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

const resolveEntryNames = (entry: NewEntryForm) => {
  const account = proLedgerStore.proAccounts.find(acc => acc.value === entry.account)
  const contract = contractStore.getContracts.find(c => c.value === entry.contract)
  return { account_name: account?.label || '', contract_name: contract?.label || '' }
}

const handleDownloadTemplate = (index = 0) => {
  uploadTargetIndex.value = index
  const entries = targetEntries.value.map(entry => ({
    ...resolveEntryNames(entry),
    trader: entry.trader || '',
    amount: entry.amount || 0,
    evidence_type: entry.evidence_type || '',
  }))

  downloadTemplate({ amount: targetAmount.value, entries }, 'project')
}

const handleUploadClick = (index = 0) => {
  uploadTargetIndex.value = index
  fileInputRef.value?.click()
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    const existingEntries = targetEntries.value.map(entry => ({
      pk: entry.pk,
      account: entry.account ?? undefined,
      ...resolveEntryNames(entry),
      trader: entry.trader || '',
      amount: entry.amount || 0,
      evidence_type: entry.evidence_type || '',
      contract: entry.contract ?? undefined,
    }))

    const result = await parseExcelFile(
      file,
      proLedgerStore.proAccounts,
      existingEntries,
      targetAmount.value,
      'project',
      contractStore.getContracts,
    )
    parseResult.value = result
    uploadDialogVisible.value = true
  } catch (error) {
    console.error('Excel parsing error:', error)
    alertModal.value?.callModal(
      '엑셀 파싱 오류',
      '엑셀 파일 파싱 중 오류가 발생했습니다.',
      'mdi-alert-circle',
      'danger',
    )
  } finally {
    target.value = ''
  }
}

const handleUploadConfirm = () => {
  if (!parseResult.value) return

  const toEntry = (p: ParseResult['entriesToCreate'][number]): NewEntryForm => ({
    pk: undefined,
    account: p.account ?? null,
    trader: p.trader,
    amount: p.amount,
    evidence_type: p.evidence_type as NewEntryForm['evidence_type'],
    contract: p.contract ?? null,
  })

  if (isCreateMode.value) {
    const current = bankTransactions.value[uploadTargetIndex.value]
    if (current) {
      const uploaded = [
        ...parseResult.value.entriesToUpdate,
        ...parseResult.value.entriesToCreate,
      ]
        .filter(p => p.isValid)
        .sort((a, b) => a.rowNumber - b.rowNumber)
        .map(toEntry)
      if (uploaded.length) {
        updateBankTransaction(uploadTargetIndex.value, {
          ...current,
          entries: uploaded,
        })
      }
    }
  } else {
    const nextEntries = [...editableEntries.value]
    parseResult.value.entriesToUpdate.forEach(parsedEntry => {
      if (!parsedEntry.isValid) return
      const idx = nextEntries.findIndex(e => e.pk === parsedEntry.existingPk)
      if (idx !== -1) {
        nextEntries[idx] = {
          ...nextEntries[idx],
          account: parsedEntry.account ?? null,
          trader: parsedEntry.trader,
          amount: parsedEntry.amount,
          evidence_type: parsedEntry.evidence_type as NewEntryForm['evidence_type'],
          contract: parsedEntry.contract ?? null,
        }
      }
    })

    parseResult.value.entriesToCreate.forEach(parsedEntry => {
      if (!parsedEntry.isValid) return
      nextEntries.push(toEntry(parsedEntry))
    })

    parseResult.value.entriesToDelete.forEach(entryToDelete => {
      const idx = nextEntries.findIndex(e => e.pk === entryToDelete.pk)
      if (idx !== -1) nextEntries.splice(idx, 1)
    })
    editableEntries.value = nextEntries
  }

  uploadDialogVisible.value = false
  parseResult.value = null
}

// === 엑셀: 다수 은행거래 + 회계 계정 대량 입력 (신규 모드 전용) ===
const bulkFileInputRef = ref<HTMLInputElement | null>(null)
const bulkDialogVisible = ref(false)
const bulkResult = ref<BulkParseResult | null>(null)
const { downloadBulkTemplate, parseBulkFile, parseBulkText } = useBulkTransExcel()

const getExistingForDeduplication = async () => {
  let dbList = proLedgerStore.proBankTransList
  if (props.project && proLedgerStore.proBankTransCount > dbList.length) {
    dbList = await proLedgerStore.fetchExistingTransRefs(
      props.project,
      props.isImprest ? 'true' : 'all',
    )
  }
  const dbExisting = dbList.map(t => ({
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
    accounts: proLedgerStore.proAccounts,
    payOrders: props.isImprest ? [] : payOrderOptions.value,
    systemType: 'project',
  })

const handleBulkUploadClick = () => bulkFileInputRef.value?.click()

const handleBulkFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    const existingTransactions = await getExistingForDeduplication()
    bulkResult.value = await parseBulkFile(file, {
      bankAccounts: formBankAccounts.value,
      accounts: proLedgerStore.proAccounts,
      payOrders: props.isImprest ? [] : payOrderOptions.value,
      systemType: 'project',
      contracts: contractStore.getContracts,
      existingTransactions,
    })
    bulkDialogVisible.value = true
  } catch (error) {
    console.error('Bulk excel parsing error:', error)
    alertModal.value?.callModal(
      '엑셀 파싱 오류',
      error instanceof Error ? error.message : '엑셀 파일 파싱 중 오류가 발생했습니다.',
      'mdi-alert-circle',
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
    const existingTransactions = await getExistingForDeduplication()
    bulkResult.value = await parseBulkText(text, {
      bankAccounts: formBankAccounts.value,
      accounts: proLedgerStore.proAccounts,
      payOrders: props.isImprest ? [] : payOrderOptions.value,
      systemType: 'project',
      contracts: contractStore.getContracts,
      existingTransactions,
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

const hasEnteredTransactions = computed(() =>
  bankTransactions.value.some(
    t =>
      t.bankForm.amount ||
      t.bankForm.content ||
      t.entries.some(e => e.amount || e.account || e.trader),
  ),
)

const handleBulkConfirm = ({
  replace,
  result,
}: {
  replace: boolean
  result?: BulkParseResult | null
}) => {
  const source = result ?? bulkResult.value
  if (!source) return

  const imported: BankTransactionData[] = source.transactions
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
          contract: e.contract,
          contractor: null,
          installment_order: e.installment_order ?? null,
        })),
      }),
    )

  if (!imported.length) return
  bankTransactions.value = replace ? imported : [...bankTransactions.value, ...imported]
  bulkResult.value = null
}

const addRow = () => {
  editableEntries.value = [...editableEntries.value, {}]
}

const removeEntry = (index: number) => {
  const next = [...editableEntries.value]
  if (next.length === 1) {
    next[0] = { ...next[0], amount: 0 }
  } else {
    next.splice(index, 1)
  }
  editableEntries.value = next
}

const insertTransferFeeEntry = (index: number) => {
  if (transferFeePk.value === undefined) {
    alertModal.value?.callModal(
      '계정 안내',
      '이체수수료 계정이 설정되지 않았습니다.',
      'mdi-alert-circle',
      'warning',
    )
    return
  }

  const next = [...editableEntries.value]
  const currentRow = next[index]
  const bankTransactionAmount = Number(bankForm.amount) || 0
  const newCurrentAmount = Math.max(0, bankTransactionAmount - 500)
  next[index] = { ...currentRow, amount: newCurrentAmount }

  const currentTrader = currentRow.trader?.trim() || '[]'
  const newEntry: NewEntryForm = {
    pk: undefined,
    account: transferFeePk.value,
    trader: `[${currentTrader}]-이체수수료`,
    amount: 500,
    contract: null,
    contractor: null,
    evidence_type: '0',
  }

  next.splice(index + 1, 0, newEntry)
  editableEntries.value = next
}

// === 신규 모드용 다수 거래건 메서드 ===
const addBankTransaction = () => {
  bankTransactions.value.push(createNewTransaction())
}

const removeBankTransaction = (index: number) => {
  if (bankTransactions.value.length > 1) {
    bankTransactions.value.splice(index, 1)
  }
}

const updateBankTransaction = (index: number, data: BankTransactionData) => {
  bankTransactions.value[index] = data
}

const handleTransferWithdraw = (sourceData: BankTransactionData) => {
  const depositTransferAccount = proLedgerStore.proAccounts.find(
    acc => acc.is_cate_only === false && acc.category === 'transfer' && acc.direction === '입금',
  )

  if (!depositTransferAccount) {
    console.warn('대체(입금) 계정을 찾을 수 없습니다.')
    return
  }

  bankTransactions.value.push(
    createNewTransaction({
      bankForm: {
        deal_date: sourceData.bankForm.deal_date,
        bank_account: null,
        amount: sourceData.bankForm.amount,
        sort: 1,
        content: sourceData.bankForm.content,
        note: sourceData.bankForm.note,
      },
      entries: [
        {
          account: depositTransferAccount.value,
          trader: sourceData.entries[0]?.trader || '',
          amount: sourceData.bankForm.amount || undefined,
          evidence_type: '',
        },
      ],
    }),
  )
}

const mapEntriesToPayload = (entries: NewEntryForm[]): CompositeProAccountingEntryPayload[] =>
  entries
    .filter(e => (e.amount || 0) > 0)
    .map(entry => ({
      ...(entry.pk !== undefined ? { pk: entry.pk } : {}),
      account: entry.account ?? null,
      trader: entry.trader,
      amount: entry.amount,
      contract: entry.contract ?? null,
      contractor: entry.contractor ?? null,
      installment_order: entry.installment_order ?? null,
      evidence_type: entry.evidence_type === '' ? null : (entry.evidence_type ?? null),
    }))

// 유효성 검사 (수정 모드)
const validateForm = () => {
  if (!isBalanced.value) {
    throw new Error('거래 금액과 분류 금액이 일치하지 않습니다.')
  }

  if (!bankForm.deal_date || !bankForm.bank_account || !bankForm.amount || !bankForm.content) {
    throw new Error('거래일자, 거래계좌, 금액, 적요는 필수 입력 항목입니다.')
  }

  const validEntries = editableEntries.value.filter(e => (e.amount || 0) > 0)
  if (validEntries.length === 0) {
    throw new Error('최소 하나 이상의 분류 항목이 필요합니다.')
  }

  const anyMissingAccount = editableEntries.value.some(e => (e.amount || 0) > 0 && !e.account)
  if (anyMissingAccount) {
    throw new Error('분류 금액이 입력된 모든 항목에 회계 계정을 선택해야 합니다.')
  }
}

const buildUpdatePayload = (): CompositeProBankTransPayload => {
  if (!transaction.value?.pk) {
    throw new Error('수정할 거래 데이터가 없습니다.')
  }

  validateForm()

  return {
    pk: transaction.value.pk,
    project: props.project!,
    deal_date: bankForm.deal_date,
    bank_account: Number(bankForm.bank_account),
    amount: bankForm.amount!,
    sort: bankForm.sort,
    content: bankForm.content,
    note: bankForm.note,
    accounting_entries: mapEntriesToPayload(editableEntries.value),
  }
}

const validateCreateList = () => {
  if (!props.project) {
    throw new Error('프로젝트가 선택되지 않았습니다.')
  }
  for (let i = 0; i < bankTransactions.value.length; i++) {
    const trans = bankTransactions.value[i]
    if (
      !trans.bankForm.deal_date ||
      !trans.bankForm.bank_account ||
      !trans.bankForm.amount ||
      !trans.bankForm.content
    ) {
      throw new Error(`거래건 ${i + 1}: 거래일자, 거래계좌, 금액, 적요는 필수 입력 항목입니다.`)
    }

    const bankAmt = trans.bankForm.amount || 0
    const entryTotal = trans.entries.reduce((sum, e) => sum + (Number(e.amount) || 0), 0)
    if (bankAmt !== entryTotal) {
      throw new Error(
        `거래건 ${i + 1}: 거래 금액(${bankAmt})과 분류 금액(${entryTotal})이 일치하지 않습니다.`,
      )
    }

    const validEntries = trans.entries.filter(e => (e.amount || 0) > 0)
    if (validEntries.length === 0) {
      throw new Error(`거래건 ${i + 1}: 최소 하나 이상의 분류 항목이 필요합니다.`)
    }
    if (validEntries.some(e => !e.account)) {
      throw new Error(`거래건 ${i + 1}: 분류 금액이 입력된 모든 항목에 회계 계정을 선택해야 합니다.`)
    }
  }
}

const saveMultipleTransactions = async (): Promise<boolean> => {
  validateCreateList()

  let savedCount = 0
  for (const trans of bankTransactions.value) {
    const payload: CompositeProBankTransPayload = {
      project: props.project!,
      deal_date: trans.bankForm.deal_date,
      bank_account: Number(trans.bankForm.bank_account),
      amount: trans.bankForm.amount!,
      sort: trans.bankForm.sort,
      content: trans.bankForm.content,
      note: trans.bankForm.note,
      accounting_entries: mapEntriesToPayload(trans.entries),
    }

    const ok = await proLedgerStore.createProBankTrans(payload)
    if (!ok) {
      if (savedCount > 0) {
        bankTransactions.value = bankTransactions.value.slice(savedCount)
      }
      return false
    }
    savedCount++
  }

  return true
}

const saveTransaction = async (event: Event) => {
  if (!canAccessForm.value) return
  const isFormInvalid = isValidate(event) || !isFormValid.value
  if (isFormInvalid) {
    validated.value = true
    event.preventDefault()
    event.stopPropagation()
    return
  }

  if (isSaving.value) return

  try {
    isSaving.value = true

    if (isCreateMode.value) {
      const ok = await saveMultipleTransactions()
      if (!ok) return
      bankTransactions.value = []
    } else {
      const payload = buildUpdatePayload()
      const ok = await proLedgerStore.updateProBankTrans(payload)
      if (!ok) return
    }

    skipLeaveGuard.value = true
    await router.push({ name: listRouteName.value })
  } catch (error: unknown) {
    console.error('저장 실패:', error)
    const msg = error instanceof Error ? error.message : '저장 중 오류가 발생했습니다.'
    alertModal.value?.callModal('저장 오류', msg, 'mdi-alert-circle', 'danger')
  } finally {
    isSaving.value = false
  }
}

const delTransaction = async () => {
  const pk = transaction.value?.pk
  if (!pk || !canLedgerDelete.value) return
  confirmModal.value?.close()
  const ok = await proLedgerStore.deleteProBankTrans(pk)
  if (!ok) return
  skipLeaveGuard.value = true
  await router.replace({ name: listRouteName.value })
}

const accCallModal = () => {
  if (props.project) refBankAcc.value?.callModal()
}

const onBankCreate = (payload: ProjectBank) =>
  proLedgerStore.createProBankAcc({
    ...payload,
    project: payload.project ?? props.project ?? null,
    is_imprest: props.isImprest ? (payload.is_imprest ?? true) : payload.is_imprest,
  })

const onBankUpdate = (payload: ProjectBank) =>
  proLedgerStore.updateProBankAcc({
    ...payload,
    project: payload.project ?? props.project ?? null,
  })

const isTransactionBalanced = (
  bankAmt: number | null,
  entries: { amount?: number | null }[],
): boolean => {
  if (!bankAmt) return false
  const totalEntries = entries.reduce((sum, e) => sum + (Number(e.amount) || 0), 0)
  return bankAmt === totalEntries
}

const isFormValid = computed(() => {
  if (isCreateMode.value) {
    if (bankTransactions.value.length === 0) return false

    return bankTransactions.value.every(trans => {
      const hasRequiredFields = !!(
        trans.bankForm.deal_date &&
        trans.bankForm.bank_account &&
        trans.bankForm.amount &&
        trans.bankForm.content
      )
      const hasValidEntries =
        trans.entries.length > 0 &&
        trans.entries.every(e => {
          const hasAmount = (e.amount || 0) > 0
          const hasAccount = !!e.account
          return (hasAmount && hasAccount) || (!hasAmount && !hasAccount)
        }) &&
        trans.entries.some(e => (e.amount || 0) > 0)
      const balanced = isTransactionBalanced(trans.bankForm.amount, trans.entries)

      return hasRequiredFields && hasValidEntries && balanced
    })
  } else {
    const hasRequiredFields = !!(
      bankForm.deal_date &&
      bankForm.bank_account &&
      bankForm.amount &&
      bankForm.content
    )
    const hasValidEntries =
      editableEntries.value.length > 0 &&
      editableEntries.value.every(e => {
        const hasAmount = (e.amount || 0) > 0
        const hasAccount = !!e.account
        return (hasAmount && hasAccount) || (!hasAmount && !hasAccount)
      }) &&
      editableEntries.value.some(e => (e.amount || 0) > 0)
    return hasRequiredFields && hasValidEntries && isBalanced.value
  }
})

const isSaveDisabled = computed(() => !canAccessForm.value || isSaving.value)

const hasUnsavedChanges = computed(() => {
  if (!isCreateMode.value || !canAccessForm.value) return false

  return (
    hasEnteredTransactions.value ||
    bankForm.amount !== null ||
    bankForm.content !== '' ||
    editableEntries.value.some(e => e.amount)
  )
})

let resolveLeavePrompt: ((allow: boolean) => void) | null = null

const confirmLeave = () => {
  const resolve = resolveLeavePrompt
  resolveLeavePrompt = null
  leaveConfirmModal.value?.close()
  resolve?.(true)
}

const cancelLeave = () => {
  if (!resolveLeavePrompt) return
  const resolve = resolveLeavePrompt
  resolveLeavePrompt = null
  resolve(false)
}

onBeforeRouteLeave((_to, _from, next) => {
  if (skipLeaveGuard.value || !hasUnsavedChanges.value) {
    next()
    return
  }
  new Promise<boolean>(resolve => {
    resolveLeavePrompt = resolve
    leaveConfirmModal.value?.callModal(
      '페이지 이동 확인',
      '저장하지 않은 변경사항이 있습니다. 페이지를 떠나시겠습니까?',
      'mdi-alert-box',
      'warning',
      '이동',
      'warning',
    )
  }).then(allow => next(allow))
})

onBeforeMount(async () => {
  if (props.project) {
    const needsLoad =
      !proLedgerStore.proBankList.length ||
      !proLedgerStore.proAccountList.length ||
      (!props.isImprest && !paymentStore.payOrderList.length)
    if (needsLoad) {
      await fetchFormData(props.project)
    }
  }

  if (isCreateMode.value) {
    initializeCreateForm()
  } else if (transId.value && canAccessForm.value) {
    await proLedgerStore.fetchProBankTrans(transId.value)
    initializeEditForm()
  }
})
</script>

<template>
  <NoAuth v-if="accStore.userInfo && !canAccessForm" />
  <CForm
    v-else
    class="needs-validation"
    novalidate
    :validated="validated"
    @submit.prevent="saveTransaction"
  >
    <CRow
      class="text-end py-2 mb-1 mx-1"
      :class="
        isImprest
          ? isCreateMode
            ? 'bg-brown-lighten-5'
            : 'bg-amber-lighten-5'
          : isCreateMode
            ? 'bg-light-blue-lighten-5'
            : 'bg-light-green-lighten-5'
      "
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
      <CCol col="2">
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
          variant="flat"
          size="small"
          :disabled="isSaving"
          @click="router.push({ name: listRouteName })"
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
        <col v-if="canLedgerManage" style="width: 3%" />
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
                accept=".xlsx,.xls,.csv"
                style="display: none"
                @change="handleBulkFileChange"
              />
            </template>
          </CTableHeaderCell>
          <CTableHeaderCell class="ps-0" :colspan="canLedgerManage ? 4 : 3">
            <span class="text-grey me-2">|</span> 분류 내역
            <span v-if="isCreateMode" class="text-caption text-grey ms-1">
              (거래건별 엑셀 입력은 각 행의 아이콘 사용)
            </span>
          </CTableHeaderCell>
          <CTableHeaderCell class="px-0">
            <!-- 수정 모드: 단일 거래건의 회계 계정 템플릿 -->
            <template v-if="!isCreateMode">
              <v-icon
                icon="mdi-download"
                size="16"
                color="info"
                class="me-2 pointer"
                @click="handleDownloadTemplate()"
                v-tooltip="'회계 계정 정보 템플릿 다운로드'"
              />
              <v-icon
                icon="mdi-upload"
                size="16"
                color="success"
                class="pointer"
                @click="handleUploadClick()"
                v-tooltip="'회계 계정 정보 엑셀 업로드'"
              />
            </template>

            <input
              ref="fileInputRef"
              type="file"
              accept=".xlsx,.xls"
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
          <CTableHeaderCell v-if="canLedgerManage" scope="col"></CTableHeaderCell>
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
            :project="project"
            :bank-accounts="formBankAccounts"
            :pro-accounts="proLedgerStore.proAccounts"
            :get-contracts="contractStore.getContracts"
            :get-all-contractors="contractStore.getAllContractors"
            @update:transaction="updateBankTransaction(idx, $event)"
            @remove="removeBankTransaction(idx)"
            @detect-transfer-withdraw="handleTransferWithdraw"
            @download-template="handleDownloadTemplate(idx)"
            @upload-entries="handleUploadClick(idx)"
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
            <CTableDataCell>
              <DatePicker v-model="bankForm.deal_date" required />
            </CTableDataCell>

            <CTableDataCell>
              <CFormInput v-model="bankForm.note" placeholder="메모" maxlength="50" />
            </CTableDataCell>

            <CTableDataCell>
              <CFormSelect v-model="bankForm.bank_account" required>
                <option value="">---------</option>
                <option v-for="ba in formBankAccounts" :key="ba.value!" :value="ba.value">
                  {{ ba.label }}
                </option>
              </CFormSelect>
            </CTableDataCell>

            <CTableDataCell>
              <CFormInput v-model="bankForm.content" placeholder="적요" maxlength="100" required />
            </CTableDataCell>

            <CTableDataCell class="text-end">
              <div class="d-flex align-items-center justify-content-end">
                <CFormSelect
                  v-model.number="bankForm.sort"
                  style="width: 70px"
                  required
                  class="me-2"
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

            <CTableDataCell :colspan="canLedgerManage ? 5 : 4" class="p-0">
              <ProAccountEntry
                :sort="bankForm.sort"
                :display-rows="displayRows"
                :trans-amount="bankForm.amount"
                :project="project"
                @update:entries="onEditableEntriesUpdate"
                @remove-entry="removeEntry"
                @insert-transfer-fee="insertTransferFeeEntry"
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
          @click="confirmModal?.callModal()"
          :disabled="!canLedgerDelete || isSaving"
        >
          삭제
        </v-btn>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="confirmModal">
    <template #header>{{ isImprest ? '운영비 거래 내역 삭제' : '거래 내역 삭제' }}</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 입출금 거래 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="delTransaction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="leaveConfirmModal" @confirm-func="confirmLeave" @close="cancelLeave" />

  <AlertModal ref="alertModal" />

  <AccountManage ref="refAccountManage" />

  <BankAcc
    ref="refBankAcc"
    :project="project"
    :is-imprest="isImprest"
    @on-bank-create="onBankCreate"
    @on-bank-update="onBankUpdate"
  />

  <ExcelUploadDialog
    v-model="uploadDialogVisible"
    :parse-result="parseResult"
    :transaction-amount="targetAmount"
    system-type="project"
    @confirm="handleUploadConfirm"
  />

  <BulkTransUploadDialog
    v-model="bulkDialogVisible"
    v-model:result="bulkResult"
    :has-existing="hasEnteredTransactions"
    :pay-orders="isImprest ? undefined : payOrderOptions"
    :bank-accounts="formBankAccounts"
    :accounts="proLedgerStore.proAccounts"
    @confirm="handleBulkConfirm"
  />
</template>

<style scoped lang="scss">
.dark-theme {
  .bg-light-blue-lighten-5 {
    background-color: #27374d !important;
    color: #fff !important;
  }

  .bg-light-green-lighten-5 {
    background-color: #283c34 !important;
    color: #fff !important;
  }

  .bg-brown-lighten-5 {
    background-color: #463a35 !important;
    color: #fff !important;
  }

  .bg-amber-lighten-5 {
    background-color: #4c4a43 !important;
    color: #fff !important;
  }
}
</style>
