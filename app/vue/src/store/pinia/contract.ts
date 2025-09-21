import api from '@/api'
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { message, errorHandle } from '@/utils/helper'
import {
  type Contract,
  type SimpleCont,
  type Contractor,
  type SubsSummary,
  type ContSummary,
  type OrderGroup,
  type KeyUnit,
  type HouseUnit,
  type SalesPrice,
  type DownPayment,
  type Succession,
  type BuyerForm,
  type ContractRelease,
} from '@/store/types/contract'

export interface ContFilter {
  project?: number | null
  order_group?: string
  unit_type?: string
  building?: string
  status?: string
  null_unit?: boolean
  qualification?: string
  is_sup_cont?: 'true' | 'false' | ''
  ordering?: string
  from_date?: string
  to_date?: string
  search?: string
  page?: number
  limit?: number | ''
}

export type UnitFilter = {
  project: number
  unit_type?: number
  contract?: number
  available?: 'true' | ''
}

export const useContract = defineStore('contract', () => {
  // state & getters
  const contract = ref<Contract | null>(null)
  const contractList = ref<Contract[]>([])
  const isLoading = ref(false)
  const contractsCount = ref<number>(0)
  const getContracts = ref<{ value: number; label: string }[]>([])

  // actions
  const fetchAllContracts = async (project: number) =>
    await api
      .get(`/simple-contract/?project=${project}`)
      .then(res => (getContracts.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const contractPages = (itemsPerPage: number) => Math.ceil(contractsCount.value / itemsPerPage)

  const fetchContract = (pk: number) =>
    api
      .get(`/contract-set/${pk}/`)
      .then(res => (contract.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const removeContract = () => (contract.value = null)

  const fetchContractList = async (payload: ContFilter) => {
    isLoading.value = true
    const status = payload.status ?? '2'
    const limit = payload.limit ?? 10
    let url = `/contract-set/`
    url += `?project=${payload.project}&activation=true&contractor__status=${status}&limit=${limit}`
    if (payload.order_group) url += `&order_group=${payload.order_group}`
    if (payload.unit_type) url += `&unit_type=${payload.unit_type}`
    if (payload.building) url += `&keyunit__houseunit__building_unit=${payload.building}`
    if (payload.null_unit) url += '&houseunit__isnull=true'
    if (payload.qualification) url += `&contractor__qualification=${payload.qualification}`
    if (payload.is_sup_cont) url += `&is_sup_cont=${payload.is_sup_cont}`
    if (payload.from_date) url += `&from_contract_date=${payload.from_date}`
    if (payload.to_date) url += `&to_contract_date=${payload.to_date}`
    if (payload.search) url += `&search=${payload.search}`
    const ordering = payload.ordering ? payload.ordering : '-created'
    const page = payload.page ? payload.page : 1
    url += `&ordering=${ordering}&page=${page}`

    return await api
      .get(url)
      .then(res => {
        contractList.value = res.data.results
        contractsCount.value = res.data.count
        isLoading.value = false
      })
      .catch(err => errorHandle(err.response.data))
  }

  const findContractPage = async (highlightId: number, filters: ContFilter) => {
    const status = filters.status ?? '2'
    const limit = filters.limit ?? 10
    let url = `/contract-set/find_page/?highlight_id=${highlightId}`
    url += `&project=${filters.project}&activation=true&contractor__status=${status}&limit=${limit}`
    if (filters.order_group) url += `&order_group=${filters.order_group}`
    if (filters.unit_type) url += `&unit_type=${filters.unit_type}`
    if (filters.building) url += `&keyunit__houseunit__building_unit=${filters.building}`
    if (filters.null_unit) url += '&houseunit__isnull=true'
    if (filters.qualification) url += `&contractor__qualification=${filters.qualification}`
    if (filters.is_sup_cont) url += `&is_sup_cont=${filters.is_sup_cont}`
    if (filters.from_date) url += `&from_contract_date=${filters.from_date}`
    if (filters.to_date) url += `&to_contract_date=${filters.to_date}`
    if (filters.search) url += `&search=${filters.search}`
    const ordering = filters.ordering ? filters.ordering : '-created'
    url += `&ordering=${ordering}`

    try {
      const response = await api.get(url)
      return response.data.page
    } catch (err: any) {
      errorHandle(err.response.data)
      return 1
    }
  }

  const config_headers = { headers: { 'Content-Type': 'multipart/form-data' } }

  const createContractSet = (payload: FormData) =>
    api
      .post(`/contract-set/`, payload, config_headers)
      .then(() => message())
      .catch(err => errorHandle(err.response.data))

  const updateContractSet = (pk: number, payload: FormData) =>
    api
      .put(`/contract-set/${pk}/`, payload, config_headers)
      .then(async res => {
        await fetchContract(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const contList = ref<SimpleCont[]>([])
  const fetchContList = (project: number) =>
    api
      .get(`/contract/?project=${project}`)
      .then(res => {
        contList.value = res.data.results
      })
      .catch(err => errorHandle(err.response.data))

  // 일괄 가격 업데이트 미리보기
  const previewContractPriceUpdate = async (project: number) => {
    try {
      const response = await api.post('/contract-price-update-preview/', { project })
      return response.data
    } catch (err: any) {
      errorHandle(err.response.data)
      throw err
    }
  }

  // 일괄 가격 업데이트 실행
  const bulkUpdateContractPrices = async (project: number) => {
    try {
      const response = await api.post('/contract-bulk-price-update/', { project })
      message('success', '완료!', '프로젝트 내 모든 계약 가격이 일괄 업데이트되었습니다.', 5000)
      return response.data
    } catch (err: any) {
      errorHandle(err.response.data)
      throw err
    }
  }

  // 개별 계약 가격 업데이트 (기존 함수명 유지하되 기능 단순화)
  const allContPriceSet = (payload: SimpleCont) =>
    api
      .put(`/contract/${payload.pk}/`, payload)
      .then(() => message('info', '', '개별 계약건 공급가가 재설정 되었습니다.', 5000))
      .catch(err => errorHandle(err.response.data))

  const contractor = ref<Contractor | null>(null)
  const contractorList = ref<Contractor[]>([])

  // actions
  const fetchContractor = (pk: number, project?: number) =>
    api
      .get(`/contractor/${pk}/?project=${project || ''}`)
      .then(res => (contractor.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const removeContractor = () => (contractor.value = null)

  const fetchContractorList = (project: number, search = '') => {
    api
      .get(`/contractor/?contract__project=${project}&search=${search}&is_active=true`)
      .then(res => (contractorList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  // state & getters
  const subsSummaryList = ref<SubsSummary[]>([])
  const contSummaryList = ref<ContSummary[]>([])
  const contAggregate = ref<{
    total_units: number
    subs_num: number
    conts_num: number
    non_conts_num: number
  } | null>()
  const contPriceSum = ref<{
    down_pay_sum: number
    middle_pay_sum: number
    remain_pay_sum: number
  } | null>(null)

  // actions
  const fetchSubsSummaryList = (project: number) =>
    api
      .get(`/subs-sum/?project=${project}`)
      .then(res => (subsSummaryList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchContSummaryList = (project: number, date = '') =>
    api
      .get(`/cont-sum/?project=${project}&to_contract_date=${date}`)
      .then(res => (contSummaryList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const removeContAggregate = () => (contAggregate.value = null)

  const fetchContAggregate = (project: number) =>
    api
      .get(`/cont-aggregate/${project}/`)
      .then(res => (contAggregate.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchContPriceSum = (project: number) =>
    api
      .get(`/cont-price-sum/${project}/`)
      .then(res => (contPriceSum.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const removeContPriceSum = () => (contPriceSum.value = null)

  const orderGroupList = ref<OrderGroup[]>([])
  const getOrderGroups = computed(() =>
    orderGroupList.value.map(o => ({
      value: o.pk,
      label: o.name,
      sort: o.sort,
    })),
  )

  const fetchOrderGroupList = (project: number, sort = '') =>
    api
      .get(`/order-group/?project=${project}&&sort=${sort}`)
      .then(res => (orderGroupList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createOrderGroup = (payload: OrderGroup) =>
    api
      .post(`/order-group/`, payload)
      .then(res => {
        fetchOrderGroupList(res.data.project).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateOrderGroup = (payload: OrderGroup) =>
    api
      .put(`/order-group/${payload.pk}/`, payload)
      .then(res => fetchOrderGroupList(res.data.project).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const deleteOrderGroup = (payload: { pk: number; project: number }) =>
    api
      .delete(`/order-group/${payload.pk}/`)
      .then(() =>
        fetchOrderGroupList(payload.project).then(() =>
          message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  // state & getters
  const keyUnitList = ref<KeyUnit[]>([])
  const getKeyUnits = computed(() =>
    keyUnitList.value.map(k => ({
      value: k.pk,
      label: k.unit_code,
    })),
  )
  const houseUnitList = ref<HouseUnit[]>([])
  const getHouseUnits = computed(() =>
    houseUnitList.value.map(h => ({ value: h.pk, label: h.__str__ })),
  )
  const salesPriceList = ref<SalesPrice[]>([])
  const downPaymentList = ref<DownPayment[]>([])

  // actions
  const fetchKeyUnitList = async (payload: UnitFilter) => {
    const { project } = payload
    const unit_type = payload.unit_type || ''
    const contract = payload.contract || ''
    const available = payload.available || ''
    return await api
      .get(
        `/key-unit/?project=${project}&unit_type=${unit_type}&contract=${contract}&available=${available}`,
      )
      .then(res => (keyUnitList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }
  const fetchHouseUnitList = async (payload: {
    project: number
    unit_type?: number
    contract?: number
  }) => {
    const { project } = payload
    let url = `/available-house-unit/?project=${project}`
    if (payload.unit_type) url += `&unit_type=${payload.unit_type}`
    if (payload.contract) url += `&contract=${payload.contract}`

    return await api
      .get(url)
      .then(res => (houseUnitList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }
  const fetchSalePriceList = async (payload: {
    project: number
    order_group?: number
    unit_type?: number
  }) => {
    const { project } = payload
    let url = `/price/?project=${project}`
    if (payload.order_group) url += `&order_group=${payload.order_group}`
    if (payload.unit_type) url += `&unit_type=${payload.unit_type}`

    return await api
      .get(url)
      .then(res => (salesPriceList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }
  const fetchDownPayList = async (payload: {
    project: number
    order_group?: number
    unit_type?: number
  }) => {
    const { project } = payload
    let url = `/down-payment/?project=${project}`
    if (payload.order_group) url += `&order_group=${payload.order_group}`
    if (payload.unit_type) url += `&unit_type=${payload.unit_type}`

    return await api
      .get(url)
      .then(res => (downPaymentList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  // state & getters
  const succession = ref<Succession | null>(null)
  const successionList = ref<Succession[]>([])
  const successionCount = ref<number>(0)

  // actions
  const successionPages = (itemsPerPage: number) => Math.ceil(successionCount.value / itemsPerPage)

  const fetchSuccession = (pk: number) =>
    api
      .get(`/succession/${pk}/`)
      .then(res => (succession.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchSuccessionList = (project: number, page = 1) =>
    api
      .get(`/succession/?contract__project=${project}&page=${page}`)
      .then(res => {
        successionList.value = res.data.results
        successionCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))

  const createSuccession = async (
    payload: Succession & BuyerForm & { project: number; page: number },
  ) => {
    const { project, page, ...dbData } = payload
    return await api
      .post(`/succession/`, dbData)
      .then(res =>
        fetchSuccessionList(project, page).then(() =>
          fetchContractor(res.data.buyer.pk).then(() => message()),
        ),
      )
      .catch(err => errorHandle(err.response.data))
  }

  const patchSuccession = async (
    payload: Succession & BuyerForm & { project: number; page: number },
  ) => {
    const { pk, project, page, ...dbData } = payload
    return await api
      .put(`/succession/${pk}/`, dbData)
      .then(res =>
        fetchSuccessionList(project, page).then(() =>
          fetchContractor(res.data.buyer.pk).then(() => message()),
        ),
      )
      .catch(err => errorHandle(err.response.data))
  }

  const findSuccessionPage = async (highlightId: number, projectId: number) => {
    let url = `/succession/find-page/?highlight_id=${highlightId}`
    url += `&project=${projectId}&limit=10`

    try {
      const response = await api.get(url)
      return response.data.page
    } catch (err: any) {
      errorHandle(err.response.data)
      return 1
    }
  }

  const findContractorReleasePage = async (highlightId: number, projectId: number) => {
    let url = `/contractor-release/find-page/?highlight_id=${highlightId}`
    url += `&project=${projectId}&limit=10`

    try {
      const response = await api.get(url)
      return response.data.page
    } catch (err: any) {
      errorHandle(err.response.data)
      return 1
    }
  }

  // state & getters
  const contRelease = ref<ContractRelease | null>(null)
  const contReleaseList = ref<ContractRelease[]>([])
  const contReleaseCount = ref<number>(0)

  // actions
  const releasePages = (itemsPerPage: number) => Math.ceil(contReleaseCount.value / itemsPerPage)

  const fetchContRelease = (pk: number) =>
    api
      .get(`/contractor-release/${pk}/`)
      .then(res => (contRelease.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchContReleaseList = (project: number, page = 1) =>
    api
      .get(`/contractor-release/?project=${project}&page=${page}`)
      .then(res => {
        contReleaseList.value = res.data.results
        contReleaseCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))

  const createRelease = (payload: ContractRelease) =>
    api
      .post(`/contractor-release/`, payload)
      .then(res => {
        contRelease.value = res.data
        fetchContReleaseList(payload.project).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateRelease = (payload: ContractRelease & { page: number }) =>
    api
      .put(`/contractor-release/${payload.pk}/`, payload)
      .then(() => fetchContReleaseList(payload.project, payload.page).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  return {
    contract,
    contractList,
    isLoading,
    contractsCount,
    getContracts,

    fetchAllContracts,
    contractPages,
    fetchContract,
    removeContract,
    fetchContractList,
    findContractPage,
    createContractSet,
    updateContractSet,

    contList,
    fetchContList,
    previewContractPriceUpdate,
    bulkUpdateContractPrices,
    // allContPriceSet,

    contractor,
    contractorList,

    fetchContractor,
    removeContractor,
    fetchContractorList,

    subsSummaryList,
    contSummaryList,
    contAggregate,
    contPriceSum,

    fetchSubsSummaryList,
    fetchContSummaryList,
    removeContAggregate,
    fetchContAggregate,
    fetchContPriceSum,
    removeContPriceSum,

    orderGroupList,
    getOrderGroups,

    fetchOrderGroupList,
    createOrderGroup,
    updateOrderGroup,
    deleteOrderGroup,

    keyUnitList,
    getKeyUnits,
    houseUnitList,
    getHouseUnits,
    salesPriceList,
    downPaymentList,

    fetchKeyUnitList,
    fetchHouseUnitList,
    fetchSalePriceList,
    fetchDownPayList,

    succession,
    successionList,
    successionCount,

    successionPages,
    fetchSuccession,
    fetchSuccessionList,
    createSuccession,
    patchSuccession,
    findSuccessionPage,

    contRelease,
    contReleaseList,
    contReleaseCount,

    releasePages,
    fetchContRelease,
    fetchContReleaseList,
    createRelease,
    updateRelease,
    findContractorReleasePage,
  }
})
