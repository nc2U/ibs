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
  type AccountingEntry,
  type CompanyBankTransaction,
  type LedgerTransactionForDisplay,
} from '@/store/types/comLedger'

export type DataFilter = {
  page?: number
  company?: number | null
  from_date?: string
  to_date?: string
  sort?: 1 | 2 | null
  account?: number | null
  affiliate?: number | null
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

  const fetchBankCodeList = async () =>
    await api
      .get('/ledger/bank-code/')
      .then(res => (bankCodeList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  // state & getters - Affiliate
  const affiliateList = ref<Affiliate[]>([])
  const affiliates = computed(() =>
    affiliateList.value.map(aff => ({
      value: aff.pk,
      label: `[${aff.sort === 'company' ? 'CO' : 'PR'}]${aff.company_name ?? aff.project_name}`,
    })),
  )

  const fetchAffiliateList = async (payload?: { sort?: 'company' | 'project' }) => {
    const params = payload?.sort ? { sort: payload.sort } : {}
    return await api
      .get('/ledger/affiliate/', { params })
      .then(res => (affiliateList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

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
        direction: acc.direction_display,
        is_cate_only: acc.is_category_only,
        req_affiliate: acc.requires_affiliate,
      })),
  )

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
      .catch(err => errorHandle(err.response.data))
  }

  // state & getters - comBankList
  const comBankList = ref<CompanyBank[]>([])
  const getComBanks = computed(() =>
    comBankList.value.map(bk => ({ value: bk.pk, label: bk.alias_name })),
  )
  const allComBankList = ref<CompanyBank[]>([])

  const fetchComBankAccList = async (company: number) =>
    await api
      .get(`/ledger/company-bank-account/?company=${company}&is_hide=false&inactive=false`)
      .then(res => (comBankList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchAllComBankAccList = async (company: number) =>
    await api
      .get(`/ledger/company-bank-account/?company=${company}`)
      .then(res => (allComBankList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createComBankAcc = async (payload: CompanyBank) =>
    await api
      .post(`/ledger/company-bank-account/`, payload)
      .then(async res => {
        await fetchAllComBankAccList(res.data.company)
        await fetchComBankAccList(res.data.company).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateComBankAcc = async (payload: CompanyBank) =>
    await api
      .put(`/ledger/company-bank-account/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllComBankAccList(res.data.company)
        await fetchComBankAccList(res.data.company).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const patchComBankAcc = async (payload: CompanyBank) =>
    await api
      .patch(`/ledger/company-bank-account/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllComBankAccList(res.data.company)
        await fetchComBankAccList(res.data.company).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const deleteComBankAcc = async (pk: number, company: number) =>
    await api
      .delete(`/ledger/company-bank-account/${pk}/`)
      .then(async () => {
        await fetchAllComBankAccList(company)
        await fetchComBankAccList(company)
        message('danger', '알림!', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  const comBalanceByAccList = ref<BalanceByAccount[]>([])

  const fetchComBalanceByAccList = async (payload: {
    company: number
    date: string
    is_balance?: '' | 'true'
  }) => {
    const { company, date } = payload
    const is_balance = payload.is_balance ?? ''
    const dateUri = date ? `&is_balance=${is_balance}&date=${date}` : ''
    return await api
      .get(`/balance-by-acc/?company=${company}${dateUri}`)
      .then(res => (comBalanceByAccList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const dateCashBook = ref<BankTransaction[]>([])

  const fetchDateCashBookList = async (payload: { company: number; date: string }) => {
    const { company, date } = payload
    return await api
      .get(`/date-cashbook/?company=${company}&date=${date}`)
      .then(res => (dateCashBook.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const bankTransaction = ref<BankTransaction | null>(null)
  const bankTransactionList = ref<BankTransaction[]>([])
  const bankTransactionCount = ref<number>(0)
  // const childrenCache = ref<Map<number, BankTransaction[]>>(new Map())

  const cashesPages = (itemsPerPage: number) => Math.ceil(bankTransactionCount.value / itemsPerPage)

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
      account: payload.account,
      affiliate: payload.affiliate,
      bank_account: payload.bank_account,
      search: payload.search,
      page: payload.page || 1,
    })

    return await api
      .get('/ledger/company-transaction/', { params })
      .then(res => {
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

  // // 특정 부모의 자식 레코드 조회 (페이지네이션)
  // const fetchChildrenRecords = async (parentPk: number, page: number = 1) => {
  //   try {
  //     const response = await api.get(`/bank-transaction/${parentPk}/children/?page=${page}`)
  //     const children = response.data.results as BankTransaction[]
  //     const count = response.data.count
  //
  //     // 페이지별 캐시 업데이트 (각 페이지를 독립적으로 저장)
  //     childrenCache.value.set(parentPk, children)
  //
  //     return {
  //       results: children,
  //       count,
  //       next: response.data.next,
  //       previous: response.data.previous,
  //     }
  //   } catch (err: any) {
  //     errorHandle(err.response?.data)
  //     throw err
  //   }
  // }
  //
  // // 캐시에서 자식 레코드 가져오기
  // const getCachedChildren = (parentPk: number): BankTransaction[] => {
  //   return childrenCache.value.get(parentPk) || []
  // }
  //
  // // 캐시 무효화
  // const invalidateChildrenCache = (parentPk?: number) => {
  //   if (parentPk !== undefined) {
  //     childrenCache.value.delete(parentPk)
  //   } else {
  //     childrenCache.value.clear()
  //   }
  // }
  //
  // // 캐시된 자식 레코드 업데이트
  // const updateCachedChild = (parentPk: number, updatedChild: BankTransaction) => {
  //   const cachedChildren = childrenCache.value.get(parentPk)
  //   if (cachedChildren) {
  //     const index = cachedChildren.findIndex(child => child.pk === updatedChild.pk)
  //     if (index !== -1) {
  //       // 기존 자식 레코드를 업데이트된 데이터로 교체
  //       cachedChildren[index] = updatedChild
  //       childrenCache.value.set(parentPk, [...cachedChildren])
  //     }
  //   }
  // }
  //
  // // 목록에서 부모 레코드 업데이트 (is_balanced 등 갱신)
  // const updateParentInList = (parentPk: number, updatedParent: BankTransaction) => {
  //   const index = bankTransactionList.value.findIndex(item => item.pk === parentPk)
  //   if (index !== -1) {
  //     bankTransactionList.value[index] = updatedParent
  //   }
  // }

  const createBankTransaction = async (
    payload: BankTransaction & { accData: AccountingEntry | null },
  ) =>
    await api
      .post(`/ledger/company-composite-transaction/`, payload)
      .then(async res => {
        return await fetchBankTransactionList({ company: res.data.company }).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateBankTransaction = async (
    payload: BankTransaction & { accData: AccountingEntry | null } & { filters: DataFilter },
  ) => {
    const { filters, ...formData } = payload
    return await api
      .put(`/ledger/company-composite-transaction/${formData.pk}/`, formData)
      .then(async res => {
        return await fetchBankTransactionList({ company: res.data.company }).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))
  }

  const deleteBankTransaction = async (payload: BankTransaction & { filters: DataFilter }) => {
    const { pk, filters, company } = payload
    return await api
      .delete(`//ledger/company-transaction/${pk}/`)
      .then(() =>
        fetchBankTransactionList({ company, ...filters }).then(() =>
          message('danger', '알림!', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))
  }

  const comLedgerCalc = ref<ComCalculated[]>([])

  const fetchComLedgerCalc = async (com: number) =>
    await api
      .get(`/com-cash-calc/?company=${com}`)
      .then(res => (comLedgerCalc.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createComLedgerCalc = async (payload: ComCalculated) =>
    await api
      .post(`/com-cash-calc/`, payload)
      .then(res => fetchComLedgerCalc(res.data.company).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const patchComLedgerCalc = async (payload: ComCalculated) =>
    await api
      .patch(`/com-cash-calc/${payload.pk}/`, payload)
      .then(res => fetchComLedgerCalc(res.data.company).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const comLastDeal = ref<{ deal_date: string }[]>([])
  const fetchComLastDeal = async (com: number) =>
    await api
      .get(`/com-last-deal/?company=${com}`)
      .then(res => (comLastDeal.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const comCalculated = computed(() => (comLedgerCalc.value.length ? comLedgerCalc.value[0] : null))
  const comLastDealDate = computed(() => (comLastDeal.value.length ? comLastDeal.value[0] : null))

  // ============================================
  // Status 페이지용 Ledger API (신규 추가)
  // ============================================
  const comLedgerBankList = ref<CompanyBank[]>([])
  const comLedgerBalanceByAccList = ref<BalanceByAccount[]>([])
  const dateLedgerTransactions = ref<CompanyBankTransaction[]>([])
  const comLedgerCalculation = ref<ComCalculated[]>([])
  const comLedgerLastDealList = ref<{ deal_date: string }[]>([])

  // Computed - UI 호환성을 위한 어댑터
  const dateLedgerForDisplay = computed<LedgerTransactionForDisplay[]>(() =>
    dateLedgerTransactions.value.map(tx => ({
      pk: tx.pk,
      company: tx.company,
      sort: tx.sort,
      sort_desc: tx.sort_name,
      account_d1: null,
      account_d2: null,
      account_d3: null,
      content: tx.content,
      trader: tx.accounting_entries?.[0]?.trader || '',
      bank_account: tx.bank_account,
      bank_account_desc: tx.bank_account_name,
      income: tx.sort === 1 ? tx.amount : null,
      outlay: tx.sort === 2 ? tx.amount : null,
      deal_date: tx.deal_date,
      note: tx.note,
    })),
  )

  const comLedgerCalculated = computed(() =>
    comLedgerCalculation.value.length ? comLedgerCalculation.value[0] : null,
  )

  const comLedgerLastDealDate = computed(() =>
    comLedgerLastDealList.value.length ? comLedgerLastDealList.value[0] : null,
  )

  const fetchComLedgerBankAccList = async (company: number) =>
    await api
      .get(`/ledger/company-bank-account/?company=${company}&is_hide=false&inactive=false`)
      .then(res => (comLedgerBankList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

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
      .get(`/company-ledger-calculation/?company=${com}`)
      .then(res => (comLedgerCalculation.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createComLedgerCalculation = async (payload: ComCalculated) =>
    await api
      .post(`/company-ledger-calculation/`, payload)
      .then(res => fetchComLedgerCalculation(res.data.company).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const patchComLedgerCalculation = async (payload: ComCalculated) =>
    await api
      .patch(`/company-ledger-calculation/${payload.pk}/`, payload)
      .then(res => fetchComLedgerCalculation(res.data.company).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const fetchComLedgerLastDealDate = async (com: number) =>
    await api
      .get(`/ledger/company-transaction/last_deal/?company=${com}`)
      .then(res => (comLedgerLastDealList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  return {
    bankCodeList,
    fetchBankCodeList,

    affiliateList,
    affiliates,
    fetchAffiliateList,

    comAccountList,
    comAccountFilter,
    comAccounts,
    fetchCompanyAccounts,

    comBankList,
    getComBanks,
    allComBankList,
    fetchComBankAccList,
    fetchAllComBankAccList,
    createComBankAcc,
    updateComBankAcc,
    patchComBankAcc,
    deleteComBankAcc,

    comBalanceByAccList,
    fetchComBalanceByAccList,

    dateCashBook,
    fetchDateCashBookList,

    bankTransaction,
    bankTransactionList,
    bankTransactionCount,
    cashesPages,
    fetchBankTransaction,
    fetchBankTransactionList,
    findBankTransactionPage,
    // fetchChildrenRecords,
    // getCachedChildren,
    // invalidateChildrenCache,
    // updateCachedChild,
    // updateParentInList,
    createBankTransaction,
    updateBankTransaction,
    deleteBankTransaction,

    comLedgerCalc,
    comCalculated,
    fetchComLedgerCalc,
    createComLedgerCalc,
    patchComLedgerCalc,

    comLastDeal,
    comLastDealDate,
    fetchComLastDeal,

    // Status 페이지용 (신규)
    comLedgerBankList,
    comLedgerBalanceByAccList,
    dateLedgerTransactions,
    dateLedgerForDisplay,
    comLedgerCalculation,
    comLedgerLastDealList,
    comLedgerCalculated,
    comLedgerLastDealDate,
    fetchComLedgerBankAccList,
    fetchComLedgerBalanceByAccList,
    fetchDateLedgerTransactionList,
    fetchComLedgerCalculation,
    createComLedgerCalculation,
    patchComLedgerCalculation,
    fetchComLedgerLastDealDate,
  }
})
