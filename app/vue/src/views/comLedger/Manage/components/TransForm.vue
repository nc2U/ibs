<script lang="ts" setup>
import { computed, onBeforeMount, provide, reactive, ref, watch } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { getToday, numFormat } from '@/utils/baseMixins.ts'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import { usePerms } from '@/composables/usePerms'
import type { ParseResult } from '@/composables/useExcelUpload'
import { useExcelUpload } from '@/composables/useExcelUpload'
import { type BulkParseResult, useBulkTransExcel } from '@/composables/useBulkTransExcel'
import { TableSecondary } from '@/utils/cssMixins.ts'
import type { BankTransaction } from '@/store/types/comLedger'
import BankTransactionRow, { type BankTransactionData } from './BankTransactionRow.vue'
import BulkTransUploadDialog from '@/views/proLedger/Manage/components/BulkTransUploadDialog.vue'
import ExcelUploadDialog from '@/components/LedgerAccount/ExcelUploadDialog.vue'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import AccountManage from './AccountManage.vue'
import JournalRow from './JournalRow.vue'
import BankAcc from './BankAcc.vue'

const props = defineProps({
  company: { type: Number, default: null },
})

watch(
  () => props.company,
  async () => {
    if (isCreateMode.value) initializeCreateForm()
    else await router.push({ name: '본사 거래 내역' })
  },
)

const { canGlobal, PERM } = usePerms()
const canComLedgerCreate = computed(() => canGlobal(PERM.HQ_LEDGER_CREATE))
const canComLedgerUpdate = computed(() => canGlobal(PERM.HQ_LEDGER_UPDATE))
const canComLedgerDelete = computed(() => canGlobal(PERM.HQ_LEDGER_DELETE))
const canComLedgerEdit = computed(() =>
  isCreateMode.value ? canComLedgerCreate.value : canComLedgerUpdate.value,
)

const confirmModal = ref()
const alertModal = ref()
const refAccountManage = ref()
const refBankAcc = ref()

const [route, router] = [useRoute(), useRouter()]

const transId = computed(() => Number(route.params.transId) || null)
const isCreateMode = computed(() => !transId.value)
const isSaving = ref(false)

const ledgerStore = useComLedger()
const transferFeePk = computed(() => ledgerStore.transferFeePk)
const transaction = computed(() => ledgerStore.bankTransaction as BankTransaction | null)

// Watch transaction data to reinitialize form when loaded
watch(
  () => transaction.value,
  val => {
    if (val && !isCreateMode.value) {
      initializeEditForm()
    }
  },
)

// 은행 거래 폼 데이터 (생성 모드용)
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

// 입력 폼 데이터
interface NewEntryForm {
  pk?: number
  account?: number | null
  trader?: string
  amount?: number
  affiliate?: number | null
  evidence_type?: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
}

// 수정 가능한 폼 데이터 (기존 데이터 + 새로운 데이터)
const editableEntries = ref<NewEntryForm[]>([])

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

// 폼 초기화 함수들
const initializeCreateForm = () => {
  // 신규 모드: 기본값으로 초기화
  Object.assign(bankForm, {
    deal_date: getToday(),
    bank_account: '',
    amount: null,
    sort: 2,
    content: '',
    note: '',
  })
  editableEntries.value = [{}]

  // 다중 거래건 초기화
  bankTransactions.value = [createNewTransaction()]
}

const initializeEditForm = () => {
  if (!transaction.value) return

  // 수정 모드: 기존 데이터로 초기화
  Object.assign(bankForm, {
    deal_date: transaction.value.deal_date,
    note: transaction.value.note,
    bank_account: transaction.value.bank_account,
    content: transaction.value.content,
    sort: transaction.value.sort,
    amount: transaction.value.amount,
  })

  // 기존 회계 항목들로 초기화
  if (transaction.value.accounting_entries) {
    editableEntries.value = transaction.value.accounting_entries.map(entry => ({
      pk: entry.pk,
      account: entry.account,
      trader: entry.trader,
      amount: entry.amount,
      affiliate: entry.affiliate,
      evidence_type: entry.evidence_type,
    }))
  } else {
    editableEntries.value = [{}]
  }
}

// 표시할 행 목록
const displayRows = computed(() => editableEntries.value)

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

// 차액 계산 - bankAmount 사용
const difference = computed(() => {
  return bankAmount.value - totalEntryAmount.value
})

// 금액 일치 여부
const isBalanced = computed(() => {
  return difference.value === 0
})

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

// File change handler
const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) return

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
    alertModal.value?.callModal('엑셀 파싱 오류', '엑셀 파일 파싱 중 오류가 발생했습니다.', 'mdi-alert-circle', 'danger')
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

  if (!imported.length) return
  bankTransactions.value = replace ? imported : [...bankTransactions.value, ...imported]
  bulkResult.value = null
}

const addRow = () => {
  editableEntries.value.push({})
}

const removeEntry = (index: number) => {
  if (editableEntries.value.length === 1) {
    // entry 개수가 1개일 때는 amount를 0으로 설정 (삭제 처리)
    editableEntries.value[index].amount = 0
  } else {
    // entry 행수가 2개 이상일 배열에서 제거
    editableEntries.value.splice(index, 1)
  }
}

const insertTransferFeeEntry = (index: number) => {
  if (transferFeePk.value === undefined) {
    alertModal.value?.callModal('계정 안내', '이체수수료 계정이 설정되지 않았습니다.', 'mdi-alert-circle', 'warning')
    return
  }

  const currentRow = editableEntries.value[index]
  const bankTransactionAmount = Number(bankForm.amount) || 0

  // Calculate a new amount based on bank transaction amount (minimum 0)
  const newCurrentAmount = Math.max(0, bankTransactionAmount - 500)

  // Modify the current row amount
  currentRow.amount = newCurrentAmount

  // Create a trader name (default to [] if empty)
  const currentTrader = currentRow.trader?.trim() || '[]'

  // Create a new transfer fee entry
  const newEntry: NewEntryForm = {
    pk: undefined,
    account: transferFeePk.value,
    trader: `[${currentTrader}]-이체수수료`,
    amount: 500,
    affiliate: null,
    evidence_type: '0',
  }

  // Insert immediately after the current row
  editableEntries.value.splice(index + 1, 0, newEntry)
}

// ========== 다중 거래건 관련 메서드 ==========
// 거래건 추가
const addBankTransaction = () => {
  bankTransactions.value.push(createNewTransaction())
}

// 거래건 삭제
const removeBankTransaction = (index: number) => {
  if (bankTransactions.value.length > 1) {
    bankTransactions.value.splice(index, 1)
  }
}

// 거래건 업데이트
const updateBankTransaction = (index: number, newData: BankTransactionData) => {
  bankTransactions.value[index] = newData
}

// 대체(출금) 거래 자동 추가
const handleTransferWithdraw = (sourceData: BankTransactionData) => {
  const sourceAccount = ledgerStore.comAccounts.find(
    acc => acc.value === sourceData.entries[0].account,
  )

  if (!sourceAccount || sourceAccount.category !== 'transfer') return

  // 대체(입금) 계정 찾기 (category='transfer' && direction='입금')
  const depositTransferAccount = ledgerStore.comAccounts.find(
    acc => acc.is_cate_only === false && acc.category === 'transfer' && acc.direction === '입금',
  )

  if (!depositTransferAccount) {
    alertModal.value?.callModal('계정 안내', '대체(입금) 계정을 찾을 수 없습니다.', 'mdi-alert-circle', 'warning')
    return
  }

  // 입금 거래건 자동 추가
  bankTransactions.value.push({
    bankForm: {
      deal_date: sourceData.bankForm.deal_date,
      note: sourceData.bankForm.note,
      bank_account: null, // 사용자가 선택해야 함
      content: sourceData.bankForm.content,
      sort: 1, // 입금
      amount: sourceData.bankForm.amount,
    },
    entries: [
      {
        account: depositTransferAccount.value,
        trader: sourceData.entries[0].trader || '',
        amount: sourceData.bankForm.amount || undefined,
        evidence_type: '',
      },
    ],
  })
}

// 유효성 검사
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

// 신규 거래 데이터 생성
const buildCreatePayload = () => {
  validateForm()

  const validEntries = editableEntries.value
    .filter(e => (e.amount || 0) > 0)
    .map(entry => ({
      ...entry,
      evidence_type: entry.evidence_type === '' ? null : entry.evidence_type,
    }))

  return {
    company: props.company!,
    deal_date: bankForm.deal_date,
    bank_account: bankForm.bank_account!,
    amount: bankForm.amount!,
    sort: bankForm.sort,
    content: bankForm.content,
    note: bankForm.note,
    accounting_entries: validEntries,
  } as any // API 요청 타입과 BankTransaction 타입이 다르므로 any 처리
}

// 수정 거래 데이터 생성
const buildUpdatePayload = () => {
  if (!transaction.value) {
    throw new Error('수정할 거래 데이터가 없습니다.')
  }

  validateForm()

  const validEntries = editableEntries.value
    .filter(e => (e.amount || 0) > 0)
    .map(entry => ({
      ...entry,
      evidence_type: entry.evidence_type === '' ? null : entry.evidence_type,
    }))

  return {
    pk: transaction.value.pk,
    company: props.company!,
    deal_date: bankForm.deal_date,
    bank_account: bankForm.bank_account!,
    amount: bankForm.amount!,
    sort: bankForm.sort,
    content: bankForm.content,
    note: bankForm.note,
    accounting_entries: validEntries,
    filters: {},
  } as any // API 요청 타입과 BankTransaction 타입이 다르므로 any 처리
}

// 다중 거래건 저장 처리
const saveMultipleTransactions = async () => {
  // 모든 거래건 검증
  for (let i = 0; i < bankTransactions.value.length; i++) {
    const trans = bankTransactions.value[i]

    if (!trans.bankForm.deal_date || !trans.bankForm.bank_account || !trans.bankForm.amount) {
      throw new Error(`${i + 1}번째 거래: 거래일자, 거래계좌, 금액은 필수 입력 항목입니다.`)
    }

    if (!trans.bankForm.content) {
      throw new Error(`${i + 1}번째 거래: 적요는 필수 입력 항목입니다.`)
    }

    const validEntries = trans.entries.filter(e => (e.amount || 0) > 0)
    if (validEntries.length === 0) {
      throw new Error(`${i + 1}번째 거래: 최소 하나 이상의 분류 항목이 필요합니다.`)
    }

    const totalEntryAmount = validEntries.reduce((sum, e) => sum + (Number(e.amount) || 0), 0)
    if (trans.bankForm.amount !== totalEntryAmount) {
      throw new Error(`${i + 1}번째 거래: 거래 금액과 분류 금액이 일치하지 않습니다.`)
    }
  }

  // 각 거래건을 순차적으로 저장
  for (const trans of bankTransactions.value) {
    const validEntries = trans.entries
      .filter(e => (e.amount || 0) > 0)
      .map(entry => ({
        ...entry,
        evidence_type: entry.evidence_type === '' ? null : entry.evidence_type,
      }))

    const payload = {
      company: props.company!,
      deal_date: trans.bankForm.deal_date,
      bank_account: trans.bankForm.bank_account!,
      amount: trans.bankForm.amount!,
      sort: trans.bankForm.sort,
      content: trans.bankForm.content,
      note: trans.bankForm.note,
      accounting_entries: validEntries,
    } as any

    await ledgerStore.createBankTransaction(payload)
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
        // 다중 거래건이 있으면 다중 저장, 없으면 단일 저장
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

      // 성공 시 거래 목록 페이지로 이동
      await router.push({ name: '본사 거래 내역' })
    } catch (error: any) {
      console.error('저장 실패:', error)
      alertModal.value?.callModal('저장 오류', error.message || '저장 중 오류가 발생했습니다.', 'mdi-alert-circle', 'danger')
    } finally {
      isSaving.value = false
    }
  }
}

const delTransaction = async () => {
  confirmModal.value.close()
  await ledgerStore.deleteBankTransaction(transaction.value?.pk!)
  await router.replace({ name: '본사 거래 내역' })
}

const accCallModal = () => {
  if (props.company) refBankAcc.value.callModal()
}

onBeforeMount(async () => {
  if (isCreateMode.value) {
    // 신규 모드: 기본 폼으로 초기화
    initializeCreateForm()
  } else if (transId.value) {
    // 수정 모드: 기존 거래 데이터 로드 후 폼 초기화
    await ledgerStore.fetchBankTransaction(transId.value)
    initializeEditForm()
  }
})

// 거래건별 금액 일치 확인 헬퍼 함수
const isTransactionBalanced = (
  bankAmount: number | null,
  entries: { amount?: number | null }[],
): boolean => {
  if (!bankAmount) return false
  const totalEntries = entries.reduce((sum, e) => sum + (Number(e.amount) || 0), 0)
  return bankAmount === totalEntries
}

// 폼 유효성 검사 상태
const isFormValid = computed(() => {
  if (isCreateMode.value) {
    // 신규 모드: 모든 거래건 검증
    if (bankTransactions.value.length === 0) return false

    return bankTransactions.value.every(trans => {
      const hasRequiredFields = !!(
        trans.bankForm.deal_date &&
        trans.bankForm.bank_account &&
        trans.bankForm.amount
      )
      const hasValidEntries =
        trans.entries.length > 0 &&
        trans.entries.every(e => {
          const hasAmount = (e.amount || 0) > 0
          const hasAccount = !!e.account
          return (hasAmount && hasAccount) || (!hasAmount && !hasAccount)
        }) &&
        trans.entries.some(e => (e.amount || 0) > 0)
      const isBalanced = isTransactionBalanced(trans.bankForm.amount, trans.entries)

      return hasRequiredFields && hasValidEntries && isBalanced
    })
  } else {
    // 수정 모드: 기존 단일 거래건 검증
    const hasRequiredFields = !!(bankForm.deal_date && bankForm.bank_account && bankForm.amount)
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

// 저장 버튼 비활성화 상태
const isSaveDisabled = computed(() => {
  return isSaving.value
})

// 네비게이션 가드
const hasUnsavedChanges = computed(() => {
  if (!isCreateMode.value) return false

  return (
    hasEnteredTransactions.value ||
    bankForm.amount !== null ||
    bankForm.content !== '' ||
    editableEntries.value.some(e => e.amount)
  )
})

onBeforeRouteLeave((to, from, next) => {
  if (hasUnsavedChanges.value) {
    const answer = window.confirm('저장하지 않은 변경사항이 있습니다. 페이지를 떠나시겠습니까?')
    next(answer)
  } else {
    next()
  }
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
          <span class="ml-2 text-success strong">분할 중...</span>
        </template>
      </CCol>
      <CCol col="2">
        <span> 거래내역 금액: {{ sortName }} {{ numFormat(bankAmount, 0, '0') }} </span>
        ∙
        <span>분류 금액 합계: {{ sortName }} {{ numFormat(totalEntryAmount, 0, '0') }}</span> ∙
        <span class="strong mr-3" :class="{ 'text-danger': !isBalanced }">
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
          <CTableHeaderCell class="pl-3" colspan="5">
            은행거래내역
            <!-- 신규 모드: 다수 은행거래 + 회계 계정 엑셀 대량 입력 -->
            <template v-if="isCreateMode">
              <span class="text-grey mx-2">|</span>
              <span class="text-caption mr-1">대량 입력</span>
              <v-icon
                icon="mdi-download"
                size="16"
                color="info"
                class="mr-2 pointer"
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
          <CTableHeaderCell class="pl-0" :colspan="canComLedgerEdit ? 4 : 3">
            <span class="text-grey mr-2">|</span> 분류 내역
            <span v-if="isCreateMode" class="text-caption text-grey ml-1">
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
                class="mr-2 pointer"
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
            <a href="#" @click.prevent="refAccountManage.callModal()">
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
          />

          <!-- 거래건 추가 버튼 행 -->
          <CTableRow class="bg-light">
            <CTableDataCell colspan="10" class="text-center py-2">
              <v-btn size="small" color="primary" variant="outlined" @click="addBankTransaction">
                <v-icon icon="mdi-plus" class="mr-1" />
                은행거래건 추가
              </v-btn>
              <small class="text-muted ml-3">
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
              <CFormSelect v-model="bankForm.bank_account" required>
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
            <CTableDataCell class="text-right">
              <div class="d-flex align-items-center justify-content-end">
                <CFormSelect
                  v-model.number="bankForm.sort"
                  style="width: 70px"
                  required
                  class="mr-2"
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
                  class="text-right"
                />
                <v-btn density="compact" rounded="1" size="22" class="ml-2 pointer" @click="addRow">
                  <v-icon icon="mdi-plus" color="success" />
                </v-btn>
              </div>
            </CTableDataCell>

            <CTableDataCell :colspan="canComLedgerEdit ? 5 : 4" class="p-0">
              <JournalRow
                :sort="bankForm.sort"
                :display-rows="displayRows"
                :trans-amount="bankForm.amount"
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
          @click="confirmModal.callModal()"
          :disabled="!canComLedgerDelete"
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
    :result="bulkResult"
    :has-existing="hasEnteredTransactions"
    :bank-accounts="formBankAccounts"
    :accounts="ledgerStore.comAccounts"
    related-label="관계회사(프로젝트)"
    @confirm="handleBulkConfirm"
  />
</template>
