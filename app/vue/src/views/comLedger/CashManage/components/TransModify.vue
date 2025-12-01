<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { numFormat } from '@/utils/baseMixins.ts'
import { useComLedger } from '@/store/pinia/comLedger.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { write_company_cash } from '@/utils/pageAuth.ts'
import type { CompanyBank } from '@/store/types/comLedger'
import type { BankTransaction } from '@/store/types/comLedger'
import Devided from './Devided.vue'
import BankAcc from './BankAcc.vue'
import AccDepth from './AccDepth.vue'

const props = defineProps({
  company: { type: Number, default: null },
})

const emit = defineEmits(['patch-d3-hide', 'on-bank-create', 'on-bank-update'])

const refAccDepth = ref()
const refBankAcc = ref()
const rowCount = ref(0)

const [route, router] = [useRoute(), useRouter()]

const transId = computed(() => Number(route.params.transId) || null)

const ledgerStore = useComLedger()
const transaction = computed(() => ledgerStore.bankTransaction as BankTransaction | null)

// 입력 폼 데이터
interface NewEntryForm {
  pk?: number
  account_d1?: number | null
  account_d3?: number | null
  trader?: string
  amount?: number
  evidence_type?: string | number | null
}

// 수정 가능한 폼 데이터 (기존 데이터 + 새로운 데이터)
const editableEntries = ref<NewEntryForm[]>([])

// 기존 데이터를 편집 가능한 폼 데이터로 변환
const initializeEditableEntries = () => {
  if (!transaction.value?.accounting_entries) return

  editableEntries.value = transaction.value.accounting_entries.map(entry => ({
    pk: entry.pk,
    account_d1: entry.account_d1,
    account_d3: entry.account_d3,
    trader: entry.trader,
    amount: entry.amount,
    evidence_type: entry.evidence_type,
  }))
}

// 표시할 행 목록 - 이제 editableEntries를 직접 반환
const displayRows = computed(() => editableEntries.value)

// 분류 금액 합계 계산
const totalEntryAmount = computed(() => {
  return displayRows.value.reduce((sum, row) => {
    return sum + (Number(row.amount) || 0)
  }, 0)
})

// 차액 계산 (은행 거래 금액 - 분류 금액 합계)
const difference = computed(() => {
  const bankAmount = transaction.value?.amount || 0
  return bankAmount - totalEntryAmount.value
})

// 금액 일치 여부
const isBalanced = computed(() => {
  return difference.value === 0
})

const addRow = () => {
  // 새로운 빈 객체를 editableEntries에 직접 추가
  editableEntries.value.push({})
  rowCount.value++
}

const removeEntry = (index: number) => {
  // 기존 entry인 경우 (pk가 있는 경우)
  if (index < editableEntries.value.length && editableEntries.value[index].pk) {
    // amount만 0으로 변경 (삭제하지 않음)
    editableEntries.value[index].amount = 0
  } else {
    // 새로 추가된 행인 경우
    if (index < editableEntries.value.length) {
      // editableEntries에서 제거
      editableEntries.value.splice(index, 1)
    }
    // rowCount 감소
    rowCount.value--
  }
}
const onBankCreate = (payload: CompanyBank) => emit('on-bank-create', payload)
const onBankUpdate = (payload: CompanyBank) => emit('on-bank-update', payload)

const accCallModal = () => {
  if (props.company) refBankAcc.value.callModal()
}

const patchD3Hide = (payload: { pk: number; is_hide: boolean }) => emit('patch-d3-hide', payload)

onBeforeMount(async () => {
  if (transId.value) await ledgerStore.fetchBankTransaction(transId.value)
  initializeEditableEntries()
  rowCount.value = editableEntries.value.length
})
</script>

<template>
  <CRow class="text-right py-2 mb-1 bg-light-green-lighten-5 mx-1">
    <CCol class="text-left">
      {{ transaction?.deal_date }} ∙ {{ transaction?.bank_account_name }} ∙
      {{ transaction?.content }}
      <span class="ml-2 text-success strong">분할 중...</span>
    </CCol>
    <CCol col="2">
      <span>
        거래내역 금액: {{ transaction?.sort_name }} {{ numFormat(transaction?.amount ?? 0) }}
      </span>
      ∙
      <span>분류 금액 합계: {{ transaction?.sort_name }} {{ numFormat(totalEntryAmount) }}</span> ∙
      <span class="strong mr-3" :class="{ 'text-danger': !isBalanced }">
        차액: {{ transaction?.sort_name }} {{ numFormat(Math.abs(difference)) }}
      </span>
      <!--      <v-btn size="x-small" disabled>증빙으로 분할</v-btn>-->
      <v-btn size="x-small" @click="router.push({ name: '본사 거래 내역' })">취소</v-btn>
      <v-btn color="success" size="x-small" :disabled="!!difference">저장</v-btn>
    </CCol>
  </CRow>
  <hr class="mb-0" />
  <CTable hover responsive class="mb-5">
    <colgroup>
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 6%" />
      <col style="width: 12%" />
      <col style="width: 8%" />
      <col style="width: 5%" />
      <col style="width: 11%" />
      <col style="width: 13%" />
      <col style="width: 11%" />
      <col style="width: 8%" />
      <col v-if="write_company_cash" style="width: 5%" />
    </colgroup>

    <CTableHead class="sticky-table-head">
      <CTableRow :color="TableSecondary" class="sticky-header-row-1">
        <CTableHeaderCell class="pl-3" colspan="5">은행거래내역</CTableHeaderCell>
        <CTableHeaderCell class="pl-0" :colspan="write_company_cash ? 6 : 5">
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
        <CTableHeaderCell class="text-left pl-0" scope="col">
          <span class="text-grey mr-2">|</span> 계정
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">
          세부계정
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
        <CTableDataCell>{{ transaction?.deal_date ?? '' }}</CTableDataCell>
        <CTableDataCell>{{ transaction?.note }}</CTableDataCell>
        <CTableDataCell>{{ transaction?.bank_account_name }}</CTableDataCell>
        <CTableDataCell>{{ transaction?.content }}</CTableDataCell>
        <CTableDataCell class="text-right">
          {{ numFormat(transaction?.amount ?? 0) }}
          <v-btn
            icon="mdi-plus"
            density="compact"
            rounded="1"
            size="22"
            class="ml-2 pointer"
            @click="addRow"
          />
        </CTableDataCell>
        <CTableDataCell colspan="6">
          <Devided :display-rows="displayRows" @remove-entry="removeEntry" />
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

.sticky-header-row-1 th {
  background-color: #e3f2fd;
}

/* 헤더 두 번째 행 고정 */
.sticky-header-row-2 {
  position: sticky;
  top: 38px; /* 첫 번째 헤더 행 높이만큼 */
  z-index: 30;
}

.sticky-header-row-2 th {
  background-color: #e3f2fd;
}

/* 은행거래내역 행 고정 */
.sticky-bank-row {
  position: sticky;
  top: 76px; /* 두 헤더 행 높이의 합 */
  z-index: 20;
  background-color: white;
}

.sticky-bank-row td {
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>
