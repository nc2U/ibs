import api from '@/api'
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { message, errorHandle } from '@/utils/helper'
import { type CashBookFilter } from '@/store/types/proCash'
import {
  type Price,
  type PayOrder,
  type DownPay,
  type PaymentSummaryComponent,
  type ContractNum,
  type AllPayment,
  type OverallSummary,
  type PaymentStatusByUnitType,
  type PaymentPerInstallment,
  type PaymentPerInstallmentPayload,
} from '@/store/types/payment'

export type DownPayFilter = {
  project: number
  order_group?: number
  unit_type?: number
}

export type PriceFilter = {
  project?: number | null
  order_group?: number | null
  unit_type?: number | null
}

export type PaymentPerInstallmentFilter = {
  sales_price?: number | null
  sales_price__project?: number | null
  sales_price__order_group?: number | null
  sales_price__unit_type?: number | null
  pay_order?: number | null
}

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
  const contNumList = ref<ContractNum[]>([])

  // actions
  const fetchContNumList = (project: number) =>
    api
      .get(`/cont-num-type/?project=${project}`)
      .then(res => (contNumList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

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

    downPayList,

    fetchDownPayList,
    createDownPay,
    updateDownPay,
    deleteDownPay,

    paymentList,
    AllPaymentList,
    getPayments,
    paymentsCount,

    fetchPaymentList,
    fetchAllPaymentList,
    paymentPages,

    paymentSummaryList,
    fetchPaymentSummaryList,

    contNumList,
    fetchContNumList,

    overallSummary,
    fetchOverallSummary,

    paymentStatusByUnitType,
    fetchPaymentStatusByUnitType,

    paymentPerInstallmentList,
    fetchPaymentPerInstallmentList,
    getPaymentPerInstallmentData,
    createPaymentPerInstallment,
    updatePaymentPerInstallment,
    deletePaymentPerInstallment,
  }
})
