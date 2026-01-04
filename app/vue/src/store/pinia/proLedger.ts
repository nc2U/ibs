import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { cleanupParams, errorHandle, message } from '@/utils/helper'
import type {
  ProjectBank,
  ProjectAccount,
  DataFilter,
  ProAccountFilter,
  ProBankTrans,
  ProAccountingEntry,
  BalanceByAccount,
  ProCalculated,
  LedgerTransactionForDisplay,
} from '@/store/types/proLedger.ts'

export const useProLedger = defineStore('proLedger', () => {
  // state & getters
  const proBankList = ref<ProjectBank[]>([])
  const getProBanks = computed(() =>
    proBankList.value.map(bk => ({ value: bk.pk, label: bk.alias_name })),
  )
  const allProBankList = ref<ProjectBank[]>([])

  const fetchProBankAccList = async (project: number) =>
    await api
      .get(`/ledger/project-bank-account/?project=${project}&is_hide=false&inactive=false`)
      .then(res => (proBankList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchAllProBankAccList = async (project: number) =>
    await api
      .get(`/ledger/project-bank-account/?project=${project}`)
      .then(res => (allProBankList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createProBankAcc = async (payload: ProjectBank) =>
    await api
      .post(`/ledger/project-bank-account/`, payload)
      .then(async res => {
        await fetchAllProBankAccList(res.data.project)
        await fetchProBankAccList(res.data.project).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateProBankAcc = async (payload: ProjectBank) =>
    await api
      .put(`/ledger/project-bank-account/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllProBankAccList(res.data.project)
        await fetchProBankAccList(res.data.project).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const patchProBankAcc = async (payload: ProjectBank) =>
    await api
      .patch(`/ledger/project-bank-account/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllProBankAccList(res.data.project)
        await fetchProBankAccList(res.data.project).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  // state & getters
  const proAccountFilter = ref<ProAccountFilter>({})
  const proAccountList = ref<ProjectAccount[]>([])
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
        requires_contract: acc.requires_contract,
        is_related_contractor: acc.is_related_contractor,
      })),
  )

  const fetchProjectAccounts = async (payload: ProAccountFilter = {}) => {
    proAccountFilter.value = payload
    const params = cleanupParams({
      category: payload.category,
      direction: payload.direction,
      parent: payload.parent,
      is_category_only: payload.is_category_only,
      is_payment: payload.is_payment,
      requires_contract: payload.requires_contract,
      is_related_contractor: payload.is_related_contractor,
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

  // state & getters - proBankTrans
  const proBankTransFilter = ref<DataFilter>({})
  const proBankTrans = ref<ProBankTrans | null>(null)
  const proBankTransList = ref<ProBankTrans[]>([])
  const proBankTransCount = ref<number>(0)

  const proTransPages = (itemsPerPage: number) => Math.ceil(proBankTransCount.value / itemsPerPage)

  const fetchProBankTrans = async (pk: number) =>
    await api
      .get(`/ledger/project-transaction/${pk}/`)
      .then(res => {
        proBankTrans.value = res.data
      })
      .catch(err => errorHandle(err.response.data))

  const fetchProBankTransList = async (payload: DataFilter = {}) => {
    const params = cleanupParams({
      project: payload.project,
      from_date: payload.from_date,
      to_date: payload.to_date,
      sort: payload.sort,
      bank_account: payload.bank_account,
      is_imprest: payload.is_imprest,
      account: payload.account,
      account_category: payload.account_category,
      account_name: payload.account_name,
      contract: payload.contract,
      search: payload.search,
      page: payload.page || 1,
    })

    return await api
      .get('/ledger/project-transaction/', { params })
      .then(res => {
        proBankTransFilter.value = payload
        proBankTransList.value = res.data.results
        proBankTransCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const findProBankTransPage = async (highlightId: number, filters: DataFilter) => {
    const params = cleanupParams({
      highlight_id: highlightId,
      project: filters.project,
      from_date: filters.from_date,
      to_date: filters.to_date,
      sort: filters.sort,
      account: filters.account,
      bank_account: filters.bank_account,
      search: filters.search,
    })

    try {
      const response = await api.get('/ledger/project-transaction/find_page/', { params })
      return response.data.page
    } catch (err: any) {
      errorHandle(err.response.data)
      return 1
    }
  }

  const createProBankTrans = async (
    payload: ProBankTrans & { accData: ProAccountingEntry | null },
  ) =>
    await api
      .post(`/ledger/project-composite-transaction/`, payload)
      .then(async res => {
        return await fetchProBankTransList(proBankTransFilter.value).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateProBankTrans = async (
    payload: ProBankTrans & { accData: ProAccountingEntry | null },
  ) => {
    const { pk, ...formData } = payload
    return await api
      .put(`/ledger/project-composite-transaction/${pk}/`, formData)
      .then(async res => {
        return await fetchProBankTransList(proBankTransFilter.value).then(() => message())
      })
      .catch(err => errorHandle(err.response?.data))
  }

  const patchProBankTrans = async (
    payload: Partial<ProBankTrans & { accData: ProAccountingEntry | null }>,
  ) => {
    const { pk, ...formData } = payload
    return await api
      .patch(`/ledger/project-composite-transaction/${pk}/`, formData)
      .then(async res => {
        return await fetchProBankTransList(proBankTransFilter.value)
      })
      .catch(err => errorHandle(err.response?.data))
  }

  const deleteProBankTrans = async (pk: number) => {
    return await api
      .delete(`/ledger/project-composite-transaction/${pk}/`)
      .then(async () => {
        return await fetchProBankTransList(proBankTransFilter.value).then(() =>
          message('warning', '알림!', '본사 거래 데이터가 삭제되었습니다.'),
        )
      })
      .catch(err => errorHandle(err.response?.data))
  }

  // ============================================
  // Status 페이지용 Ledger API (신규 추가)
  // ============================================
  const proLedgerBalanceByAccList = ref<BalanceByAccount[]>([])
  const dateLedgerTransactions = ref<ProBankTrans[]>([])
  const dateLedgerForDisplay = computed<LedgerTransactionForDisplay[]>(() =>
    dateLedgerTransactions.value.map(tx => ({
      pk: tx.pk!,
      project: tx.project,
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

  const proLedgerCalculation = ref<ProCalculated[]>([])
  const proLedgerCalculated = computed(() =>
    proLedgerCalculation.value.length ? proLedgerCalculation.value[0] : null,
  )

  const proLedgerLastDealList = ref<{ deal_date: string }[]>([])
  const proLedgerLastDealDate = computed(() =>
    proLedgerLastDealList.value.length ? proLedgerLastDealList.value[0] : null,
  )

  const fetchProLedgerBalanceByAccList = async (payload: {
    project: number
    direct?: string
    date?: string
    is_balance?: '' | 'true'
  }) => {
    const { project, date, is_balance = '' } = payload
    return await api
      .get(
        `/ledger/project-transaction/balance_by_account/?project=${project}&date=${date}&is_balance=${is_balance}`,
      )
      .then(res => (proLedgerBalanceByAccList.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchDateLedgerTransactionList = async (payload: { project: number; date: string }) => {
    const { project, date } = payload
    return await api
      .get(`/ledger/project-transaction/daily_transactions/?project=${project}&date=${date}`)
      .then(res => (dateLedgerTransactions.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchProLedgerCalculation = async (pro: number) =>
    await api
      .get(`/ledger/project-calculation/?project=${pro}`)
      .then(res => (proLedgerCalculation.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createProLedgerCalculation = async (payload: ProCalculated) =>
    await api
      .post(`/ledger/project-calculation/`, payload)
      .then(res => fetchProLedgerCalculation(res.data.project).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const patchProLedgerCalculation = async (payload: ProCalculated) =>
    await api
      .patch(`/ledger/project-calculation/${payload.pk}/`, payload)
      .then(res => fetchProLedgerCalculation(res.data.project).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const fetchProLedgerLastDealDate = async (pro: number) =>
    await api
      .get(`/ledger/project-last-deal-date/?project=${pro}`)
      .then(res => (proLedgerLastDealList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  // --- Picker 공유 상태 및 로직 ---
  const sharedEditingState = ref<{ type: 'tran' | 'entry'; pk: number; field: string } | null>(null)
  const sharedPickerPosition = ref<{ top: number; left: number; width: number } | null>(null)

  const clearSharedPickerState = () => {
    sharedEditingState.value = null
    sharedPickerPosition.value = null
  }

  return {
    proBankList,
    getProBanks,
    allProBankList,
    fetchProBankAccList,
    fetchAllProBankAccList,
    createProBankAcc,
    updateProBankAcc,
    patchProBankAcc,

    proAccountList,
    proAccountFilter,
    proAccounts,

    fetchProjectAccounts,

    proBankTrans,
    proBankTransFilter,
    proBankTransList,
    proBankTransCount,
    proTransPages,
    fetchProBankTrans,
    fetchProBankTransList,
    findProBankTransPage,
    createProBankTrans,
    updateProBankTrans,
    patchProBankTrans,
    deleteProBankTrans,

    // Status 페이지용 (신규)
    proLedgerBalanceByAccList,
    dateLedgerTransactions,
    dateLedgerForDisplay,

    proLedgerCalculation,
    proLedgerCalculated,

    proLedgerLastDealList,
    proLedgerLastDealDate,

    fetchProLedgerBalanceByAccList,
    fetchDateLedgerTransactionList,

    fetchProLedgerCalculation,
    createProLedgerCalculation,
    patchProLedgerCalculation,
    fetchProLedgerLastDealDate,

    // Shared Picker State
    sharedEditingState,
    sharedPickerPosition,
    clearSharedPickerState,
  }
})
