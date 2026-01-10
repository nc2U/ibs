<script lang="ts" setup>
import { computed, onBeforeMount, reactive, ref, watch } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { getToday, numFormat } from '@/utils/baseMixins.ts'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import { useContract } from '@/store/pinia/contract.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { write_project_cash } from '@/utils/pageAuth.ts'
import type { ProBankTrans } from '@/store/types/proLedger.ts'
import type { ParseResult } from '@/composables/useExcelUpload'
import { useExcelUpload } from '@/composables/useExcelUpload'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import ExcelUploadDialog from '@/components/LedgerAccount/ExcelUploadDialog.vue'
import BankAcc from './BankAcc.vue'
import JournalRow from './JournalRow.vue'
import AccountManage from './AccountManage.vue'
import BankTransactionRow, { type BankTransactionData } from './BankTransactionRow.vue'

const props = defineProps({
  project: { type: Number, default: null },
})

watch(
  () => props.project,
  val => {
    if (isCreateMode.value) initializeCreateForm()
    else router.push({ name: '운영 계좌 내역' })
  },
)

const confirmModal = ref()
const refAccountManage = ref()
const refBankAcc = ref()

const [route, router] = [useRoute(), useRouter()]

const transId = computed(() => Number(route.params.transId) || null)
const isCreateMode = computed(() => !transId.value)
const isSaving = ref(false)

const proLedgerStore = useProLedger()
const contractStore = useContract()
const transaction = computed(() => proLedgerStore.proBankTrans as ProBankTrans | null)

// 은행 거래 폼 데이터 (생성 모드용)
interface ProBankTransForm {
  deal_date: string
  note: string
  bank_account: number | null
  content: string
  sort: 1 | 2
  amount: number | null
}

const validated = ref(false)
const bankForm = reactive<ProBankTransForm>({
  deal_date: getToday(),
  sort: 1,
  amount: null,
  content: '',
  note: '',
  bank_account: null,
})

// 입력 폼 데이터
interface NewEntryForm {
  pk?: number
  account?: number | null
  trader?: string
  amount?: number
  contract?: number | null
  evidence_type?: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
}

// 수정 가능한 폼 데이터 (기존 데이터 + 새로운 데이터) - 수정 모드용
const editableEntries = ref<NewEntryForm[]>([])

// 신규 생성 모드용: 다수 은행거래건 배열
const bankTransactions = ref<BankTransactionData[]>([])

// 폼 초기화 함수들
const initializeCreateForm = () => {
  // 신규 모드: 다수 거래건 구조로 초기화 (기본 1개 거래건)
  bankTransactions.value = [
    {
      bankForm: {
        deal_date: getToday(),
        bank_account: null,
        amount: null,
        sort: 1,
        content: '',
        note: '',
      },
      entries: [{}],
    },
  ]

  // 기존 단일 거래건 폼도 초기화 (하위 호환성 유지)
  Object.assign(bankForm, {
    deal_date: getToday(),
    bank_account: null,
    amount: null,
    sort: 1,
    content: '',
    note: '',
  })
  editableEntries.value = [{}]
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
      contract: entry.contract,
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
  const activeBanks = proLedgerStore.getProBanks

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
  const currentBank = proLedgerStore.allProBankList.find(b => b.pk === currentBankId)
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

// Excel upload state
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadDialogVisible = ref(false)
const parseResult = ref<ParseResult | null>(null)
const { parseExcelFile, downloadTemplate } = useExcelUpload()

// Download template handler
const handleDownloadTemplate = () => {
  // Resolve account and contract IDs to names
  const entries = editableEntries.value.map(entry => {
    // Find the account name from ID
    const account = proLedgerStore.proAccounts.find(acc => acc.value === entry.account)
    const account_name = account?.label || ''

    // Find a contract name from ID
    const contract = contractStore.getContracts.find(c => c.value === entry.contract)
    const contract_name = contract?.label || ''

    return {
      account_name,
      trader: entry.trader || '',
      amount: entry.amount || 0,
      evidence_type: entry.evidence_type || '',
      contract_name,
    }
  })

  downloadTemplate({ amount: bankForm.amount || 0, entries }, 'project')
}

// Upload click handler
const handleUploadClick = () => {
  fileInputRef.value?.click()
}

// File change handler
const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) return

  try {
    // Prepare existing entries for matching - resolve IDs to names
    const existingEntries = editableEntries.value.map(entry => {
      // Find the account name from ID
      const account = proLedgerStore.proAccounts.find(acc => acc.value === entry.account)
      const account_name = account?.label || ''

      // Find a contract name from ID
      const contract = contractStore.getContracts.find(c => c.value === entry.contract)
      const contract_name = contract?.label || ''

      return {
        pk: entry.pk,
        account: entry.account ?? undefined,
        account_name,
        trader: entry.trader || '',
        amount: entry.amount || 0,
        evidence_type: entry.evidence_type || '',
        contract: entry.contract ?? undefined, // Convert null to undefined
        contract_name,
      }
    })

    // Parse Excel file with matching
    await parseExcelFile(
      file,
      proLedgerStore.proAccounts,
      existingEntries,
      bankForm.amount || 0,
      'project',
      contractStore.getContracts,
    ).then(result => {
      parseResult.value = result
      uploadDialogVisible.value = true
    })
  } catch (error) {
    console.error('Excel parsing error:', error)
    alert('엑셀 파일 파싱 중 오류가 발생했습니다.')
  } finally {
    // Reset file input
    target.value = ''
  }
}

// Confirm upload handler
const handleUploadConfirm = () => {
  if (!parseResult.value) return

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
      existingEntry.contract = parsedEntry.contract ?? null
    }
  })

  // Step 2: Create new entries (no pk)
  parseResult.value.entriesToCreate.forEach(parsedEntry => {
    if (!parsedEntry.isValid) return // Skip invalid

    editableEntries.value.push({
      pk: undefined,
      account: parsedEntry.account ?? null,
      trader: parsedEntry.trader,
      amount: parsedEntry.amount,
      evidence_type: parsedEntry.evidence_type as NewEntryForm['evidence_type'],
      contract: parsedEntry.contract ?? null,
    })
  })

  // Step 3: Delete entries (remove from an array)
  parseResult.value.entriesToDelete.forEach(entryToDelete => {
    const index = editableEntries.value.findIndex(e => e.pk === entryToDelete.pk)
    if (index !== -1) {
      editableEntries.value.splice(index, 1)
    }
  })

  uploadDialogVisible.value = false
  parseResult.value = null
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

// === 신규 모드용 다수 거래건 메서드 ===

// 새 은행거래건 추가
const addBankTransaction = () => {
  bankTransactions.value.push({
    bankForm: {
      deal_date: getToday(),
      bank_account: null,
      amount: null,
      sort: 1,
      content: '',
      note: '',
    },
    entries: [{}],
  })
}

// 은행거래건 삭제
const removeBankTransaction = (index: number) => {
  if (bankTransactions.value.length > 1) {
    bankTransactions.value.splice(index, 1)
  }
}

// 거래건 업데이트
const updateBankTransaction = (index: number, data: BankTransactionData) => {
  bankTransactions.value[index] = data
}

// 대체(출금) 거래 감지 시 대체(입금) 거래 자동 추가
const handleTransferWithdraw = (sourceData: BankTransactionData) => {
  // 대체(입금) 계정 찾기 (category='transfer' && direction='입금')
  const depositTransferAccount = proLedgerStore.proAccounts.find(
    acc => acc.category === 'transfer' && acc.direction === '입금',
  )

  if (!depositTransferAccount) {
    console.warn('대체(입금) 계정을 찾을 수 없습니다.')
    return
  }

  // 새로운 대체(입금) 거래건 추가
  bankTransactions.value.push({
    bankForm: {
      deal_date: sourceData.bankForm.deal_date,
      bank_account: null, // 사용자가 선택해야 함 (출발 계좌와 달라야 함)
      amount: sourceData.bankForm.amount,
      sort: 1, // 입금
      content: sourceData.bankForm.content,
      note: sourceData.bankForm.note,
    },
    entries: [
      {
        account: depositTransferAccount.value, // 대체(입금) 계정 자동 선택
        trader: sourceData.entries[0]?.trader || '',
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
    project: props.project!,
    deal_date: bankForm.deal_date,
    bank_account: bankForm.bank_account!,
    amount: bankForm.amount!,
    sort: bankForm.sort,
    content: bankForm.content,
    note: bankForm.note,
    accounting_entries: validEntries,
  } as any // API 요청 타입과 ProBankTrans 타입이 다르므로 any 처리
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
    project: props.project!,
    deal_date: bankForm.deal_date,
    bank_account: bankForm.bank_account!,
    amount: bankForm.amount!,
    sort: bankForm.sort,
    content: bankForm.content,
    note: bankForm.note,
    accounting_entries: validEntries,
    filters: {},
  } as any // API 요청 타입과 ProBankTrans 타입이 다르므로 any 처리
}

// 신규 모드용: 다수 거래건 저장
const saveMultipleTransactions = async () => {
  // 각 거래건 검증
  for (let i = 0; i < bankTransactions.value.length; i++) {
    const trans = bankTransactions.value[i]

    // 필수 필드 검증
    if (
      !trans.bankForm.deal_date ||
      !trans.bankForm.bank_account ||
      !trans.bankForm.amount ||
      !trans.bankForm.content
    ) {
      throw new Error(`거래건 ${i + 1}: 거래일자, 거래계좌, 금액, 적요는 필수 입력 항목입니다.`)
    }

    // 금액 일치 검증
    const bankAmount = trans.bankForm.amount || 0
    const entryTotal = trans.entries.reduce((sum, e) => sum + (Number(e.amount) || 0), 0)
    if (bankAmount !== entryTotal) {
      throw new Error(
        `거래건 ${i + 1}: 거래 금액(${bankAmount})과 분류 금액(${entryTotal})이 일치하지 않습니다.`,
      )
    }

    // 유효한 분개 항목 검증
    const validEntries = trans.entries.filter(e => (e.amount || 0) > 0)
    if (validEntries.length === 0) {
      throw new Error(`거래건 ${i + 1}: 최소 하나 이상의 분류 항목이 필요합니다.`)
    }
  }

  // 각 거래건을 개별적으로 API 호출
  for (const trans of bankTransactions.value) {
    const validEntries = trans.entries
      .filter(e => (e.amount || 0) > 0)
      .map(entry => ({
        ...entry,
        evidence_type: entry.evidence_type === '' ? null : entry.evidence_type,
      }))

    const payload = {
      project: props.project!,
      deal_date: trans.bankForm.deal_date,
      bank_account: trans.bankForm.bank_account!,
      amount: trans.bankForm.amount!,
      sort: trans.bankForm.sort,
      content: trans.bankForm.content,
      note: trans.bankForm.note,
      accounting_entries: validEntries,
    } as any

    await proLedgerStore.createProBankTrans(payload)
  }
}

// 저장 처리
const saveTransaction = async (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (isSaving.value) return

    try {
      isSaving.value = true

      if (isCreateMode.value) {
        // 신규 모드: 다수 거래건 저장
        await saveMultipleTransactions()
      } else {
        // 수정 모드: 기존 단일 거래건 저장
        const payload = buildUpdatePayload()
        await proLedgerStore.updateProBankTrans(payload)
      }

      // 성공 시 거래 목록 페이지로 이동
      await router.push({ name: '운영 계좌 내역' })
    } catch (error: any) {
      console.error('저장 실패:', error)
      alert(error.message || '저장 중 오류가 발생했습니다.')
    } finally {
      isSaving.value = false
    }
  }
}

const delTransaction = async () => {
  confirmModal.value.close()
  await proLedgerStore.deleteProBankTrans(transaction.value?.pk!)
  await router.replace({ name: '운영 계좌 내역' })
}

const accCallModal = () => {
  if (props.project) refBankAcc.value.callModal()
}

onBeforeMount(async () => {
  if (isCreateMode.value) {
    // 신규 모드: 기본 폼으로 초기화
    initializeCreateForm()
  } else if (transId.value) {
    // 수정 모드: 기존 거래 데이터 로드 후 폼 초기화
    await proLedgerStore.fetchProBankTrans(transId.value)
    initializeEditForm()
  }
})

// 단일 거래건의 균형 검사 헬퍼 함수
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
      const hasValidEntries = trans.entries.some(e => (e.amount || 0) > 0)
      const isBalanced = isTransactionBalanced(trans.bankForm.amount, trans.entries)

      return hasRequiredFields && hasValidEntries && isBalanced
    })
  } else {
    // 수정 모드: 기존 단일 거래건 검증
    const hasRequiredFields = !!(bankForm.deal_date && bankForm.bank_account && bankForm.amount)
    const hasValidEntries = editableEntries.value.some(e => (e.amount || 0) > 0)
    return hasRequiredFields && hasValidEntries && isBalanced.value
  }
})

// 저장 버튼 비활성화 상태
const isSaveDisabled = computed(() => {
  return isSaving.value || !isFormValid.value
})

// 네비게이션 가드
const hasUnsavedChanges = computed(() => {
  if (!isCreateMode.value) return false

  return (
    bankForm.amount !== null || bankForm.content !== '' || editableEntries.value.some(e => e.amount)
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
      class="text-right py-2 mb-1 mx-1"
      :class="isCreateMode ? 'bg-brown-lighten-5' : 'bg-amber-lighten-5'"
    >
      <CCol class="text-left">
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
          color="light"
          size="small"
          :disabled="isSaving"
          @click="router.push({ name: '운영 계좌 내역' })"
        >
          취소
        </v-btn>
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
        <col v-if="write_project_cash" style="width: 3%" />
      </colgroup>

      <CTableHead class="sticky-table-head">
        <CTableRow :color="TableSecondary" class="sticky-header-row-1">
          <CTableHeaderCell class="pl-3" colspan="5">은행거래내역</CTableHeaderCell>
          <CTableHeaderCell class="pl-0" :colspan="write_project_cash ? 4 : 3">
            <span class="text-grey mr-2">|</span> 분류 내역
          </CTableHeaderCell>
          <CTableHeaderCell class="px-0">
            <!-- Download Template -->
            <v-icon
              icon="mdi-download"
              size="16"
              color="info"
              class="mr-2 pointer"
              @click="handleDownloadTemplate"
              v-tooltip="'회계 계정 정보 템플릿 다운로드'"
            />

            <!-- Upload Excel -->
            <v-icon
              icon="mdi-upload"
              size="16"
              color="success"
              class="pointer"
              @click="handleUploadClick"
              v-tooltip="'회계 계정 정보 엑셀 업로드'"
            />

            <!-- Hidden file input -->
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
            <a href="javascript:void(0)">
              <CIcon name="cilCog" @click="accCallModal" />
            </a>
          </CTableHeaderCell>
          <CTableHeaderCell scope="col">적요</CTableHeaderCell>
          <CTableHeaderCell scope="col">입출금액</CTableHeaderCell>
          <CTableHeaderCell scope="col">
            계정
            <a href="javascript:void(0)">
              <CIcon name="cilCog" @click="refAccountManage.callModal()" />
            </a>
          </CTableHeaderCell>
          <CTableHeaderCell scope="col">거래처</CTableHeaderCell>
          <CTableHeaderCell scope="col">분류 금액</CTableHeaderCell>
          <CTableHeaderCell scope="col">지출증빙</CTableHeaderCell>
          <CTableHeaderCell v-if="write_project_cash" scope="col"></CTableHeaderCell>
        </CTableRow>
      </CTableHead>

      <CTableBody>
        <!-- 신규 모드: 다수 거래건 입력 (BankTransactionRow 사용) -->
        <template v-if="isCreateMode">
          <BankTransactionRow
            v-for="(trans, idx) in bankTransactions"
            :key="`trans-${idx}`"
            :transaction="trans"
            :index="idx"
            :bank-accounts="formBankAccounts"
            :pro-accounts="proLedgerStore.proAccounts"
            :get-contracts="contractStore.getContracts"
            :get-all-contractors="contractStore.getAllContractors"
            @update:transaction="updateBankTransaction(idx, $event)"
            @remove="removeBankTransaction(idx)"
            @detect-transfer-withdraw="handleTransferWithdraw"
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
              <CFormSelect v-model.number="bankForm.bank_account" required>
                <option :value="null">---------</option>
                <option v-for="ba in formBankAccounts" :key="ba.value!" :value="ba.value">
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

            <CTableDataCell colspan="7" class="p-0">
              <JournalRow
                :sort="bankForm.sort"
                :display-rows="displayRows"
                :trans-amount="bankForm.amount"
                @remove-entry="removeEntry"
              />
            </CTableDataCell>
          </CTableRow>
        </template>
      </CTableBody>
    </CTable>

    <CRow v-if="!isCreateMode" class="text-right px-2">
      <CCol>
        <v-btn
          color="warning"
          size="small"
          @click="confirmModal.callModal()"
          :disabled="!write_project_cash"
        >
          삭제
        </v-btn>
      </CCol>
    </CRow>
  </CForm>

  <ConfirmModal ref="confirmModal">
    <template #header>본서 거래 내역 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 입출금 거래 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn size="small" color="warning" @click="delTransaction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AccountManage ref="refAccountManage" />

  <BankAcc ref="refBankAcc" />

  <ExcelUploadDialog
    v-model="uploadDialogVisible"
    :parse-result="parseResult"
    :transaction-amount="bankForm.amount ?? 0"
    system-type="project"
    @confirm="handleUploadConfirm"
  />
</template>
