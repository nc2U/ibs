<script lang="ts" setup>
import { computed, inject, onBeforeMount, reactive, ref, toRef, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { getToday, numFormat } from '@/utils/baseMixins.ts'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { write_company_cash } from '@/utils/pageAuth.ts'
import type { BankTransaction, CompanyBank } from '@/store/types/comLedger'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import JournalRow from './JournalRow.vue'
import BankAcc from './BankAcc.vue'
import AccDepth from './AccDepth.vue'

const props = defineProps({
  company: { type: Number, default: null },
})

const emit = defineEmits(['patch-d3-hide', 'on-bank-create', 'on-bank-update'])

const refAccDepth = ref()
const refBankAcc = ref()

const [route, router] = [useRoute(), useRouter()]

const transId = computed(() => Number(route.params.transId) || null)
const isCreateMode = computed(() => !transId.value)
const isSaving = ref(false)

const ledgerStore = useComLedger()
const transaction = computed(() => ledgerStore.bankTransaction as BankTransaction | null)
const allComBankList = inject('allComBankList')

// 입력 폼 데이터
interface NewEntryForm {
  pk?: number
  account?: number | null
  trader?: string
  amount?: number
  affiliated?: number | null
  evidence_type?: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
}

// 수정 가능한 폼 데이터 (기존 데이터 + 새로운 데이터)
const editableEntries = ref<NewEntryForm[]>([])

// 디버깅을 위한 watch
watch(
  editableEntries,
  newEntries => {
    console.log('editableEntries 변경됨:', newEntries)
  },
  { deep: true },
)

// 은행 거래 폼 데이터 (생성 모드용)
interface BankTransactionForm {
  deal_date: string
  note: string
  bank_account: number | null
  content: string
  sort: 1 | 2
  amount: number | null
}

const bankForm = reactive<BankTransactionForm>({
  deal_date: getToday(),
  bank_account: null,
  amount: null,
  sort: 1,
  content: '',
  note: '',
})

// 폼 초기화 함수들
const initializeCreateForm = () => {
  // 신규 모드: 기본값으로 초기화
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
    const newEntries = transaction.value.accounting_entries.map(entry => ({
      pk: entry.pk,
      account: entry.account,
      trader: entry.trader,
      amount: entry.amount,
      affiliated: entry.affiliated,
      evidence_type: entry.evidence_type,
    }))
    editableEntries.value = newEntries
  } else {
    editableEntries.value = [{}]
  }
}

// 표시할 행 목록
const displayRows = computed(() => editableEntries.value)

// 은행 거래 금액 - 생성/수정 모드에 따라 다른 소스
const bankAmount = computed(() => {
  return isCreateMode.value ? bankForm.amount || 0 : transaction.value?.amount || 0
})

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
  const total = editableEntries.value.reduce((sum, row) => {
    const amount = Number(row.amount) || 0
    return sum + amount
  }, 0)
  console.log('totalEntryAmount 계산:', {
    entries: editableEntries.value,
    amounts: editableEntries.value.map(row => ({
      amount: row.amount,
      converted: Number(row.amount) || 0,
    })),
    total,
  })
  return total
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
const getComBanks = computed(() => ledgerStore.getComBanks)

const addRow = () => {
  editableEntries.value.push({})
}

const removeEntry = (index: number) => {
  if (index < editableEntries.value.length && editableEntries.value[index].pk) {
    // 기존 entry는 amount를 0으로 설정 (삭제 처리)
    editableEntries.value[index].amount = 0
  } else {
    // 새로 추가된 행은 배열에서 제거
    editableEntries.value.splice(index, 1)
  }
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

  const validEntries = editableEntries.value.filter(e => (e.amount || 0) > 0)

  return {
    company: props.company!,
    deal_date: bankForm.deal_date,
    bank_account: bankForm.bank_account!,
    amount: bankForm.amount!,
    sort: bankForm.sort,
    content: bankForm.content,
    note: bankForm.note,
    accData: {
      entries: validEntries,
    },
  } as any // API 요청 타입과 BankTransaction 타입이 다르므로 any 처리
}

// 수정 거래 데이터 생성
const buildUpdatePayload = () => {
  if (!transaction.value) {
    throw new Error('수정할 거래 데이터가 없습니다.')
  }

  validateForm()

  const validEntries = editableEntries.value.filter(e => (e.amount || 0) > 0)

  return {
    pk: transaction.value.pk,
    company: props.company!,
    deal_date: bankForm.deal_date,
    bank_account: bankForm.bank_account!,
    amount: bankForm.amount!,
    sort: bankForm.sort,
    content: bankForm.content,
    note: bankForm.note,
    accData: {
      entries: validEntries,
    },
    filters: {},
  } as any // API 요청 타입과 BankTransaction 타입이 다르므로 any 처리
}

// 저장 처리
const saveTransaction = async () => {
  if (isSaving.value) return

  try {
    isSaving.value = true

    if (isCreateMode.value) {
      const payload = buildCreatePayload()
      await ledgerStore.createBankTransaction(payload)
    } else {
      const payload = buildUpdatePayload()
      await ledgerStore.updateBankTransaction(payload)
    }

    // 성공 시 거래 목록 페이지로 이동
    await router.push({ name: '본사 거래 내역' })
  } catch (error: any) {
    console.error('저장 실패:', error)
    alert(error.message || '저장 중 오류가 발생했습니다.')
  } finally {
    isSaving.value = false
  }
}

const onBankCreate = (payload: CompanyBank) => emit('on-bank-create', payload)
const onBankUpdate = (payload: CompanyBank) => emit('on-bank-update', payload)

const accCallModal = () => {
  if (props.company) refBankAcc.value.callModal()
}

const patchD3Hide = (payload: { pk: number; is_hide: boolean }) => emit('patch-d3-hide', payload)

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

// 폼 유효성 검사 상태
const isFormValid = computed(() => {
  const hasRequiredFields = !!(
    bankForm.deal_date &&
    bankForm.bank_account &&
    bankForm.amount &&
    bankForm.content
  )

  const hasValidEntries = editableEntries.value.some(e => (e.amount || 0) > 0)

  return hasRequiredFields && hasValidEntries && isBalanced.value
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
  <CRow
    class="text-right py-2 mb-1 mx-1"
    :class="isCreateMode ? 'bg-light-blue-lighten-5' : 'bg-light-green-lighten-5'"
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
      <span> 거래내역 금액: {{ sortName }} {{ numFormat(bankAmount) }} </span>
      ∙
      <span>분류 금액 합계: {{ sortName }} {{ (numFormat(totalEntryAmount), '0') }}</span> ∙
      <span class="strong mr-3" :class="{ 'text-danger': !isBalanced }">
        차액: {{ sortName }} {{ (numFormat(Math.abs(difference)), '0') }}
      </span>
      <v-btn
        size="x-small"
        variant="outlined"
        :disabled="isSaving"
        @click="router.push({ name: '본사 거래 내역' })"
      >
        취소
      </v-btn>
      <v-btn
        :color="isCreateMode ? 'primary' : 'success'"
        size="x-small"
        :disabled="isSaveDisabled"
        :loading="isSaving"
        @click="saveTransaction"
      >
        {{
          isSaving ? (isCreateMode ? '생성 중...' : '저장 중...') : isCreateMode ? '생성' : '저장'
        }}
      </v-btn>
    </CCol>
  </CRow>

  <hr class="mb-0" />
  <CTable hover class="mb-5">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 12%" />
      <col style="width: 8%" />
      <col style="width: 12%" />
      <col style="width: 10%" />

      <col style="width: 13%" />
      <col style="width: 13%" />
      <col style="width: 10%" />
      <col style="width: 11%" />
      <col v-if="write_company_cash" style="width: 3%" />
    </colgroup>

    <CTableHead class="sticky-table-head">
      <CTableRow :color="TableSecondary" class="sticky-header-row-1">
        <CTableHeaderCell class="pl-3" colspan="5">은행거래내역</CTableHeaderCell>
        <CTableHeaderCell class="pl-0" :colspan="write_company_cash ? 5 : 4">
          <span class="text-grey mr-2">|</span> 분류 내역
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
            <CIcon name="cilCog" @click="refAccDepth.callModal()" />
          </a>
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">거래처</CTableHeaderCell>
        <CTableHeaderCell scope="col">분류 금액</CTableHeaderCell>
        <CTableHeaderCell scope="col">지출증빙</CTableHeaderCell>
        <CTableHeaderCell v-if="write_company_cash" scope="col"></CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow class="sticky-bank-row">
        <!-- 거래일자 -->
        <CTableDataCell>
          <DatePicker v-model="bankForm.deal_date" required />
        </CTableDataCell>

        <!-- 메모 -->
        <CTableDataCell>
          <CFormInput v-model="bankForm.note" size="sm" placeholder="메모" maxlength="50" />
        </CTableDataCell>

        <!-- 거래계좌 -->
        <CTableDataCell>
          <CFormSelect v-model.number="bankForm.bank_account" size="sm" required>
            <option :value="null">---------</option>
            <option v-for="ba in getComBanks" :key="ba.value" :value="ba.value">
              {{ ba.label }}
            </option>
          </CFormSelect>
          <!--          <a href="javascript:void(0)" class="ml-2">-->
          <!--            <CIcon name="cilCog" @click="accCallModal" />-->
          <!--          </a>-->
        </CTableDataCell>

        <!-- 적요 -->
        <CTableDataCell>
          <CFormInput
            v-model="bankForm.content"
            size="sm"
            placeholder="적요"
            maxlength="100"
            required
          />
        </CTableDataCell>

        <!-- 입출금액 -->
        <CTableDataCell class="text-right">
          <div class="d-flex align-items-center justify-content-end">
            <CFormSelect
              v-model.number="bankForm.sort"
              size="sm"
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
              size="sm"
              min="0"
              placeholder="금액"
              required
              style="width: 120px"
              class="text-right"
            />
            <v-btn
              icon="mdi-plus"
              density="compact"
              rounded="1"
              size="22"
              class="ml-2 pointer"
              @click="addRow"
            />
          </div>
        </CTableDataCell>

        <CTableDataCell colspan="7">
          <JournalRow :display-rows="displayRows" @remove-entry="removeEntry" />
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <AccDepth ref="refAccDepth" @patch-d3-hide="patchD3Hide" />

  <BankAcc ref="refBankAcc" @on-bank-create="onBankCreate" @on-bank-update="onBankUpdate" />
</template>

<style scoped>
/* 헤더 첫 번째 행 고정 */
.sticky-header-row-1 {
  position: sticky;
  top: 0;
  z-index: 30;
}

/* 헤더 두 번째 행 고정 */
.sticky-header-row-2 {
  position: sticky;
  top: 38px; /* 첫 번째 헤더 행 높이만큼 */
  z-index: 30;
}

/* 은행거래내역 행 고정 */
.sticky-bank-row {
  position: sticky;
  top: 76px; /* 두 헤더 행 높이의 합 */
  z-index: 20;
}

.sticky-bank-row td {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 드롭다운이 테이블 외부로 렌더링되도록 설정 */
:deep(table),
:deep(tbody),
:deep(tr),
:deep(td) {
  overflow: visible !important;
}
</style>
