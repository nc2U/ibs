import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import { type AccountSort } from '@/store/types/comCash'
import {
  type BalanceByAccount,
  type CashBookFilter,
  type ProBankAcc,
  type ProCalculated,
  type ProjectAccountD2,
  type ProjectAccountD3,
  type ProjectCashBook,
} from '@/store/types/proCash'
import { usePayment } from '@/store/pinia/payment'

export const useProCash = defineStore('proCash', () => {
  // state & getters
  const sortList = ref<AccountSort[]>([])

  const fetchProAccSortList = async () =>
    await api
      .get(`/account-sort/`)
      .then(res => (sortList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const allAccD2List = ref<ProjectAccountD2[]>([])

  const fetchProAllAccD2List = async () =>
    await api
      .get(`/project-account-depth2/`)
      .then(res => (allAccD2List.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const allAccD3List = ref<ProjectAccountD3[]>([])

  const fetchProAllAccD3List = async () =>
    await api
      .get(`/project-account-depth3/`)
      .then(res => (allAccD3List.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const formAccD2List = ref<ProjectAccountD2[]>([])

  const fetchProFormAccD2List = async (d1?: number | null, sort?: number | null) => {
    let queryStr = sort ? `?d1__sorts=${sort}` : `?1=1`
    queryStr = d1 ? `${queryStr}&d1=${d1}` : queryStr

    return await api
      .get(`/project-account-depth2/${queryStr}`)
      .then(res => (formAccD2List.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const formAccD3List = ref<ProjectAccountD3[]>([])

  const fetchProFormAccD3List = async (d2: number | null = null, sort: number | null = null) => {
    const uri = `?sort=${sort || ''}&d2=${d2 || ''}`
    return await api
      .get(`/project-account-depth3/${uri}`)
      .then(res => (formAccD3List.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const proBankAccountList = ref<ProBankAcc[]>([])
  const getProBanks = computed(() =>
    proBankAccountList.value.map(bk => ({
      value: bk.pk,
      label: bk.alias_name,
    })),
  )
  const allProBankAccountList = ref<ProBankAcc[]>([])

  const fetchProBankAccList = async (project: number) =>
    await api
      .get(`/project-bank-account/?project=${project}&is_hide=false&inactive=false`)
      .then(res => (proBankAccountList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchAllProBankAccList = async (project: number) =>
    await api
      .get(`/project-bank-account/?project=${project}`)
      .then(res => (allProBankAccountList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createProBankAcc = async (payload: ProBankAcc) =>
    await api
      .post(`/project-bank-account/`, payload)
      .then(async res => {
        await fetchAllProBankAccList(res.data.project)
        await fetchProBankAccList(res.data.project).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateProBankAcc = async (payload: ProBankAcc) =>
    await api
      .put(`/project-bank-account/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllProBankAccList(res.data.project)
        await fetchProBankAccList(res.data.project).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const patchProBankAcc = async (payload: ProBankAcc) =>
    await api
      .patch(`project-bank-account/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllProBankAccList(res.data.project)
        await fetchProBankAccList(res.data.project).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const deleteProBankAcc = async (pk: number, project: number) =>
    await api
      .delete(`/project-bank-account/${pk}/`)
      .then(async () => {
        await fetchAllProBankAccList(project)
        await fetchProBankAccList(project)
        message('danger', '알림!', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  const balanceByAccList = ref<BalanceByAccount[]>([])

  const fetchBalanceByAccList = async (payload: {
    project: number
    direct?: string
    is_balance?: 'true' | ''
    date?: string
  }) => {
    const { project, date, direct = '0' } = payload
    const is_balance = payload.is_balance ?? ''
    let url = `/pr-balance-by-acc/?project=${project}&bank_account__directpay=${direct}&is_balance=${is_balance}`
    if (date) url += `&date=${date}`
    return await api
      .get(url)
      .then(res => (balanceByAccList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const proDateCashBook = ref<ProjectCashBook[]>([])

  const fetchDateCashBookList = async (payload: { project: number; date: string }) => {
    const { project, date } = payload
    const url = `/pr-date-cashbook/?project=${project}&date=${date}`
    return await api
      .get(url)
      .then(res => (proDateCashBook.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const proCashBookList = ref<ProjectCashBook[]>([])
  const proCashesCount = ref<number>(0)
  const childrenCache = ref<Map<number, ProjectCashBook[]>>(new Map())

  const getUrl = (payload: CashBookFilter) => {
    let url = ''
    if (payload.from_date) url += `&from_deal_date=${payload.from_date}`
    if (payload.to_date) url += `&to_deal_date=${payload.to_date}`
    if (payload.sort) url += `&sort=${payload.sort}`
    if (payload.account_d1) url += `&project_account_d2__d1=${payload.account_d1}`
    if (payload.pro_acc_d2) url += `&project_account_d2=${payload.pro_acc_d2}`
    if (payload.pro_acc_d3) url += `&project_account_d3=${payload.pro_acc_d3}`
    if (payload.is_imprest) url += `&is_imprest=${payload.is_imprest}`
    if (payload.bank_account) url += `&bank_account=${payload.bank_account}`
    if (payload.contract) url += `&contract=${payload.contract}`
    if (payload.search) url += `&search=${payload.search}`
    const page = payload.page ? payload.page : 1
    if (payload.page) url += `&page=${page}`
    return url
  }

  const fetchProjectCashList = async (payload: CashBookFilter) => {
    const { project, is_imprest } = payload
    let url = `/project-cashbook/?project=${project}&is_imprest=${is_imprest}&parents_only=true`
    url += getUrl(payload)

    return await api
      .get(url)
      .then(res => {
        proCashBookList.value = res.data.results
        proCashesCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  // 특정 부모의 자식 레코드 조회 (페이지네이션)
  const fetchChildrenRecords = async (parentPk: number, page: number = 1) => {
    try {
      const response = await api.get(`/project-cashbook/${parentPk}/children/?page=${page}`)
      const children = response.data.results as ProjectCashBook[]
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
  const getCachedChildren = (parentPk: number): ProjectCashBook[] => {
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

  const findProjectCashBookPage = async (highlightId: number, filters: CashBookFilter) => {
    const { project, is_imprest } = filters
    let url = `/project-cashbook/find_page/?highlight_id=${highlightId}&project=${project}&is_imprest=${is_imprest}`
    url += getUrl(filters)

    try {
      const response = await api.get(url)
      return response.data.page
    } catch (err: any) {
      errorHandle(err.response.data)
      return 1
    }
  }

  const proCashPages = (itemsPerPage: number) => Math.ceil(proCashesCount.value / itemsPerPage)

  const paymentStore = usePayment()

  const createPrCashBook = async (
    payload: ProjectCashBook & { sepData: ProjectCashBook | null } & {
      filters: CashBookFilter
    },
  ) => {
    const { filters, ...formData } = payload
    return await api
      .post(`/project-cashbook/`, formData)
      .then(async res => {
        // 캐시 무효화 (부모가 생성되었을 수 있음)
        invalidateChildrenCache()

        await fetchProjectCashList({
          project: res.data.project,
          ...filters,
        })
        await fetchProjectImprestList({
          project: res.data.project,
          ...filters,
        })
        await paymentStore.fetchAllPaymentList({
          project: res.data.project,
          contract: res.data.contract,
          ordering: 'deal_date',
        })
        await paymentStore.fetchPaymentList({
          project: res.data.project,
          ...filters,
        })
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const updatePrCashBook = async (
    payload: ProjectCashBook & { sepData: ProjectCashBook | null } & {
      isPayment?: boolean
    } & {
      filters: CashBookFilter
    },
  ) => {
    const cont = payload.contract
    const { pk, isPayment, filters, ...formData } = payload
    if (formData.rmCont) formData.contract = null
    return await api
      .put(`/project-cashbook/${pk}/`, formData)
      .then(async res => {
        // 캐시 무효화 (해당 부모의 자식이 수정되었을 수 있음)
        if (res.data.separated) {
          invalidateChildrenCache(res.data.separated)
        }
        invalidateChildrenCache(pk || undefined)

        if (isPayment) {
          await paymentStore.fetchAllPaymentList({
            project: res.data.project,
            contract: cont || undefined,
            ordering: 'deal_date',
            ...filters,
          })
          await paymentStore
            .fetchPaymentList({
              project: res.data.project,
              ...filters,
            })
            .then(() => message())
        } else
          await fetchProjectCashList({
            project: res.data.project,
            ...filters,
          }).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))
  }

  const patchPrCashBook = async (
    payload: ProjectCashBook & { isPayment?: boolean } & {
      filters: CashBookFilter
    },
  ) => {
    const cont = payload.contract
    const { pk, isPayment, filters, ...formData } = payload
    if (formData.rmCont) formData.contract = null
    return await api
      .patch(`/project-cashbook/${pk}/`, formData)
      .then(async res => {
        // 캐시 무효화
        if (res.data.separated) {
          invalidateChildrenCache(res.data.separated)
        }
        invalidateChildrenCache(pk || undefined)

        if (isPayment) {
          await paymentStore.fetchAllPaymentList({
            project: res.data.project,
            contract: cont || undefined,
            ordering: 'deal_date',
            ...filters,
          })
          await paymentStore
            .fetchPaymentList({
              project: res.data.project,
              ...filters,
            })
            .then(() => message())
        } else
          await fetchProjectCashList({
            project: res.data.project,
            ...filters,
          }).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))
  }

  const deletePrCashBook = async (
    payload: {
      pk: number
      project: number
      contract?: number | null
    } & {
      filters?: CashBookFilter
    },
  ) => {
    const { pk, project, filters, contract } = payload

    return await api
      .delete(`/project-cashbook/${pk}/`)
      .then(async () => {
        // 캐시 무효화 (전체 캐시 클리어)
        invalidateChildrenCache()

        await fetchProjectCashList({
          project,
          ...filters,
        })
        if (contract) {
          await paymentStore.fetchAllPaymentList({
            project,
            contract,
            ordering: 'deal_date',
          })
          await paymentStore.fetchPaymentList({
            project,
            ...filters,
          })
          message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.')
        }
      })
      .catch(err => errorHandle(err.response.data))
  }

  const proImprestList = ref<ProjectCashBook[]>([])
  const proImprestCount = ref<number>(0)

  const fetchProjectImprestList = async (payload: CashBookFilter) => {
    const { project } = payload
    let url = `/project-imprest/?project=${project}`
    url += getUrl(payload)

    return await api
      .get(url)
      .then(res => {
        proImprestList.value = res.data.results
        proImprestCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const proImprestPages = (itemsPerPage: number) => Math.ceil(proImprestCount.value / itemsPerPage)

  const imprestBAccount = computed(() => allProBankAccountList.value.filter(b => b.is_imprest))

  const getImpBankAccs = computed(() =>
    imprestBAccount.value.map(i => ({ value: i.pk, label: i.alias_name })),
  )

  const updatePrImprestBook = async (
    payload: ProjectCashBook & { sepData: ProjectCashBook | null } & {
      filters: CashBookFilter
    },
  ) => {
    const { pk, filters, ...formData } = payload
    return await api
      .put(`/project-imprest/${pk}/`, formData)
      .then(async res => {
        await fetchProjectImprestList({
          project: res.data.project,
          ...filters,
        })
        await paymentStore.fetchAllPaymentList({
          project: res.data.project,
          contract: res.data.contract,
          ordering: 'deal_date',
        })
        await paymentStore.fetchPaymentList({
          project: res.data.project,
          ...filters,
        })
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const patchPrImprestBook = async (payload: ProjectCashBook & { filters: CashBookFilter }) => {
    const { pk, filters, ...formData } = payload
    return await api
      .patch(`/project-imprest/${pk}/`, formData)
      .then(async res => {
        await fetchProjectImprestList({
          project: res.data.project,
          ...filters,
        })
        await paymentStore.fetchAllPaymentList({
          project: res.data.project,
          contract: res.data.contract,
          ordering: 'deal_date',
        })
        await paymentStore.fetchPaymentList({
          project: res.data.project,
          ...filters,
        })
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const deletePrImprestBook = async (
    payload: { pk: number; project: number; contract?: number | null } & {
      filters?: CashBookFilter
    },
  ) => {
    const { pk, project, filters, contract } = payload

    return await api
      .delete(`/project-imprest/${pk}/`)
      .then(async () => {
        await fetchProjectImprestList({
          project,
          ...filters,
        })
        if (contract) {
          await paymentStore.fetchAllPaymentList({
            project,
            contract,
            ordering: 'deal_date',
          })
          await paymentStore.fetchPaymentList({
            project,
            ...filters,
          })
          message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.')
        }
      })
      .catch(err => errorHandle(err.response.data))
  }

  const proCashCalc = ref<ProCalculated[]>([])

  const fetchProCashCalc = async (com: number) =>
    await api
      .get(`/pro-cash-calc/?company=${com}`)
      .then(res => (proCashCalc.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createProCashCalc = async (payload: ProCalculated) =>
    await api
      .post(`/pro-cash-calc/`, payload)
      .then(res => fetchProCashCalc(res.data.project).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const patchProCashCalc = async (payload: ProCalculated) =>
    await api
      .patch(`/pro-cash-calc/${payload.pk}/`, payload)
      .then(res => fetchProCashCalc(res.data.project).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const proLastDeal = ref<{ deal_date: string }[]>([])

  const fetchProLastDeal = async (proj: number) =>
    await api
      .get(`/pro-last-deal/?project=${proj}`)
      .then(res => (proLastDeal.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const proCalculated = computed(() => (proCashCalc.value.length ? proCashCalc.value[0] : null))
  const proLastDealDate = computed(() => (proLastDeal.value.length ? proLastDeal.value[0] : null))

  return {
    sortList,
    allAccD2List,
    allAccD3List,
    fetchProAccSortList,
    fetchProAllAccD2List,
    fetchProAllAccD3List,

    formAccD2List,
    formAccD3List,
    fetchProFormAccD2List,
    fetchProFormAccD3List,

    proBankAccountList,
    getProBanks,
    allProBankAccountList,
    fetchProBankAccList,
    fetchAllProBankAccList,
    createProBankAcc,
    updateProBankAcc,
    patchProBankAcc,
    deleteProBankAcc,

    balanceByAccList,
    fetchBalanceByAccList,

    proDateCashBook,
    fetchDateCashBookList,

    proCashBookList,
    proCashesCount,
    fetchProjectCashList,
    findProjectCashBookPage,
    proCashPages,
    createPrCashBook,
    updatePrCashBook,
    patchPrCashBook,
    deletePrCashBook,
    fetchChildrenRecords,
    getCachedChildren,
    invalidateChildrenCache,

    proImprestList,
    proImprestCount,
    fetchProjectImprestList,
    proImprestPages,
    updatePrImprestBook,
    patchPrImprestBook,
    deletePrImprestBook,
    imprestBAccount,
    getImpBankAccs,

    proCashCalc,
    proCalculated,
    fetchProCashCalc,
    createProCashCalc,
    patchProCashCalc,

    proLastDeal,
    proLastDealDate,
    fetchProLastDeal,
  }
})
