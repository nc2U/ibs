import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import { type CashBookFilter } from '@/store/types/proCash'
import type {
  AllPayment,
  CompositeTransactionPayload,
  CompositeTransactionResponse,
  ContPayFilter,
  DownPay,
  DownPayFilter,
  OriginPayment,
  OverallSummary,
  PaymentPerInstallment,
  PaymentPerInstallmentFilter,
  PaymentPerInstallmentPayload,
  PaymentStatusByUnitType,
  PaymentSummaryComponent,
  PayOrder,
  Price,
  PriceFilter,
} from '@/store/types/payment'

export const usePayment = defineStore('payment', () => {
  // state & getters
  const priceList = ref<Price[]>([])

  // actions
  const fetchPriceList = async (payload: PriceFilter) => {
    const project = payload.project || ''
    const order_group = payload.order_group || ''
    const unit_type = payload.unit_type || ''

    return await api
      .get(`/price/?project=${project}&order_group=${order_group}&unit_type=${unit_type}`)
      .then(res => (priceList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const createPrice = (payload: Price) =>
    api
      .post(`/price/`, payload)
      .then(() => fetchPriceList(payload).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const updatePrice = (payload: Price) =>
    api
      .put(`/price/${payload.pk}/`, payload)
      .then(() => fetchPriceList(payload).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const deletePrice = (payload: PriceFilter & { pk: number }) =>
    api
      .delete(`/price/${payload.pk}/`)
      .then(() =>
        fetchPriceList(payload).then(() =>
          message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  // state & getters
  const payOrder = ref<PayOrder | null>(null)
  const payOrderList = ref<PayOrder[]>([])

  // actions
  const fetchPayOrder = (pk: number) =>
    api
      .get(`/pay-order/${pk}/`)
      .then(res => (payOrder.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchPayOrderList = (project: number, pay_sort__in?: string) =>
    api
      .get(`/pay-order/?project=${project}&pay_sort__in=${pay_sort__in ?? ''}`)
      .then(res => (payOrderList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createPayOrder = (payload: PayOrder) =>
    api
      .post(`/pay-order/`, payload)
      .then(res => fetchPayOrderList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const patchPayOrder = (payload: PayOrder) =>
    api
      .patch(`/pay-order/${payload.pk}/`, payload)
      .then(res => fetchPayOrderList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const updatePayOrder = (payload: PayOrder) =>
    api
      .put(`/pay-order/${payload.pk}/`, payload)
      .then(res => fetchPayOrderList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const deletePayOrder = (pk: number, project: number) =>
    api
      .delete(`/pay-order/${pk}/`)
      .then(() =>
        fetchPayOrderList(project).then(() =>
          message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  // PaymentPerInstallment state & getters
  const paymentPerInstallmentList = ref<PaymentPerInstallment[]>([])

  // PaymentPerInstallment actions
  const fetchPaymentPerInstallmentList = async (payload: PaymentPerInstallmentFilter) => {
    let url = '/payment-installment/?'
    const params = new URLSearchParams()

    if (payload.sales_price) params.append('sales_price', payload.sales_price.toString())
    if (payload.sales_price__project)
      params.append('sales_price__project', payload.sales_price__project.toString())
    if (payload.sales_price__order_group)
      params.append('sales_price__order_group', payload.sales_price__order_group.toString())
    if (payload.sales_price__unit_type)
      params.append('sales_price__unit_type', payload.sales_price__unit_type.toString())
    if (payload.pay_order) params.append('pay_order', payload.pay_order.toString())

    url += params.toString()

    return await api
      .get(url)
      .then(res => (paymentPerInstallmentList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const createPaymentPerInstallment = (payload: PaymentPerInstallmentPayload) =>
    api
      .post('/payment-installment/', payload)
      .then(() =>
        fetchPaymentPerInstallmentList({ sales_price: payload.sales_price }).then(() => message()),
      )
      .catch(err => errorHandle(err.response.data))

  const updatePaymentPerInstallment = (payload: PaymentPerInstallmentPayload) =>
    api
      .put(`/payment-installment/${payload.pk}/`, payload)
      .then(() =>
        fetchPaymentPerInstallmentList({ sales_price: payload.sales_price }).then(() => message()),
      )
      .catch(err => errorHandle(err.response.data))

  const deletePaymentPerInstallment = (pk: number, salesPriceId: number) =>
    api
      .delete(`/payment-installment/${pk}/`)
      .then(() =>
        fetchPaymentPerInstallmentList({ sales_price: salesPriceId }).then(() =>
          message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  // 컴포넌트용 PaymentPerInstallment 데이터 조회 (전역 상태 업데이트 없음)
  const getPaymentPerInstallmentData = async (
    payload: PaymentPerInstallmentFilter,
  ): Promise<PaymentPerInstallment[]> => {
    let url = '/payment-installment/?'
    const params = new URLSearchParams()

    if (payload.sales_price) params.append('sales_price', payload.sales_price.toString())
    if (payload.sales_price__project)
      params.append('sales_price__project', payload.sales_price__project.toString())
    if (payload.sales_price__order_group)
      params.append('sales_price__order_group', payload.sales_price__order_group.toString())
    if (payload.sales_price__unit_type)
      params.append('sales_price__unit_type', payload.sales_price__unit_type.toString())
    if (payload.pay_order) params.append('pay_order', payload.pay_order.toString())

    url += params.toString()

    try {
      const response = await api.get(url)
      return response.data.results || []
    } catch (err: any) {
      errorHandle(err.response.data)
      return []
    }
  }

  // state & getters
  const downPayList = ref<DownPay[]>([])

  // actions
  const fetchDownPayList = async (payload: DownPayFilter) => {
    let url = `/down-payment/?project=${payload.project}`
    if (payload.order_group) url += `&order_group=${payload.order_group}`
    if (payload.unit_type) url += `&unit_type=${payload.unit_type}`
    return await api
      .get(url)
      .then(res => (downPayList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const createDownPay = (payload: DownPay) =>
    api
      .post(`/down-payment/`, payload)
      .then(res => fetchDownPayList({ project: res.data.project }).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const updateDownPay = (payload: DownPay) =>
    api
      .put(`/down-payment/${payload.pk}/`, payload)
      .then(res => fetchDownPayList({ project: res.data.project }).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const deleteDownPay = (pk: number, project: number) =>
    api
      .delete(`/down-payment/${pk}/`)
      .then(() =>
        fetchDownPayList({ project }).then(() =>
          message('danger', '알림!', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  /////////////////////////////// old payment ///////////////////////////////
  // state & getters
  const paymentList = ref<AllPayment[]>([])
  const AllPaymentList = ref<AllPayment[]>([])
  const getPayments = computed(() =>
    paymentList.value
      ? paymentList.value.map((p: AllPayment) => ({
          pk: p.pk,
          deal_date: p.deal_date,
          contract: p.contract,
          order_group: p.contract ? p.contract.order_group.name : '-',
          type_color: p.contract ? p.contract.unit_type.color : '-',
          type_name: p.contract ? p.contract.unit_type.name : '-',
          serial_number: p.contract ? p.contract.serial_number : '-',
          contractor: p.contract ? p.contract.contractor : '-',
          income: p.income,
          installment_order: p.installment_order ? p.installment_order.__str__ : '-',
          bank_account: p.bank_account.alias_name,
          trader: p.trader,
          note: p.note,
        }))
      : [],
  )
  const paymentsCount = ref<number>(0)

  // actions
  const fetchPaymentList = async (payload: CashBookFilter) => {
    const { project } = payload
    let url = `/payment/?project=${project}`
    if (payload.from_date) url += `&from_deal_date=${payload.from_date}`
    if (payload.to_date) url += `&to_deal_date=${payload.to_date}`
    if (payload.order_group) url += `&contract__order_group=${payload.order_group}`
    if (payload.unit_type) url += `&contract__unit_type=${payload.unit_type}`
    if (payload.pay_order) url += `&installment_order=${payload.pay_order}`
    if (payload.pay_account) url += `&bank_account=${payload.pay_account}`
    if (payload.contract) url += `&contract=${payload.contract}`
    if (payload.no_contract) url += `&no_contract=true`
    if (payload.no_install) url += `&no_install=true&no_contract=false`
    if (payload.ordering) url += `&ordering=${payload.ordering}`
    if (payload.search) url += `&search=${payload.search}`
    const page = payload.page ? payload.page : 1
    if (payload.page) url += `&page=${page}`
    return await api
      .get(url)
      .then(res => {
        paymentList.value = res.data.results
        paymentsCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllPaymentList = async (payload: CashBookFilter) => {
    const { project } = payload
    let url = `/all-payment/?project=${project}`
    if (payload.contract) url += `&contract=${payload.contract}`
    if (payload.ordering) url += `&ordering=${payload.ordering}`
    return await api
      .get(url)
      .then(res => (AllPaymentList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const paymentPages = (itemsPerPage: number) => Math.ceil(paymentsCount.value / itemsPerPage)

  // state & getters - PaymentSummary Component
  const paymentSummaryList = ref<PaymentSummaryComponent[]>([])

  // actions
  const fetchPaymentSummaryList = async (project: number, date = '') => {
    let url = `/payment-summary/?project=${project}`
    if (date) url += `&date=${date}`
    return await api
      .get(url)
      .then(res => (paymentSummaryList.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  // state & getters
  const overallSummary = ref<OverallSummary | null>(null)

  // actions
  const fetchOverallSummary = async (project: number, date?: string) => {
    let url = `/overall-summary/?project=${project}`
    if (date) url += `&date=${date}`
    return await api
      .get(url)
      .then(res => (overallSummary.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  // state & getters
  const paymentStatusByUnitType = ref<PaymentStatusByUnitType[]>([])

  // actions
  const fetchPaymentStatusByUnitType = async (project: number, date?: string) => {
    let url = `/payment-status-by-unit-type/?project=${project}`
    if (date) url += `&date=${date}`
    return await api
      .get(url)
      .then(res => (paymentStatusByUnitType.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  /////////////////////////////// old payment ///////////////////////////////

  /////////////////////////////// new payment ///////////////////////////////
  // state & getters
  const ledgerPaymentList = ref<OriginPayment[]>([])
  const ledgerAllPaymentList = ref<OriginPayment[]>([])
  const legerGetPayments = computed(() =>
    ledgerPaymentList.value
      ? ledgerPaymentList.value.map((p: OriginPayment) => ({
          pk: p.pk,
          trans_id: p.bank_transaction_id,
          deal_date: p.deal_date,
          contract: p.contract,
          order_group: p.contract ? p.contract.order_group.name : '-',
          type_color: p.contract ? p.contract.unit_type.color : '-',
          type_name: p.contract ? p.contract.unit_type.name : '-',
          serial_number: p.contract ? p.contract.serial_number : '-',
          contractor: p.contract ? p.contract.contractor : '-',
          amount: p.amount,
          installment_order: p.installment_order ? p.installment_order.__str__ : '-',
          bank_account: p.bank_account.alias_name,
          trader: p.trader,
          note: p.note,
        }))
      : [],
  )
  const ledgerPaymentsCount = ref<number>(0)

  // action
  const ledgerPaymentPages = (itemsPerPage: number) =>
    Math.ceil(ledgerPaymentsCount.value / itemsPerPage)

  const fetchLedgerPaymentList = async (payload: ContPayFilter) => {
    const { project } = payload
    let url = `/ledger/payment/?is_payment_mismatch=false&project=${project}`
    if (payload.from_date) url += `&from_deal_date=${payload.from_date}`
    if (payload.to_date) url += `&to_deal_date=${payload.to_date}`
    if (payload.order_group) url += `&contract__order_group=${payload.order_group}`
    if (payload.unit_type) url += `&contract__unit_type=${payload.unit_type}`
    if (payload.pay_order) url += `&installment_order=${payload.pay_order}`
    if (payload.pay_account) url += `&bank_account=${payload.pay_account}`
    if (payload.contract) url += `&contract=${payload.contract}`
    if (payload.no_contract) url += `&no_contract=true`
    if (payload.no_install) url += `&no_install=true&no_contract=false`
    if (payload.ordering) url += `&ordering=${payload.ordering}`
    if (payload.search) url += `&search=${payload.search}`
    const page = payload.page ? payload.page : 1
    if (payload.page) url += `&page=${page}`
    return await api
      .get(url)
      .then(res => {
        ledgerPaymentList.value = res.data.results
        ledgerPaymentsCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchLedgerAllPaymentList = async (payload: ContPayFilter) => {
    const { project } = payload
    let url = `/ledger/all-payment/?project=${project}`
    if (payload.contract) url += `&contract=${payload.contract}`
    if (payload.ordering) url += `&ordering=${payload.ordering}`
    return await api
      .get(url)
      .then(res => (ledgerAllPaymentList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  // state & getters - PaymentSummary Component
  const ledgerPaymentSummaryList = ref<PaymentSummaryComponent[]>([])

  // actions
  const fetchLedgerPaymentSummaryList = async (project: number, date = '') => {
    let url = `/ledger/payment-summary/?project=${project}`
    if (date) url += `&date=${date}`
    return await api
      .get(url)
      .then(res => (ledgerPaymentSummaryList.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  // state & getters
  const ledgerOverallSummary = ref<OverallSummary | null>(null)

  // actions
  const fetchLedgerOverallSummary = async (project: number, date?: string) => {
    let url = `/ledger/overall-summary/?project=${project}`
    if (date) url += `&date=${date}`
    return await api
      .get(url)
      .then(res => (ledgerOverallSummary.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  // state & getters
  const ledgerPaymentStatusByUnitType = ref<PaymentStatusByUnitType[]>([])

  // actions
  const fetchLedgerPaymentStatusByUnitType = async (project: number, date?: string) => {
    let url = `/ledger/payment-status-by-unit-type/?project=${project}`
    if (date) url += `&date=${date}`
    return await api
      .get(url)
      .then(res => (ledgerPaymentStatusByUnitType.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  // ============================================
  // ContractPayment CRUD (Ledger 기반)
  // ============================================

  /**
   * 계약 납부 생성 (복합 거래)
   *
   * 은행 거래 + 회계 분개 + 계약 결제를 한 번에 생성합니다.
   * ProjectAccountingEntry.save() → trigger_sync_contract_payment() → ContractPayment 자동 생성
   *
   * @param payload - 복합 거래 데이터
   * @returns Promise<CompositeTransactionResponse>
   *
   * @example
   * // 단일 계약 납부 등록
   * await createContractPayment({
   *   project: 1,
   *   bank_account: 10,
   *   deal_date: '2025-01-15',
   *   amount: 50000000,
   *   sort: 1, // 입금
   *   content: '계약금 입금',
   *   note: '',
   *   accounting_entries: [
   *     {
   *       account: 111, // 분담금 계정
   *       amount: 50000000,
   *       trader: '홍길동',
   *       contract: 123,
   *       installment_order: 1, // 계약금
   *     }
   *   ]
   * })
   *
   * @example
   * // 분할 납부 등록 (한 입금에 여러 회차)
   * await createContractPayment({
   *   project: 1,
   *   bank_account: 10,
   *   deal_date: '2025-01-15',
   *   amount: 80000000,
   *   sort: 1,
   *   content: '중도금 + 잔금 입금',
   *   accounting_entries: [
   *     {
   *       account: 111,
   *       amount: 50000000,
   *       contract: 123,
   *       installment_order: 2, // 중도금
   *     },
   *     {
   *       account: 111,
   *       amount: 30000000,
   *       contract: 123,
   *       installment_order: 3, // 잔금
   *     }
   *   ]
   * })
   */

  const createContractPayment = async (
    payload: CompositeTransactionPayload,
  ): Promise<CompositeTransactionResponse> => {
    try {
      const response = await api.post('/ledger/project-composite-transaction/', payload)
      message('success', '', '계약 납부가 등록되었습니다.')
      return response.data
    } catch (err: any) {
      errorHandle(err.response?.data)
      throw err
    }
  }

  /**
   * 계약 납부 수정 (복합 거래 - 전체 교체)
   *
   * 은행 거래 + 회계 분개 + 계약 결제를 한 번에 수정합니다.
   * ProjectAccountingEntry 수정 → trigger_sync_contract_payment() → ContractPayment 자동 업데이트
   *
   * ⚠️ PUT 요청: 모든 필드 필수, accounting_entries에 없는 기존 분개는 삭제됨
   *
   * @param bankTransactionId - 수정할 은행 거래 ID (ProjectBankTransaction.pk)
   * @param payload - 수정할 복합 거래 데이터 (전체 필드 필수)
   * @returns Promise<CompositeTransactionResponse>
   *
   * @example
   * // 납부 금액 수정
   * await updateContractPayment(456, {
   *   project: 1,
   *   bank_account: 10,
   *   deal_date: '2025-01-15',
   *   amount: 60000000, // 수정된 금액
   *   sort: 1,
   *   content: '계약금 입금 (수정)',
   *   accounting_entries: [
   *     {
   *       pk: 789, // 기존 분개 ID
   *       account: 111,
   *       amount: 60000000, // 수정된 금액
   *       contract: 123,
   *       installment_order: 1,
   *     }
   *   ]
   * })
   */
  const updateContractPayment = async (
    bankTransactionId: number,
    payload: CompositeTransactionPayload,
  ): Promise<CompositeTransactionResponse> => {
    try {
      const response = await api.put(
        `/ledger/project-composite-transaction/${bankTransactionId}/`,
        payload,
      )
      message('success', '', '계약 납부가 수정되었습니다.')
      return response.data
    } catch (err: any) {
      errorHandle(err.response?.data)
      throw err
    }
  }

  /**
   * 계약 납부 부분 수정 (PATCH - installment_order 전용)
   *
   * ContractPayment의 installment_order만 수정하거나 일부 필드만 수정합니다.
   * PATCH 요청 시에만 installment_order가 ContractPayment에 직접 업데이트됩니다.
   *
   * ⚠️ PATCH 요청: 필수 필드 없음, accounting_entries에 없는 기존 분개는 유지됨
   *
   * @param bankTransactionId - 수정할 은행 거래 ID (ProjectBankTransaction.pk)
   * @param payload - 수정할 필드만 포함 (Partial)
   * @returns Promise<CompositeTransactionResponse>
   *
   * @example
   * // 회차만 수정 (가장 일반적인 사용 케이스)
   * await patchContractPayment(456, {
   *   accounting_entries: [
   *     {
   *       pk: 789,
   *       installment_order: 2  // 1회차 → 2회차 변경
   *     }
   *   ]
   * })
   *
   * @example
   * // 여러 분개의 회차 동시 수정
   * await patchContractPayment(456, {
   *   accounting_entries: [
   *     { pk: 789, installment_order: 2 },
   *     { pk: 790, installment_order: 3 }
   *   ]
   * })
   *
   * @example
   * // 은행 거래 내용만 수정 (회차는 그대로)
   * await patchContractPayment(456, {
   *   content: '중도금 입금 (수정)',
   *   note: '비고 추가'
   * })
   */
  const patchContractPayment = async (
    bankTransactionId: number,
    payload: Partial<CompositeTransactionPayload>,
  ): Promise<CompositeTransactionResponse> => {
    try {
      const response = await api.patch(
        `/ledger/project-composite-transaction/${bankTransactionId}/`,
        payload,
      )
      message('success', '', '계약 납부가 수정되었습니다.')
      return response.data
    } catch (err: any) {
      errorHandle(err.response?.data)
      throw err
    }
  }

  /**
   * 계약 납부 삭제 (은행 거래 삭제)
   *
   * 은행 거래를 삭제하면 CASCADE로 회계 분개와 계약 결제도 자동 삭제됩니다.
   * ProjectBankTransaction 삭제 → AccountingEntry 삭제 → ContractPayment 삭제
   *
   * @param bankTransactionId - 삭제할 은행 거래 ID (ProjectBankTransaction.pk)
   * @returns Promise<void>
   *
   * @example
   * await deleteContractPayment(456)
   */
  const deleteContractPayment = async (bankTransactionId: number): Promise<void> => {
    try {
      await api.delete(`/ledger/project-bank-transaction/${bankTransactionId}/`)
      message('warning', '', '계약 납부가 삭제되었습니다.')
    } catch (err: any) {
      errorHandle(err.response?.data)
      throw err
    }
  }

  /**
   * 은행 거래 상세 조회 (회계 분개 포함)
   *
   * 특정 은행 거래의 상세 정보와 연결된 회계 분개 목록을 조회합니다.
   *
   * @param bankTransactionId - 조회할 은행 거래 ID
   * @returns Promise<any>
   *
   * @example
   * const detail = await fetchBankTransactionDetail(456)
   * console.log(detail.bank_transaction) // 은행 거래 정보
   * console.log(detail.accounting_entries) // 회계 분개 배열
   */
  const fetchBankTransactionDetail = async (bankTransactionId: number): Promise<any> => {
    try {
      const response = await api.get(`/ledger/project-bank-transaction/${bankTransactionId}/`)
      return response.data
    } catch (err: any) {
      errorHandle(err.response?.data)
      throw err
    }
  }

  /**
   * 회계 분개 목록 조회 (특정 은행 거래의 자식 분개)
   *
   * 특정 은행 거래(UUID)에 연결된 모든 회계 분개를 조회합니다.
   * 분할 납부 시 여러 회차의 분개 내역을 확인할 때 유용합니다.
   *
   * @param transactionId - 거래 UUID (ProjectBankTransaction.transaction_id)
   * @returns Promise<any[]>
   *
   * @example
   * // UUID로 회계 분개 조회
   * const entries = await fetchAccountingEntriesByTransactionId('uuid-string-here')
   * console.log(entries) // [{ pk: 789, amount: 50000000, ... }, ...]
   */
  const fetchAccountingEntriesByTransactionId = async (transactionId: string): Promise<any[]> => {
    try {
      const response = await api.get(
        `/ledger/project-accounting-entry/?transaction_id=${transactionId}`,
      )
      return response.data.results || response.data
    } catch (err: any) {
      errorHandle(err.response?.data)
      throw err
    }
  }

  /////////////////////////////// new payment ///////////////////////////////

  return {
    priceList,
    fetchPriceList,
    createPrice,
    updatePrice,
    deletePrice,

    payOrderList,
    payOrder,
    fetchPayOrder,
    fetchPayOrderList,
    createPayOrder,
    patchPayOrder,
    updatePayOrder,
    deletePayOrder,

    paymentPerInstallmentList,
    fetchPaymentPerInstallmentList,
    getPaymentPerInstallmentData,
    createPaymentPerInstallment,
    updatePaymentPerInstallment,
    deletePaymentPerInstallment,

    downPayList,
    fetchDownPayList,
    createDownPay,
    updateDownPay,
    deleteDownPay,

    // old property
    paymentList,
    AllPaymentList,
    getPayments,
    paymentsCount,
    fetchPaymentList,
    fetchAllPaymentList,
    paymentPages,

    paymentSummaryList,
    fetchPaymentSummaryList,

    overallSummary,
    fetchOverallSummary,

    paymentStatusByUnitType,
    fetchPaymentStatusByUnitType,

    // new property
    ledgerPaymentList,
    ledgerAllPaymentList,
    legerGetPayments,
    ledgerPaymentsCount,
    ledgerPaymentPages,
    fetchLedgerPaymentList,
    fetchLedgerAllPaymentList,

    ledgerPaymentSummaryList,
    fetchLedgerPaymentSummaryList,

    ledgerOverallSummary,
    fetchLedgerOverallSummary,

    ledgerPaymentStatusByUnitType,
    fetchLedgerPaymentStatusByUnitType,

    // ContractPayment CRUD (Ledger 기반)
    createContractPayment,
    updateContractPayment,
    patchContractPayment,
    deleteContractPayment,
    fetchBankTransactionDetail,
    fetchAccountingEntriesByTransactionId,
  }
})
