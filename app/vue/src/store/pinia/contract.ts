import api from '@/api'
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { message, errorHandle } from '@/utils/helper'
import {
  type RequiredDocs,
  type Contract,
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
  type ContractorAddress,
  type ContractPriceWithPaymentPlan,
  type ContractDocument,
  type ConsultationLog,
  type ConsultationLogPagination,
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
  const requiredDocsList = ref<RequiredDocs[]>([])
  const fetchRequiredDocsList = async (project: number) =>
    await api
      .get(`/required-docs/?project=${project}`)
      .then(res => (requiredDocsList.value = res.data.results))
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
      .then(async res => {
        await fetchContractList({ project: res.data.project, status: res.data.contractor.status })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateContractSet = (pk: number, payload: FormData) =>
    api
      .put(`/contract-set/${pk}/`, payload, config_headers)
      .then(async res => {
        await fetchContractList({ project: res.data.project, status: res.data.contractor.status })
        message()
      })
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
  const createContractFile = async (contractorId: number, file: File, contract: number) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('contractor', contractorId.toString())

    return await api
      .post(`/contract-file/upload/${contractorId}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then(async res => {
        await fetchContract(contract)
        message('success', '파일이 업로드되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err.response.data)
        throw err
      })
  }

  const updateContractFile = async (pk: number, file: File, contract: number) => {
    const formData = new FormData()
    formData.append('file', file)

    return await api
      .patch(`/contract-file/${pk}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then(async res => {
        await fetchContract(contract)
        message('success', '파일이 수정되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err.response.data)
        throw err
      })
  }

  const removeContractFile = async (pk: number, contract: number) => {
    return await api
      .delete(`/contract-file/${pk}/`)
      .then(async () => {
        await fetchContract(contract)
        message('warning', '파일이 삭제되었습니다.')
      })
      .catch(err => {
        errorHandle(err.response.data)
        throw err
      })
  }

  // state & getters - ContractDocument
  const contractDocumentList = ref<ContractDocument[]>([])

  // actions - ContractDocument CRUD
  const fetchContractDocuments = (contractor: number, sort?: 'proof' | 'pledge') =>
    api
      .get(`/contract-docs/?contractor=${contractor}&sort=${sort || ''}`)
      .then(res => (contractDocumentList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createContractDocument = async (payload: ContractDocument) => {
    return await api
      .post(`/contract-docs/`, payload)
      .then(async res => {
        await fetchContractDocuments(res.data.contractor)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err.response.data)
        throw err
      })
  }

  const updateContractDocument = async (pk: number, payload: Partial<ContractDocument>) => {
    return await api
      .patch(`/contract-docs/${pk}/`, payload)
      .then(async res => {
        await fetchContractDocuments(res.data.contractor)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err.response.data)
        throw err
      })
  }

  const deleteContractDocument = async (pk: number, contractor: number) => {
    return await api
      .delete(`/contract-docs/${pk}/`)
      .then(async () => {
        await fetchContractDocuments(contractor)
        message('warning', '알림!', '서류 기록이 삭제되었습니다.')
      })
      .catch(err => {
        errorHandle(err.response.data)
        throw err
      })
  }

  // actions - ContractDocumentFile
  const uploadDocumentFile = async (contractDocId: number, file: File, contractor: number) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('contract_document', contractDocId.toString())

    return await api
      .post(`/contract-docs-file/upload/${contractDocId}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then(async res => {
        await fetchContractDocuments(contractor)
        message('success', '파일이 업로드되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err.response.data)
        throw err
      })
  }

  const deleteDocumentFile = async (pk: number, contractDocId: number, contractor: number) => {
    return await api
      .delete(`/contract-docs-file/${pk}/`)
      .then(async () => {
        await fetchContractDocuments(contractor)
        message('warning', '파일이 삭제되었습니다.')
      })
      .catch(err => {
        errorHandle(err.response.data)
        throw err
      })
  }

  const downloadDocumentFile = (fileUrl: string, fileName: string) => {
    const link = document.createElement('a')
    link.href = fileUrl
    link.download = fileName
    link.click()
  }

  // state & getters
  const contAddressList = ref<ContractorAddress[]>([])

  const fetchContAddressList = (contractor: number, is_current: boolean = false) =>
    api
      .get(`/contractor-address/?contractor=${contractor}&is_current=${is_current}`)
      .then(res => (contAddressList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createContAddress = (payload: any) =>
    api
      .post(`/contractor-address/`, payload)
      .then(async res => {
        try {
          if (contract.value?.pk) {
            await fetchContract(contract.value.pk)
          }
          await fetchContAddressList(res.data.contractor)
          message()
        } catch (error) {
          message('danger', '데이터 갱신 에러', `${error}`, 5000)
        }
      })
      .catch(err => errorHandle(err.response.data))

  const patchContAddress = (pk: number, payload: any) =>
    api
      .patch(`/contractor-address/${pk}/`, payload)
      .then(async res => {
        try {
          if (contract.value?.pk) {
            await fetchContract(contract.value.pk)
          }
          await fetchContAddressList(res.data.contractor)
          message()
        } catch (error) {
          message('danger', '데이터 갱신 에러', `${error}`, 5000)
        }
      })
      .catch(err => errorHandle(err.response.data))

  // Consultation Logs
  const consultationLogList = ref<ConsultationLog[]>([])
  const consultationLogPagination = ref({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    page: 1,
    pageSize: 15,
  })

  const fetchConsultationLogs = async (
    contractorId: number,
    params?: { page?: number; status?: string },
  ) => {
    const queryParams = new URLSearchParams({
      contractor: contractorId.toString(),
      page: (params?.page || 1).toString(),
      ...(params?.status && { status: params.status }),
    })

    try {
      const res = await api.get(`/contractor-consultations/?${queryParams}`)
      consultationLogList.value = res.data.results
      consultationLogPagination.value = {
        count: res.data.count,
        next: res.data.next,
        previous: res.data.previous,
        page: params?.page || 1,
        pageSize: 15,
      }
      return res.data
    } catch (err: any) {
      return errorHandle(err.response.data)
    }
  }

  const createConsultationLog = async (payload: Partial<ConsultationLog>) => {
    return await api
      .post('/contractor-consultations/', payload)
      .then(async res => {
        if (payload.contractor) {
          await fetchConsultationLogs(payload.contractor)
        }
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err.response.data)
        throw err
      })
  }

  const updateConsultationLog = async (pk: number, payload: Partial<ConsultationLog>) => {
    return await api
      .patch(`/contractor-consultations/${pk}/`, payload)
      .then(async res => {
        if (res.data.contractor) {
          await fetchConsultationLogs(res.data.contractor, {
            page: consultationLogPagination.value.page,
          })
        }
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err.response.data)
        throw err
      })
  }

  const deleteConsultationLog = async (pk: number, contractorId: number) => {
    return await api
      .delete(`/contractor-consultations/${pk}/`)
      .then(async () => {
        await fetchConsultationLogs(contractorId, {
          page: consultationLogPagination.value.page,
        })
        message('warning', '알림!', '상담 내역이 삭제되었습니다.')
      })
      .catch(err => {
        errorHandle(err.response.data)
        throw err
      })
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

  // 일괄 가격 업데이트 미리보기
  const previewContractPriceUpdate = async (project: number, uncontractedOrderGroup?: number) => {
    try {
      let url = `/contract-price-update-preview/?project=${project}`
      if (uncontractedOrderGroup) {
        url += `&uncontracted_order_group=${uncontractedOrderGroup}`
      }
      const response = await api.get(url)
      return response.data
    } catch (err: any) {
      errorHandle(err.response.data)
      throw err
    }
  }

  // 일괄 가격 업데이트 실행
  const bulkUpdateContractPrices = async (
    project: number,
    uncontractedOrderGroup?: number,
    dryRun?: boolean,
  ) => {
    try {
      const payload: { project: number; uncontracted_order_group?: number; dry_run?: boolean } = {
        project,
      }
      if (uncontractedOrderGroup) {
        payload.uncontracted_order_group = uncontractedOrderGroup
      }
      if (dryRun !== undefined) {
        payload.dry_run = dryRun
      }

      const response = await api.post('/contract-bulk-price-update/', payload)

      if (!dryRun) {
        const successMessage =
          response.data.message || '프로젝트 내 모든 계약 가격이 일괄 업데이트되었습니다.'
        message('success', '완료!', successMessage, 5000)
      }

      return response.data
    } catch (err: any) {
      errorHandle(err.response.data)
      throw err
    }
  }

  // 계약별 납부 계획 조회 (기존 방식)
  const fetchContractPaymentPlan = async (contractId: number) => {
    try {
      const response = await api.get(`/contract/${contractId}/payment-plan/`)
      return response.data
    } catch (err: any) {
      errorHandle(err.response.data)
      throw err
    }
  }

  // ContractPrice JSON 캐시 기반 납부 계획 조회 (고성능)
  const fetchContractPricePaymentPlan = async (
    contractId: number,
  ): Promise<ContractPriceWithPaymentPlan> => {
    try {
      const response = await api.get(`/contract/${contractId}/price-payment-plan/`)
      return response.data
    } catch (err: any) {
      errorHandle(err.response.data)
      throw err
    }
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

  return {
    orderGroupList,
    getOrderGroups,
    fetchOrderGroupList,
    createOrderGroup,
    updateOrderGroup,
    deleteOrderGroup,

    requiredDocsList,
    fetchRequiredDocsList,

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
    previewContractPriceUpdate,
    bulkUpdateContractPrices,
    fetchContractPaymentPlan,
    fetchContractPricePaymentPlan,

    contractor,
    contractorList,
    fetchContractor,
    removeContractor,
    fetchContractorList,

    createContractFile,
    updateContractFile,
    removeContractFile,

    contractDocumentList,
    fetchContractDocuments,
    createContractDocument,
    updateContractDocument,
    deleteContractDocument,
    uploadDocumentFile,
    deleteDocumentFile,
    downloadDocumentFile,

    contAddressList,
    fetchContAddressList,
    createContAddress,
    patchContAddress,

    // Consultation Logs
    consultationLogList,
    consultationLogPagination,
    fetchConsultationLogs,
    createConsultationLog,
    updateConsultationLog,
    deleteConsultationLog,

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

    subsSummaryList,
    contSummaryList,
    contAggregate,
    fetchSubsSummaryList,
    fetchContSummaryList,
    removeContAggregate,
    fetchContAggregate,
  }
})
