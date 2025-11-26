import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import {
  type BalanceByAccount,
  type BankCode,
  type CashBook,
  type ComCalculated,
  type CompanyBank,
  type SepItems,
} from '@/store/types/comLedger'

export type DataFilter = {
  page?: number
  company?: number | null
  from_date?: string
  to_date?: string
  sort?: number | null
  account_d1?: number | null
  account_d2?: number | null
  account_d3?: number | null
  project?: number | null
  is_return?: boolean
  bank_account?: number | null
  search?: string
  limit?: number
}

export const useComLedger = defineStore('comLedger', () => {
  // state & getters
  const bankCodeList = ref<BankCode[]>([])

  const fetchBankCodeList = async () =>
    await api
      .get('/ledger/bank-code/')
      .then(res => (bankCodeList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const comBankList = ref<CompanyBank[]>([])
  const getComBanks = computed(() =>
    comBankList.value.map(bk => ({ value: bk.pk, label: bk.alias_name })),
  )
  const allComBankList = ref<CompanyBank[]>([])

  const fetchComBankAccList = async (company: number) =>
    await api
      .get(`/company-bank-account/?company=${company}&is_hide=false&inactive=false`)
      .then(res => (comBankList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchAllComBankAccList = async (company: number) =>
    await api
      .get(`/company-bank-account/?company=${company}`)
      .then(res => (allComBankList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createComBankAcc = async (payload: CompanyBank) =>
    await api
      .post(`/company-bank-account/`, payload)
      .then(async res => {
        await fetchAllComBankAccList(res.data.company)
        await fetchComBankAccList(res.data.company).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateComBankAcc = async (payload: CompanyBank) =>
    await api
      .put(`/company-bank-account/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllComBankAccList(res.data.company)
        await fetchComBankAccList(res.data.company).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const patchComBankAcc = async (payload: CompanyBank) =>
    await api
      .patch(`company-bank-account/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllComBankAccList(res.data.company)
        await fetchComBankAccList(res.data.company).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const deleteComBankAcc = async (pk: number, company: number) =>
    await api
      .delete(`/company-bank-account/${pk}/`)
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

  const dateCashBook = ref<CashBook[]>([])

  const fetchDateCashBookList = async (payload: { company: number; date: string }) => {
    const { company, date } = payload
    return await api
      .get(`/date-cashbook/?company=${company}&date=${date}`)
      .then(res => (dateCashBook.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const cashBookList = ref<CashBook[]>([])
  const cashBookCount = ref<number>(0)
  const childrenCache = ref<Map<number, CashBook[]>>(new Map())

  const cashesPages = (itemsPerPage: number) => Math.ceil(cashBookCount.value / itemsPerPage)

  const fetchCashBookList = async (payload: DataFilter) => {
    const { company } = payload
    let url = `/cashbook/?company=${company}`
    if (payload.from_date) url += `&from_deal_date=${payload.from_date}`
    if (payload.to_date) url += `&to_deal_date=${payload.to_date}`
    if (payload.sort) url += `&sort=${payload.sort}`
    if (payload.account_d1) url += `&account_d1=${payload.account_d1}`
    if (payload.account_d2) url += `&account_d2=${payload.account_d2}`
    if (payload.account_d3) url += `&account_d3=${payload.account_d3}`
    if (payload.project) url += `&project=${payload.project}`
    if (payload.is_return) url += `&is_return=${payload.is_return}`
    if (payload.bank_account) url += `&bank_account=${payload.bank_account}`
    if (payload.search) url += `&search=${payload.search}`
    const page = payload.page ? payload.page : 1
    if (payload.page) url += `&page=${page}`

    return await api
      .get(url)
      .then(res => {
        cashBookList.value = res.data.results
        cashBookCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const findCashBookPage = async (highlightId: number, filters: DataFilter) => {
    const { company } = filters
    let url = `/cashbook/find_page/?highlight_id=${highlightId}&company=${company}`
    if (filters.from_date) url += `&from_deal_date=${filters.from_date}`
    if (filters.to_date) url += `&to_deal_date=${filters.to_date}`
    if (filters.sort) url += `&sort=${filters.sort}`
    if (filters.account_d1) url += `&account_d1=${filters.account_d1}`
    if (filters.account_d2) url += `&account_d2=${filters.account_d2}`
    if (filters.account_d3) url += `&account_d3=${filters.account_d3}`
    if (filters.project) url += `&project=${filters.project}`
    if (filters.is_return) url += `&is_return=${filters.is_return}`
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

  // 특정 부모의 자식 레코드 조회 (페이지네이션)
  const fetchChildrenRecords = async (parentPk: number, page: number = 1) => {
    try {
      const response = await api.get(`/cashbook/${parentPk}/children/?page=${page}`)
      const children = response.data.results as CashBook[]
      const count = response.data.count

      // 페이지별 캐시 업데이트 (각 페이지를 독립적으로 저장)
      childrenCache.value.set(parentPk, children)

      return {
        results: children,
        count,
        next: response.data.next,
        previous: response.data.previous,
      }
    } catch (err: any) {
      errorHandle(err.response?.data)
      throw err
    }
  }

  // 캐시에서 자식 레코드 가져오기
  const getCachedChildren = (parentPk: number): CashBook[] => {
    return childrenCache.value.get(parentPk) || []
  }

  // 캐시 무효화
  const invalidateChildrenCache = (parentPk?: number) => {
    if (parentPk !== undefined) {
      childrenCache.value.delete(parentPk)
    } else {
      childrenCache.value.clear()
    }
  }

  // 캐시된 자식 레코드 업데이트
  const updateCachedChild = (parentPk: number, updatedChild: CashBook) => {
    const cachedChildren = childrenCache.value.get(parentPk)
    if (cachedChildren) {
      const index = cachedChildren.findIndex(child => child.pk === updatedChild.pk)
      if (index !== -1) {
        // 기존 자식 레코드를 업데이트된 데이터로 교체
        cachedChildren[index] = updatedChild
        childrenCache.value.set(parentPk, [...cachedChildren])
      }
    }
  }

  // 목록에서 부모 레코드 업데이트 (is_balanced 등 갱신)
  const updateParentInList = (parentPk: number, updatedParent: CashBook) => {
    const index = cashBookList.value.findIndex(item => item.pk === parentPk)
    if (index !== -1) {
      cashBookList.value[index] = updatedParent
    }
  }

  const createCashBook = async (payload: CashBook & { sepData: SepItems | null }) =>
    await api
      .post(`/cashbook/`, payload)
      .then(async res => {
        return await fetchCashBookList({ company: res.data.company }).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateCashBook = async (
    payload: CashBook & { sepData: SepItems | null } & { filters: DataFilter },
  ) => {
    const { filters, ...formData } = payload
    return await api
      .put(`/cashbook/${formData.pk}/`, formData)
      .then(async res => {
        // 자식 레코드를 수정한 경우
        if (res.data.separated) {
          const parentPk = res.data.separated
          // 1. 캐시된 자식 레코드 업데이트
          updateCachedChild(parentPk, res.data)

          // 2. 부모 레코드도 다시 fetch해서 is_balanced 등 갱신
          try {
            const parentRes = await api.get(`/cashbook/${parentPk}/`)
            updateParentInList(parentPk, parentRes.data)
          } catch (err) {
            console.error('부모 레코드 갱신 실패:', err)
          }
        } else {
          // 부모 레코드를 수정한 경우 - 목록에서 업데이트
          updateParentInList(formData.pk || 0, res.data)
          // 자식 캐시 무효화 (다음 열 때 다시 로드)
          invalidateChildrenCache(formData.pk || undefined)
        }

        return message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const deleteCashBook = async (payload: CashBook & { filters: DataFilter }) => {
    const { pk, filters, company } = payload
    return await api
      .delete(`/cashbook/${pk}/`)
      .then(() =>
        fetchCashBookList({ company, ...filters }).then(() =>
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

  return {
    bankCodeList,
    fetchBankCodeList,

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

    cashBookList,
    cashBookCount,
    cashesPages,
    fetchCashBookList,
    findCashBookPage,
    fetchChildrenRecords,
    getCachedChildren,
    invalidateChildrenCache,
    updateCachedChild,
    updateParentInList,
    createCashBook,
    updateCashBook,
    deleteCashBook,

    comLedgerCalc,
    comCalculated,
    fetchComLedgerCalc,
    createComLedgerCalc,
    patchComLedgerCalc,

    comLastDeal,
    comLastDealDate,
    fetchComLastDeal,
  }
})
