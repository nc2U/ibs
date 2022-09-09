import api from '@/api'
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { message, errorHandle } from '@/utils/helper'
import {
  Price,
  PayOrder,
  DownPay,
  PaySumByType,
  ContractNum,
} from '@/store/types/payment'
import { ProjectCashBook } from '@/store/types/proCash'
import { numFormat } from '@/utils/baseMixins'

export const usePayment = defineStore('payment', () => {
  // state & getters
  const priceList = ref<Price[]>([])

  type Ids = {
    project: number | null
    order_group: number | null
    unit_type: number | null
  }

  // actions
  const fetchPriceList = (payload: Ids) => {
    const { project, order_group, unit_type } = payload
    const url = `/price/?project=${project || ''}&order_group=${
      order_group || ''
    }&unit_type=${unit_type || ''}`

    return api
      .get(url)
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

  const deletePrice = (payload: Ids & { pk: number }) =>
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

  const fetchPayOrderList = (project: number) =>
    api
      .get(`/pay-order/?project=${project}`)
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
  const fetchDownPayList = (payload: any) => {
    let url = `/down-payment/?project=${payload.project}`
    if (payload.order_group) url += `&order_group=${payload.order_group}`
    if (payload.unit_type) url += `&unit_type=${payload.unit_type}`
    return api
      .get(url)
      .then(res => (paymentList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const createDownPay = (payload: DownPay) =>
    api
      .post(`/down-payment/`, payload)
      .then(res =>
        fetchDownPayList({ project: res.data.project }).then(() => message()),
      )
      .catch(err => errorHandle(err.response.data))

  const updateDownPay = (payload: DownPay) =>
    api
      .put(`/down-payment/${payload.pk}/`, payload)
      .then(res =>
        fetchDownPayList({ project: res.data.project }).then(() => message()),
      )
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
  const paymentList = ref<ProjectCashBook[]>([])
  const AllPaymentList = ref<ProjectCashBook[]>([])
  const getPayments = computed(() =>
    paymentList.value
      ? paymentList.value.map((p: any) => ({
          pk: p.pk,
          deal_date: p.deal_date,
          contract: p.contract,
          order_group: p.contract
            ? p.contract.order_group.order_group_name
            : '-',
          type_color: p.contract ? p.contract.unit_type.color : '-',
          type_name: p.contract ? p.contract.unit_type.name : '-',
          serial_number: p.contract ? p.contract.serial_number : '-',
          contractor: p.contract ? p.contract.contractor : '-',
          income: p.income,
          installment_order:
            p.contract && p.installment_order
              ? p.installment_order.__str__
              : '-',
          bank_account: p.bank_account.alias_name,
          trader: p.trader,
        }))
      : [],
  )
  const paymentsCount = ref<number>(0)

  // actions
  const fetchPaymentList = (payload: any) => {
    const { project } = payload
    let url = `/payment/?project=${project}`
    if (payload.from_date) url += `&from_deal_date=${payload.from_date}`
    if (payload.to_date) url += `&to_deal_date=${payload.to_date}`
    if (payload.pay_order) url += `&installment_order=${payload.pay_order}`
    if (payload.pay_account) url += `&bank_account=${payload.pay_account}`
    if (payload.contract) url += `&contract=${payload.contract}`
    if (payload.no_contract) url += `&no_contract=${payload.no_contract}`
    if (payload.ordering) url += `&ordering=${payload.ordering}`
    if (payload.search) url += `&search=${payload.search}`
    const page = payload.page ? payload.page : 1
    if (payload.page) url += `&page=${page}`
    return api
      .get(url)
      .then(res => (paymentList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllPaymentList = (payload: any) => {
    const { project } = payload
    let url = `/all-payment/?project=${project}`
    if (payload.contract) url += `&contract=${payload.contract}`
    if (payload.ordering) url += `&ordering=${payload.ordering}`
    api
      .get(url)
      .then(res => (AllPaymentList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const paymentPages = (itemsPerPage: number) =>
    Math.ceil(paymentsCount.value / itemsPerPage)

  // state & getters
  const paySumList = ref<PaySumByType[]>([])

  // actions
  const fetchPaySumList = (project: number) =>
    api
      .get(`/payment-sum/?project=${project}`)
      .then(res => (paySumList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  // state & getters
  const contNumList = ref<ContractNum[]>([])

  // actions
  const fetchContNumList = (project: number) =>
    api
      .get(`/contract-num/?project=${project}`)
      .then(res => (contNumList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

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

    paySumList,

    fetchPaySumList,

    contNumList,

    fetchContNumList,
  }
})
