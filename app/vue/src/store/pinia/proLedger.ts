import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { cleanupParams, errorHandle, message } from '@/utils/helper'
import type {
  ProjectAccount,
  ProBankTransaction,
  ProAccountingEntry,
  BalanceByAccount,
  ProCalculated,
  LedgerTransactionForDisplay,
} from '@/store/types/proLedger.ts'

export type DataFilter = {
  page?: number
  company?: number | null
  from_date?: string
  to_date?: string
  sort?: 1 | 2 | null
  account_category?:
    | 'asset'
    | 'liability'
    | 'equity'
    | 'revenue'
    | 'expense'
    | 'transfer'
    | 'cancel'
    | ''
  account?: number | null
  affiliate?: number | null | ''
  bank_account?: number | null
  search?: string
  limit?: number
}

export type ProAccountFilter = {
  category?: string
  direction?: string
  parent?: number | null
  is_category_only?: boolean | ''
  is_active?: boolean | ''
  search?: string
}

export const useProLedger = defineStore('proLedger', () => {
  // state & getters
  const proAccountList = ref<ProjectAccount[]>([])
  const proAccountFilter = ref<ProAccountFilter>({})
  const proAccounts = computed(() =>
    proAccountList.value
      .filter(acc => acc.is_active && acc.pk !== undefined)
      .map(acc => ({
        value: acc.pk!,
        label: acc.name,
        parent: acc.parent,
        depth: acc.depth,
        category: acc.category,
        direction: acc.direction_display,
        is_cate_only: acc.is_category_only,
        is_payment: acc.is_payment,
        is_related_contract: acc.is_related_contract,
      })),
  )

  const fetchProjectAccounts = async (payload: ProAccountFilter = {}) => {
    proAccountFilter.value = payload
    const params = cleanupParams({
      category: payload.category,
      direction: payload.direction,
      parent: payload.parent,
      is_category_only: payload.is_category_only,
      is_active: payload.is_active,
      search: payload.search,
    })

    return await api
      .get('/ledger/project-account/', { params })
      .then(res => {
        proAccountList.value = res.data.results
      })
      .catch(err => errorHandle(err.response.data))
  }

  // state & getters - bankTransaction
  const bankTransactionFilter = ref<DataFilter>({})
  const bankTransaction = ref<ProBankTransaction | null>(null)
  const bankTransactionList = ref<ProBankTransaction[]>([])
  const bankTransactionCount = ref<number>(0)

  const transPages = (itemsPerPage: number) => Math.ceil(bankTransactionCount.value / itemsPerPage)

  const fetchBankTransaction = async (pk: number) =>
    await api
      .get(`/ledger/company-transaction/${pk}/`)
      .then(res => {
        bankTransaction.value = res.data
      })
      .catch(err => errorHandle(err.response.data))

  const fetchBankTransactionList = async (payload: DataFilter = {}) => {
    const params = cleanupParams({
      company: payload.company,
      from_deal_date: payload.from_date,
      to_deal_date: payload.to_date,
      sort: payload.sort,
      account_category: payload.account_category,
      account: payload.account,
      bank_account: payload.bank_account,
      affiliate: payload.affiliate,
      search: payload.search,
      page: payload.page || 1,
    })

    return await api
      .get('/ledger/company-transaction/', { params })
      .then(res => {
        bankTransactionFilter.value = payload
        bankTransactionList.value = res.data.results
        bankTransactionCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const findBankTransactionPage = async (highlightId: number, filters: DataFilter) => {
    const { company } = filters
    let url = `/ledger/company-transaction/find_page/?highlight_id=${highlightId}&company=${company}`
    if (filters.from_date) url += `&from_deal_date=${filters.from_date}`
    if (filters.to_date) url += `&to_deal_date=${filters.to_date}`
    if (filters.sort) url += `&sort=${filters.sort}`
    if (filters.account) url += `&account=${filters.account}`
    if (filters.affiliate) url += `&affiliate=${filters.affiliate}`
    if (filters.bank_account) url += `&bank_account=${filters.bank_account}`
    if (filters.search) url += `&search=${filters.search}`

    try {
      const response = await api.get(url)
      return response.data.page
    } catch (err: any) {
      errorHandle(err.response.data)
      return 1
    }
  }

  const createBankTransaction = async (
    payload: ProBankTransaction & { accData: ProAccountingEntry | null },
  ) =>
    await api
      .post(`/ledger/company-composite-transaction/`, payload)
      .then(async res => {
        return await fetchBankTransactionList(bankTransactionFilter.value).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateBankTransaction = async (
    payload: ProBankTransaction & { accData: ProAccountingEntry | null },
  ) => {
    const { pk, ...formData } = payload
    return await api
      .put(`/ledger/company-composite-transaction/${pk}/`, formData)
      .then(async res => {
        return await fetchBankTransactionList(bankTransactionFilter.value).then(() => message())
      })
      .catch(err => errorHandle(err.response?.data))
  }

  const patchBankTransaction = async (
    payload: Partial<ProBankTransaction & { accData: ProAccountingEntry | null }>,
  ) => {
    const { pk, ...formData } = payload
    return await api
      .patch(`/ledger/company-composite-transaction/${pk}/`, formData)
      .then(async res => {
        return await fetchBankTransactionList(bankTransactionFilter.value)
      })
      .catch(err => errorHandle(err.response?.data))
  }

  const deleteBankTransaction = async (pk: number) => {
    return await api
      .delete(`/ledger/company-composite-transaction/${pk}/`)
      .then(async () => {
        return await fetchBankTransactionList(bankTransactionFilter.value).then(() =>
          message('warning', '알림!', '본사 거래 데이터가 삭제되었습니다.'),
        )
      })
      .catch(err => errorHandle(err.response?.data))
  }

  // ============================================
  // Status 페이지용 Ledger API (신규 추가)
  // ============================================
  const comLedgerBalanceByAccList = ref<BalanceByAccount[]>([])
  const dateLedgerTransactions = ref<ProBankTransaction[]>([])
  // const dateLedgerForDisplay = computed<LedgerTransactionForDisplay[]>(() =>
  //   dateLedgerTransactions.value.map(tx => ({
  //     pk: tx.pk,
  //     company: tx.company,
  //     sort: tx.sort,
  //     sort_desc: tx.sort_name,
  //     account: null,
  //     content: tx.content,
  //     trader: tx.accounting_entries?.[0]?.trader || '',
  //     bank_account: tx.bank_account,
  //     bank_account_desc: tx.bank_account_name,
  //     income: tx.sort === 1 ? tx.amount : null,
  //     outlay: tx.sort === 2 ? tx.amount : null,
  //     deal_date: tx.deal_date,
  //     note: tx.note,
  //   })),
  // )

  const comLedgerCalculation = ref<ProCalculated[]>([])
  const comLedgerCalculated = computed(() =>
    comLedgerCalculation.value.length ? comLedgerCalculation.value[0] : null,
  )

  const comLedgerLastDealList = ref<{ deal_date: string }[]>([])
  const comLedgerLastDealDate = computed(() =>
    comLedgerLastDealList.value.length ? comLedgerLastDealList.value[0] : null,
  )

  const fetchComLedgerBalanceByAccList = async (payload: {
    company: number
    date: string
    is_balance?: '' | 'true'
  }) => {
    const { company, date, is_balance = '' } = payload
    return await api
      .get(
        `/ledger/company-transaction/balance_by_account/?company=${company}&date=${date}&is_balance=${is_balance}`,
      )
      .then(res => (comLedgerBalanceByAccList.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchDateLedgerTransactionList = async (payload: { company: number; date: string }) => {
    const { company, date } = payload
    return await api
      .get(`/ledger/company-transaction/daily_transactions/?company=${company}&date=${date}`)
      .then(res => (dateLedgerTransactions.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchComLedgerCalculation = async (com: number) =>
    await api
      .get(`/ledger/company-calculation/?company=${com}`)
      .then(res => (comLedgerCalculation.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createComLedgerCalculation = async (payload: ProCalculated) =>
    await api
      .post(`/ledger/company-calculation/`, payload)
      .then(res => fetchComLedgerCalculation(res.data.company).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const patchComLedgerCalculation = async (payload: ProCalculated) =>
    await api
      .patch(`/ledger/company-calculation/${payload.pk}/`, payload)
      .then(res => fetchComLedgerCalculation(res.data.company).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const fetchComLedgerLastDealDate = async (com: number) =>
    await api
      .get(`/ledger/company-last-deal-date/?company=${com}`)
      .then(res => (comLedgerLastDealList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  return {
    proAccountList,
    proAccountFilter,
    proAccounts,

    fetchProjectAccounts,

    bankTransaction,
    bankTransactionFilter,
    bankTransactionList,
    bankTransactionCount,
    transPages,
    fetchBankTransaction,
    fetchBankTransactionList,
    findBankTransactionPage,
    createBankTransaction,
    updateBankTransaction,
    patchBankTransaction,
    deleteBankTransaction,

    // Status 페이지용 (신규)
    comLedgerBalanceByAccList,
    dateLedgerTransactions,
    // dateLedgerForDisplay,

    comLedgerCalculation,
    comLedgerCalculated,

    comLedgerLastDealList,
    comLedgerLastDealDate,

    fetchComLedgerBalanceByAccList,
    fetchDateLedgerTransactionList,

    fetchComLedgerCalculation,
    createComLedgerCalculation,
    patchComLedgerCalculation,
    fetchComLedgerLastDealDate,
  }
})
