<script lang="ts" setup>
import { computed, onBeforeMount, reactive, ref, watch } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { getToday, numFormat } from '@/utils/baseMixins.ts'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { write_project_cash } from '@/utils/pageAuth.ts'
import type { ProBankTrans } from '@/store/types/proLedger.ts'
import DatePicker from '@/components/DatePicker/DatePicker.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import JournalRow from './JournalRow.vue'
import BankAcc from './BankAcc.vue'
import AccountManage from './AccountManage.vue'

const props = defineProps({
  project: { type: Number, default: null },
})

watch(
  () => props.project,
  val => {
    if (isCreateMode.value) initializeCreateForm()
    else router.push({ name: 'PR 거래 내역' })
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
  affiliate?: number | null
  evidence_type?: '' | '0' | '1' | '2' | '3' | '4' | '5' | '6'
}

// 수정 가능한 폼 데이터 (기존 데이터 + 새로운 데이터)
const editableEntries = ref<NewEntryForm[]>([])

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

// 저장 처리
const saveTransaction = async (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (isSaving.value) return

    try {
      isSaving.value = true

      if (isCreateMode.value) {
        const payload = buildCreatePayload()
        console.log(payload)
        await proLedgerStore.createProBankTrans(payload)
      } else {
        const payload = buildUpdatePayload()
        console.log(payload)
        await proLedgerStore.updateProBankTrans(payload)
      }

      // 성공 시 거래 목록 페이지로 이동
      await router.push({ name: 'PR 거래 내역' })
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
  await router.replace({ name: 'PR 거래 내역' })
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

// 폼 유효성 검사 상태
const isFormValid = computed(() => {
  const hasRequiredFields = !!(bankForm.deal_date && bankForm.bank_account && bankForm.amount)
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
  <CForm
    class="needs-validation"
    novalidate
    :validated="validated"
    @submit.prevent="saveTransaction"
  >
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
          @click="router.push({ name: 'PR 거래 내역' })"
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
          <CTableHeaderCell class="pl-0" :colspan="write_project_cash ? 5 : 4">
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
              <CFormSelect v-model.number="bankForm.sort" style="width: 70px" required class="mr-2">
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
</template>
