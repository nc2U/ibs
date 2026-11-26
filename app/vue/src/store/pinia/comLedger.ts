import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { cleanupParams, errorHandle, message } from '@/utils/helper'
import {
  type BankCode,
  type Affiliate,
  type BalanceByAccount,
  type CompanyAccount,
  type BankTransaction,
  type ComCalculated,
  type CompanyBank,
  type CompositeTransactionPayload,
  type CompositeTransactionPatchPayload,
  type LedgerTransactionForDisplay,
  type ComMonthlySummary,
} from '@/store/types/comLedger'

export type DataFilter = {
  page?: number
  company?: number | null
  from_date?: string
  to_date?: string
  sort?: 1 | 2 | null
  account_category?:
    'asset' | 'liability' | 'equity' | 'revenue' | 'expense' | 'transfer' | 'cancel' | ''
  account?: number | null
  affiliate?: number | null | ''
  bank_account?: number | null
  search?: string
  limit?: number
}

export type ComAccountFilter = {
  category?: string
  direction?: string
  parent?: number | null
  is_category_only?: boolean | ''
  is_active?: boolean | ''
  search?: string
}

export const useComLedger = defineStore('comLedger', () => {
  // state & getters - bankCode
  const bankCodeList = ref<BankCode[]>([])
  const comBankList = ref<CompanyBank[]>([])
  const getComBanks = computed(() =>
    comBankList.value.map(bk => ({ value: bk.pk, label: bk.alias_name })),
  )
  const allComBankList = ref<CompanyBank[]>([])

  const fetchBankCodeList = async () =>
    await api
      .get('/ledger/bank-code/')
      .then(res => (bankCodeList.value = res.data.results))
      .catch(err => errorHandle(err))

  const fetchComBankAccList = async (company: number) =>
    await api
      .get(`/ledger/company-bank-account/?company=${company}&is_hide=false&inactive=false`)
      .then(res => (comBankList.value = res.data.results))
      .catch(err => errorHandle(err))

  const fetchAllComBankAccList = async (company: number) =>
    await api
      .get(`/ledger/company-bank-account/?company=${company}`)
      .then(res => (allComBankList.value = res.data.results))
      .catch(err => errorHandle(err))

  const createComBankAcc = async (payload: CompanyBank) =>
    await api
      .post(`/ledger/company-bank-account/`, payload)
      .then(async res => {
        await fetchAllComBankAccList(res.data.company)
        await fetchComBankAccList(res.data.company).then(() => message())
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        throw err
      })

  const updateComBankAcc = async (payload: CompanyBank) =>
    await api
      .put(`/ledger/company-bank-account/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllComBankAccList(res.data.company)
        await fetchComBankAccList(res.data.company).then(() => message())
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        throw err
      })

  const patchComBankAcc = async (payload: CompanyBank) =>
    await api
      .patch(`/ledger/company-bank-account/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllComBankAccList(res.data.company)
        await fetchComBankAccList(res.data.company).then(() => message())
      })
      .catch(err => errorHandle(err))

  const deleteComBankAcc = async (pk: number, company: number) =>
    await api
      .delete(`/ledger/company-bank-account/${pk}/`)
      .then(async () => {
        await fetchAllComBankAccList(company)
        await fetchComBankAccList(company)
        message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err))

  // state & getters - Accounts
  const comAccountList = ref<CompanyAccount[]>([])
  const comAccountFilter = ref<ComAccountFilter>({})
  const comAccounts = computed(() =>
    comAccountList.value
      .filter(acc => acc.is_active && acc.pk !== undefined)
      .map(acc => ({
        value: acc.pk!,
        label: acc.name,
        parent: acc.parent,
        depth: acc.depth,
        category: acc.category,
        direction: acc.direction_display,
        is_cate_only: acc.is_category_only,
        req_affiliate: acc.requires_affiliate,
      })),
  )
  const transferFeePk = computed(() => comAccountList.value.find(acc => acc.is_transfer_fee)?.pk)

  const fetchCompanyAccounts = async (payload: ComAccountFilter = {}) => {
    comAccountFilter.value = payload
    const params = cleanupParams({
      category: payload.category,
      direction: payload.direction,
      parent: payload.parent,
      is_category_only: payload.is_category_only,
      is_active: payload.is_active,
      search: payload.search,
    })

    return await api
      .get('/ledger/company-account/', { params })
      .then(res => {
        comAccountList.value = res.data.results
      })
      .catch(err => errorHandle(err))
  }

  // state & getters - Affiliate
  const affiliateList = ref<Affiliate[]>([])
  const affiliates = computed(() =>
    affiliateList.value.map(aff => ({
      value: aff.pk,
      label: `[${aff.sort === 'company' ? 'CO' : 'PR'}]${aff.company_name ?? aff.project_name}`,
      sort: aff.sort,
      id: aff.company ?? aff.project,
    })),
  )

  const fetchAffiliateList = async (payload?: { sort?: 'company' | 'project' }) => {
    const params = payload?.sort ? { sort: payload.sort } : {}
    return await api
      .get('/ledger/affiliate/', { params })
      .then(res => (affiliateList.value = res.data.results))
      .catch(err => errorHandle(err))
  }

  // state & getters - bankTransaction
  const bankTransactionFilter = ref<DataFilter>({})
  const bankTransaction = ref<BankTransaction | null>(null)
  const bankTransactionList = ref<BankTransaction[]>([])
  const bankTransactionCount = ref<number>(0)

  const transPages = (itemsPerPage: number) => Math.ceil(bankTransactionCount.value / itemsPerPage)

  const fetchBankTransaction = async (pk: number) =>
    await api
      .get(`/ledger/company-transaction/${pk}/`)
      .then(res => {
        bankTransaction.value = res.data
      })
      .catch(err => errorHandle(err))

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
      .catch(err => errorHandle(err))
  }

  const findBankTransactionPage = async (highlightId: number, filters: DataFilter) => {
    const params = cleanupParams({
      highlight_id: highlightId,
      company: filters.company,
      from_deal_date: filters.from_date,
      to_deal_date: filters.to_date,
      sort: filters.sort,
      account_category: filters.account_category,
      account: filters.account,
      affiliate: filters.affiliate,
      bank_account: filters.bank_account,
      search: filters.search,
      limit: filters.limit,
    })

    try {
      const response = await api.get('/ledger/company-transaction/find_page/', { params })
      return response.data.page
    } catch (err: unknown) {
      errorHandle(err)
      return 1
    }
  }

  const createBankTransaction = async (
    payload: CompositeTransactionPayload,
    options?: { skipRefresh?: boolean; silent?: boolean },
  ) =>
    await api
      .post(`/ledger/company-composite-transaction/`, payload)
      .then(async res => {
        if (!options?.skipRefresh) {
          await fetchBankTransactionList(bankTransactionFilter.value)
        }
        if (!options?.silent) message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        throw err
      })

  const updateBankTransaction = async (payload: CompositeTransactionPatchPayload) => {
    const { pk, ...formData } = payload
    return await api
      .put(`/ledger/company-composite-transaction/${pk}/`, formData)
      .then(async res => {
        await fetchBankTransactionList(bankTransactionFilter.value)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        throw err
      })
  }

  const patchBankTransaction = async (payload: CompositeTransactionPatchPayload) => {
    const { pk, ...formData } = payload
    return await api
      .patch(`/ledger/company-composite-transaction/${pk}/`, formData)
      .then(async res => {
        await fetchBankTransactionList(bankTransactionFilter.value)
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        throw err
      })
  }

  const deleteBankTransaction = async (pk: number) => {
    return await api
      .delete(`/ledger/company-composite-transaction/${pk}/`)
      .then(async () => {
        await fetchBankTransactionList(bankTransactionFilter.value)
        message('warning', '알림!', '본사 거래 데이터가 삭제되었습니다.')
      })
      .catch(err => {
        errorHandle(err)
        throw err
      })
  }

  // ============================================
  // Status 페이지용 Ledger API (신규 추가)
  // ============================================
  const comLedgerBalanceByAccList = ref<BalanceByAccount[]>([])
  const dateLedgerTransactions = ref<BankTransaction[]>([])
  const dateLedgerForDisplay = computed<LedgerTransactionForDisplay[]>(() =>
    dateLedgerTransactions.value
      .filter(tx => tx.pk !== undefined)
      .map(tx => ({
        pk: tx.pk!,
        company: tx.company,
        sort: tx.sort,
        sort_desc: tx.sort_name,
        account: null,
        content: tx.content,
        trader: tx.accounting_entries?.[0]?.trader || '',
        bank_account: tx.bank_account,
        bank_account_desc: tx.bank_account_name,
        amount: tx.amount,
        deal_date: tx.deal_date,
        note: tx.note,
      })),
  )

  const comLedgerCalculation = ref<ComCalculated[]>([])
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
      .catch(err => errorHandle(err))
  }

  const fetchDateLedgerTransactionList = async (payload: { company: number; date: string }) => {
    const { company, date } = payload
    return await api
      .get(`/ledger/company-transaction/daily_transactions/?company=${company}&date=${date}`)
      .then(res => (dateLedgerTransactions.value = res.data.results))
      .catch(err => errorHandle(err))
  }

  // 월별 자금 집계 (수입/지출, 전월·누계 비교)
  const comMonthlySummary = ref<ComMonthlySummary | null>(null)
  let monthlySummarySeq = 0

  const fetchComMonthlySummary = async (payload: {
    company: number
    from_date: string
    to_date: string
  }) => {
    const seq = ++monthlySummarySeq
    return await api
      .get('/ledger/company-transaction/monthly_summary/', { params: payload })
      .then(res => {
        if (seq === monthlySummarySeq) comMonthlySummary.value = res.data
        return res.data as ComMonthlySummary
      })
      .catch(err => {
        if (seq === monthlySummarySeq) comMonthlySummary.value = null
        errorHandle(err.response?.data ?? err)
        return null
      })
  }

  // 월별 자금 집계 계정 드릴다운용 거래 조회 (공유 상태를 건드리지 않는 단발성 조회)
  const fetchComMonthlyDrilldown = async (payload: {
    company: number
    from_deal_date: string
    to_deal_date: string
    account: number
    sort: 1 | 2
    page: number
  }) =>
    await api
      .get('/ledger/company-transaction/', { params: payload })
      .then(res => res.data as { count: number; results: BankTransaction[] })
      .catch(err => {
        errorHandle(err.response?.data ?? err)
        return null
      })

  const fetchComLedgerCalculation = async (com: number) =>
    await api
      .get(`/ledger/company-calculation/?company=${com}`)
      .then(res => (comLedgerCalculation.value = res.data.results))
      .catch(err => errorHandle(err))

  const createComLedgerCalculation = async (payload: ComCalculated) =>
    await api
      .post(`/ledger/company-calculation/`, payload)
      .then(res => fetchComLedgerCalculation(res.data.company).then(() => message()))
      .catch(err => errorHandle(err))

  const patchComLedgerCalculation = async (payload: ComCalculated) =>
    await api
      .patch(`/ledger/company-calculation/${payload.pk}/`, payload)
      .then(res => fetchComLedgerCalculation(res.data.company).then(() => message()))
      .catch(err => errorHandle(err))

  const fetchComLedgerLastDealDate = async (com: number) =>
    await api
      .get(`/ledger/company-last-deal-date/?company=${com}`)
      .then(res => (comLedgerLastDealList.value = res.data.results))
      .catch(err => errorHandle(err))

  // --- Picker 공유 상태 및 로직 ---
  const sharedEditingState = ref<{ type: 'tran' | 'entry'; pk: number; field: string } | null>(null)
  const sharedPickerPosition = ref<{ top: number; left: number; width: number } | null>(null)

  const clearSharedPickerState = () => {
    sharedEditingState.value = null
    sharedPickerPosition.value = null
  }

  return {
    bankCodeList,
    comBankList,
    getComBanks,
    allComBankList,
    fetchBankCodeList,
    fetchComBankAccList,
    fetchAllComBankAccList,
    createComBankAcc,
    updateComBankAcc,
    patchComBankAcc,
    deleteComBankAcc,

    comAccountList,
    comAccountFilter,
    comAccounts,
    transferFeePk,
    fetchCompanyAccounts,

    affiliateList,
    affiliates,
    fetchAffiliateList,

    bankTransaction,
    bankTransactionFilter,
    bankTransactionList,
    bankTransactionCount,
    transPages,
    fetchBankTransaction,
    fetchComMonthlyDrilldown,
    fetchBankTransactionList,
    findBankTransactionPage,
    createBankTransaction,
    updateBankTransaction,
    patchBankTransaction,
    deleteBankTransaction,

    // Status 페이지용 (신규)
    comLedgerBalanceByAccList,
    dateLedgerTransactions,
    dateLedgerForDisplay,

    comLedgerCalculation,
    comLedgerCalculated,

    comLedgerLastDealList,
    comLedgerLastDealDate,

    fetchComLedgerBalanceByAccList,
    fetchDateLedgerTransactionList,

    comMonthlySummary,
    fetchComMonthlySummary,

    fetchComLedgerCalculation,
    createComLedgerCalculation,
    patchComLedgerCalculation,
    fetchComLedgerLastDealDate,

    // Shared Picker State
    sharedEditingState,
    sharedPickerPosition,
    clearSharedPickerState,
  }
})
