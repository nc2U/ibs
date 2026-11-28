import api from '@/api'
import { computed, ref, type Ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, getErrorData, message } from '@/utils/helper'
import { type Company, type Logo, type CompanySeal } from '@/store/types/settings'
import {
  type Staff,
  type StaffFilter,
  type Department,
  type DepFilter,
  type Grade,
  type Position,
  type Duty,
  type ExecutiveRank,
  type Executive,
  type ExecutiveFilter,
  type PromotionPolicy,
  type PromotionPolicyFilter,
  type StaffEvaluation,
  type StaffEvaluationFilter,
  type PromotionCandidate,
  type PromotionCandidateFilter,
  type PersonnelOrder,
  type PersonnelOrderFilter,
  type StaffCareer,
  type StaffCertificate,
  type StaffRewardPunishment,
  type StaffRecordFilter,
  type StaffLeaveQuota,
  type StaffLeaveQuotaFilter,
  type StaffLeaveUsage,
  type StaffLeaveUsageFilter,
  type ComFilter,
} from '@/store/types/company'

const toQueryString = (params: Record<string, string | number | boolean | undefined | null>) => {
  const sp = new URLSearchParams()
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== null && val !== '') {
      sp.append(key, String(val))
    }
  }
  const qs = sp.toString()
  return qs ? `?${qs}` : ''
}

export const useCompany = defineStore('company', () => {
  // states & getters
  const companyList = ref<Company[]>([])
  const company = ref<Company | null>(null)

  const currentCompany = computed(
    () => company.value?.pk || Number(localStorage?.getItem?.('curr-company')),
  )
  const defaultCompany = computed(() => {
    const defaultCom = companyList.value.find(com => com.is_default) || companyList.value[0]
    return defaultCom?.pk || 1
  })

  const initComId = computed<number>(() => currentCompany.value || defaultCompany.value)

  const comSelect = computed<{ value: number; label: string }[]>(() => {
    return companyList.value.map((com: Company) => ({
      value: com.pk as number,
      label: com.name as string,
    }))
  })

  // actions
  const fetchCompanyList = () =>
    api
      .get('/company/')
      .then(res => (companyList.value = res.data.results))
      .catch(err => errorHandle(err))

  const fetchCompany = async (pk: number) => {
    try {
      const res = await api.get(`/company/${pk}/`)
      company.value = res.data
      // Update the localStorage to prevent future errors
      try {
        localStorage.setItem('curr-company', res.data.pk.toString())
      } catch {
        // ignore storage errors
      }
      console.log(`Switched to company: ${res.data.name} (ID: ${res.data.pk})`)
    } catch (err: unknown) {
      console.warn(`Company with ID ${pk} not found, trying to fetch first available company`)

      // If company fetch fails, try to get the first available company
      try {
        const companyListRes = await api.get('/company/')
        if (companyListRes.data.results && companyListRes.data.results.length > 0) {
          const firstCompany = companyListRes.data.results[0]
          company.value = firstCompany

          // Update the localStorage to prevent future errors
          try {
            localStorage.setItem('curr-company', firstCompany.pk.toString())
          } catch {
            // ignore storage errors
          }
          console.log(`Switched to company: ${firstCompany.name} (ID: ${firstCompany.pk})`)
        } else {
          const errData = getErrorData(err)
          errorHandle(errData === err ? { detail: 'No companies available' } : errData)
        }
      } catch (fallbackErr: unknown) {
        const errData = getErrorData(fallbackErr)
        errorHandle(errData === fallbackErr ? { detail: 'Failed to fetch companies' } : errData)
      }
    }
  }

  const removeCompany = () => (company.value = null)

  const createCompany = async (payload: Company): Promise<boolean> => {
    try {
      const res = await api.post(`/company/`, payload)
      await fetchCompanyList()
      await fetchCompany(res.data.pk)
      message()
      return true
    } catch (err) {
      errorHandle(err)
      return false
    }
  }

  const updateCompany = async (payload: Company): Promise<boolean> => {
    try {
      const res = await api.patch(`/company/${payload.pk}/`, payload)
      await Promise.all([fetchCompanyList(), fetchCompany(res.data.pk)])
      message()
      return true
    } catch (err) {
      errorHandle(err)
      return false
    }
  }

  const deleteCompany = async (pk: number): Promise<boolean> => {
    try {
      await api.delete(`/company/${pk}/`)
      await fetchCompanyList()
      if (company.value?.pk === pk) {
        const nextCompany =
          companyList.value.find(c => c.is_default) || companyList.value[0] || null
        if (nextCompany?.pk) {
          await fetchCompany(nextCompany.pk)
        } else {
          company.value = null
          try {
            localStorage.removeItem('curr-company')
          } catch {
            // ignore storage errors
          }
        }
      }
      message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      return true
    } catch (err) {
      errorHandle(err)
      return false
    }
  }

  // states & getters
  const logo = ref<Logo | null>(null)

  const fetchLogo = (pk: number) =>
    api
      .get(`/logo/${pk}/`)
      .then(res => (logo.value = res.data))
      .catch(err => errorHandle(err))

  const createLogo = (payload: Logo) =>
    api
      .post(`/logo/`, payload)
      .then(res => fetchLogo(res.data.pk).then(() => message()))
      .catch(err => errorHandle(err))

  const updateLogo = (payload: Logo) =>
    api
      .put(`/logo/${payload.pk}/`, payload)
      .then(res => fetchLogo(res.data.pk).then(() => message()))
      .catch(err => errorHandle(err))

  const deleteLogo = (pk: number) =>
    api
      .delete(`/logo/${pk}/`)
      .then(() => message('warning', '', '해당 오브젝트가 삭제되었습니다.'))
      .catch(err => errorHandle(err))

  // states & getters - CompanySeal
  const sealList = ref<CompanySeal[]>([])
  const seal = ref<CompanySeal | null>(null)

  const fetchCompanySealList = (companyId?: number) => {
    const com = companyId || currentCompany.value
    const url = com
      ? `/company-seal/?company=${com}&is_active=true`
      : `/company-seal/?is_active=true`
    return api
      .get(url)
      .then(res => (sealList.value = res.data.results || res.data))
      .catch(err => errorHandle(err))
  }

  const fetchCompanySeal = (pk: number) =>
    api
      .get(`/company-seal/${pk}/`)
      .then(res => (seal.value = res.data))
      .catch(err => errorHandle(err))

  const createCompanySeal = (payload: FormData | CompanySeal) =>
    api
      .post(`/company-seal/`, payload, {
        headers: payload instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : {},
      })
      .then(() => fetchCompanySealList().then(() => message()))
      .catch(err => errorHandle(err))

  const updateCompanySeal = (pk: number, payload: FormData | CompanySeal) =>
    api
      .put(`/company-seal/${pk}/`, payload, {
        headers: payload instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : {},
      })
      .then(() => fetchCompanySealList().then(() => message()))
      .catch(err => errorHandle(err))

  const deleteCompanySeal = (pk: number) =>
    api
      .delete(`/company-seal/${pk}/`)
      .then(() =>
        fetchCompanySealList().then(() => message('warning', '', '해당 인장이 삭제되었습니다.')),
      )
      .catch(err => errorHandle(err))

  // shared HR fetch / mutation helpers
  const fetchPaged = async <T>(
    url: string,
    listRef: Ref<T[]>,
    countRef: Ref<number>,
  ): Promise<void> => {
    try {
      const res = await api.get(url)
      listRef.value = res.data.results
      countRef.value = res.data.count
    } catch (err) {
      errorHandle(err)
    }
  }

  const fetchAllItems = async <T>(url: string, listRef: Ref<T[]>): Promise<void> => {
    try {
      const res = await api.get(url)
      listRef.value = res.data.results ?? res.data
    } catch (err) {
      errorHandle(err)
    }
  }

  const mutateHr = async (
    request: () => Promise<{ data?: { pk?: number } } | unknown>,
    refresh: (pk?: number) => Promise<unknown>,
    isDelete = false,
  ): Promise<boolean> => {
    try {
      const res = (await request()) as { data?: { pk?: number } } | undefined
      await refresh(res?.data?.pk)
      if (isDelete) message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      else message()
      return true
    } catch (err) {
      errorHandle(err)
      return false
    }
  }

  const departmentList = ref<Department[]>([])
  const allDepartList = ref<Department[]>([])
  const department = ref<Department | null>(null)

  const departmentsCount = ref<number>(0)

  // getters
  const getPkDeparts = computed(() =>
    allDepartList.value.map(d => ({
      value: d.pk,
      label: d.name,
      level: d.level,
    })),
  )

  const getSlugDeparts = computed(() =>
    allDepartList.value.map(d => ({
      value: d.name,
      label: d.name,
    })),
  )

  const getUpperDeps = computed(() => [
    ...new Set(allDepartList.value.filter(d => !!d.upper_depart).map(d => d.upper_depart)),
  ])

  // actions
  const departmentPages = (itemsPerPage: number) => Math.ceil(departmentsCount.value / itemsPerPage)

  const fetchDepartmentList = (payload: DepFilter) => {
    const { page = 1, com = 1, upp = '', q = '' } = payload
    const queryStr = toQueryString({ limit: 10, page, company: com, upper_depart: upp, search: q })
    return fetchPaged(`/department/${queryStr}`, departmentList, departmentsCount)
  }

  const fetchAllDepartList = (com = 1) =>
    fetchAllItems(`/department/${toQueryString({ company: com })}`, allDepartList)

  const fetchDepartment = (pk: number) =>
    api
      .get(`/department/${pk}/`)
      .then(res => (department.value = res.data))
      .catch(err => errorHandle(err))

  const createDepartment = (payload: Department, page = 1, com = 1, filter?: DepFilter) =>
    mutateHr(
      () => api.post('/department/', payload),
      async pk => {
        await fetchAllDepartList(com)
        await fetchDepartmentList({ ...(filter ?? {}), page, com })
        if (pk) await fetchDepartment(pk)
      },
    )

  const updateDepartment = (payload: Department, page = 1, com = 1, filter?: DepFilter) =>
    mutateHr(
      () => api.put(`/department/${payload.pk}/`, payload),
      async pk => {
        await fetchAllDepartList(com)
        await fetchDepartmentList({ ...(filter ?? {}), page, com })
        if (pk) await fetchDepartment(pk)
      },
    )

  const deleteDepartment = (pk: number, com = 1, filter?: DepFilter) =>
    mutateHr(
      () => api.delete(`/department/${pk}/`),
      async () => {
        await fetchAllDepartList(com)
        await fetchDepartmentList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  const gradeList = ref<Grade[]>([])
  const allGradeList = ref<Grade[]>([])
  const grade = ref<Grade | null>(null)
  const gradesCount = ref<number>(0)

  // getters
  const getGrades = computed(() =>
    allGradeList.value.map(r => ({
      value: r.code,
      label: r.code,
    })),
  )

  const getPkGrades = computed(() =>
    allGradeList.value.map(r => ({
      value: r.pk,
      label: r.code,
    })),
  )

  // actions
  const gradePages = (itemsPerPage: number) => Math.ceil(gradesCount.value / itemsPerPage)

  const fetchGradeList = (payload: ComFilter) => {
    const { page = 1, com = 1, q = '' } = payload
    const queryStr = toQueryString({ limit: 10, page, company: com, search: q })
    return fetchPaged(`/grade/${queryStr}`, gradeList, gradesCount)
  }

  const fetchAllGradeList = (com = 1) =>
    fetchAllItems(`/grade/${toQueryString({ company: com })}`, allGradeList)

  const fetchGrade = (pk: number) =>
    api
      .get(`/grade/${pk}/`)
      .then(res => (grade.value = res.data))
      .catch(err => errorHandle(err))

  const createGrade = (payload: Grade, page = 1, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.post('/grade/', payload),
      async pk => {
        await fetchAllGradeList(com)
        await fetchGradeList({ ...(filter ?? {}), page, com })
        if (pk) await fetchGrade(pk)
      },
    )

  const updateGrade = (payload: Grade, page = 1, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.put(`/grade/${payload.pk}/`, payload),
      async pk => {
        await fetchAllGradeList(com)
        await fetchGradeList({ ...(filter ?? {}), page, com })
        if (pk) await fetchGrade(pk)
      },
    )

  const deleteGrade = (pk: number, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.delete(`/grade/${pk}/`),
      async () => {
        await fetchAllGradeList(com)
        await fetchGradeList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  const positionList = ref<Position[]>([])
  const allPositionList = ref<Position[]>([])
  const position = ref<Position | null>(null)
  const positionsCount = ref<number>(0)

  // getters
  const getPositions = computed(() =>
    allPositionList.value.map(r => ({
      value: r.name,
      label: r.name,
    })),
  )

  const getPkPositions = computed(() =>
    allPositionList.value.map(r => ({
      value: r.pk,
      label: r.name,
    })),
  )

  // actions
  const positionPages = (itemsPerPage: number) => Math.ceil(positionsCount.value / itemsPerPage)

  const fetchPositionList = (payload: ComFilter) => {
    const { page = 1, com = 1, q = '' } = payload
    const queryStr = toQueryString({ limit: 10, page, company: com, search: q })
    return fetchPaged(`/position/${queryStr}`, positionList, positionsCount)
  }

  const fetchAllPositionList = (com = 1) =>
    fetchAllItems(`/position/${toQueryString({ company: com })}`, allPositionList)

  const fetchPosition = (pk: number) =>
    api
      .get(`/position/${pk}/`)
      .then(res => (position.value = res.data))
      .catch(err => errorHandle(err))

  const createPosition = (payload: Position, page = 1, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.post('/position/', payload),
      async pk => {
        await fetchAllPositionList(com)
        await fetchPositionList({ ...(filter ?? {}), page, com })
        if (pk) await fetchPosition(pk)
      },
    )

  const updatePosition = (payload: Position, page = 1, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.put(`/position/${payload.pk}/`, payload),
      async pk => {
        await fetchAllPositionList(com)
        await fetchPositionList({ ...(filter ?? {}), page, com })
        if (pk) await fetchPosition(pk)
      },
    )

  const deletePosition = (pk: number, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.delete(`/position/${pk}/`),
      async () => {
        await fetchAllPositionList(com)
        await fetchPositionList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  const dutyList = ref<Duty[]>([])
  const allDutyList = ref<Duty[]>([])
  const duty = ref<Duty | null>(null)
  const dutysCount = ref<number>(0)

  // getters
  const getDutys = computed(() =>
    allDutyList.value.map(r => ({
      value: r.name,
      label: r.name,
    })),
  )

  const getPkDutys = computed(() =>
    allDutyList.value.map(r => ({
      value: r.pk,
      label: r.name,
    })),
  )

  // actions
  const dutyPages = (itemsPerPage: number) => Math.ceil(dutysCount.value / itemsPerPage)

  const fetchDutyList = (payload: ComFilter) => {
    const { page = 1, com = 1, q = '' } = payload
    const queryStr = toQueryString({ limit: 10, page, company: com, search: q })
    return fetchPaged(`/duty-title/${queryStr}`, dutyList, dutysCount)
  }

  const fetchAllDutyList = (com = 1) =>
    fetchAllItems(`/duty-title/${toQueryString({ company: com })}`, allDutyList)

  const fetchDuty = (pk: number) =>
    api
      .get(`/duty-title/${pk}/`)
      .then(res => (duty.value = res.data))
      .catch(err => errorHandle(err))

  const createDuty = (payload: Duty, page = 1, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.post('/duty-title/', payload),
      async pk => {
        await fetchAllDutyList(com)
        await fetchDutyList({ ...(filter ?? {}), page, com })
        if (pk) await fetchDuty(pk)
      },
    )

  const updateDuty = (payload: Duty, page = 1, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.put(`/duty-title/${payload.pk}/`, payload),
      async pk => {
        await fetchAllDutyList(com)
        await fetchDutyList({ ...(filter ?? {}), page, com })
        if (pk) await fetchDuty(pk)
      },
    )

  const deleteDuty = (pk: number, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.delete(`/duty-title/${pk}/`),
      async () => {
        await fetchAllDutyList(com)
        await fetchDutyList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  // ExecutiveRank ----------------------------------------------------
  const executiveRankList = ref<ExecutiveRank[]>([])
  const allExecutiveRankList = ref<ExecutiveRank[]>([])
  const executiveRank = ref<ExecutiveRank | null>(null)
  const executiveRanksCount = ref<number>(0)

  const getExecutiveRanks = computed(() =>
    allExecutiveRankList.value.map(r => ({
      value: r.name,
      label: r.name,
    })),
  )

  const getPkExecutiveRanks = computed(() =>
    allExecutiveRankList.value.map(r => ({
      value: r.pk,
      label: r.name,
    })),
  )

  const executiveRankPages = (itemsPerPage: number) =>
    Math.ceil(executiveRanksCount.value / itemsPerPage)

  const fetchExecutiveRankList = (payload: ComFilter) => {
    const { page = 1, com = 1, q = '' } = payload
    const queryStr = toQueryString({ limit: 10, page, company: com, search: q })
    return fetchPaged(`/executive-rank/${queryStr}`, executiveRankList, executiveRanksCount)
  }

  const fetchAllExecutiveRankList = (com = 1) =>
    fetchAllItems(
      `/executive-rank/${toQueryString({ company: com, limit: 500 })}`,
      allExecutiveRankList,
    )

  const fetchExecutiveRank = (pk: number) =>
    api
      .get(`/executive-rank/${pk}/`)
      .then(res => (executiveRank.value = res.data))
      .catch(err => errorHandle(err))

  const createExecutiveRank = (payload: ExecutiveRank, page = 1, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.post('/executive-rank/', payload),
      async pk => {
        await fetchAllExecutiveRankList(com)
        await fetchExecutiveRankList({ ...(filter ?? {}), page, com })
        if (pk) await fetchExecutiveRank(pk)
      },
    )

  const updateExecutiveRank = (payload: ExecutiveRank, page = 1, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.put(`/executive-rank/${payload.pk}/`, payload),
      async pk => {
        await fetchAllExecutiveRankList(com)
        await fetchExecutiveRankList({ ...(filter ?? {}), page, com })
        if (pk) await fetchExecutiveRank(pk)
      },
    )

  const deleteExecutiveRank = (pk: number, com = 1, filter?: ComFilter) =>
    mutateHr(
      () => api.delete(`/executive-rank/${pk}/`),
      async () => {
        await fetchAllExecutiveRankList(com)
        await fetchExecutiveRankList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  // Executive --------------------------------------------------------
  const executiveList = ref<Executive[]>([])
  const allExecutiveList = ref<Executive[]>([])
  const executive = ref<Executive | null>(null)
  const executivesCount = ref<number>(0)

  const executivePages = (itemsPerPage: number) => Math.ceil(executivesCount.value / itemsPerPage)

  const fetchExecutiveList = (payload: ExecutiveFilter) => {
    const {
      page = 1,
      com = 1,
      rank = '',
      executive_type = '',
      is_registered = '',
      is_standing = '',
      represent_type = '',
      q = '',
    } = payload
    const queryStr = toQueryString({
      limit: 10,
      page,
      company: com,
      rank,
      executive_type,
      is_registered,
      is_standing,
      represent_type,
      search: q,
    })
    return fetchPaged(`/executive/${queryStr}`, executiveList, executivesCount)
  }

  const fetchAllExecutiveList = (com = 1) =>
    fetchAllItems(`/executive/${toQueryString({ company: com, limit: 500 })}`, allExecutiveList)

  const fetchExecutive = (pk: number) =>
    api
      .get(`/executive/${pk}/`)
      .then(res => (executive.value = res.data))
      .catch(err => errorHandle(err))

  const createExecutive = (payload: Executive, page = 1, com = 1, filter?: ExecutiveFilter) =>
    mutateHr(
      () => api.post('/executive/', payload),
      async pk => {
        await fetchAllExecutiveList(com)
        await fetchExecutiveList({ ...(filter ?? {}), page, com })
        await fetchAllStaffList(com)
        if (pk) await fetchExecutive(pk)
      },
    )

  const updateExecutive = (payload: Executive, page = 1, com = 1, filter?: ExecutiveFilter) =>
    mutateHr(
      () => api.put(`/executive/${payload.pk}/`, payload),
      async pk => {
        await fetchAllExecutiveList(com)
        await fetchExecutiveList({ ...(filter ?? {}), page, com })
        await fetchAllStaffList(com)
        if (pk) await fetchExecutive(pk)
      },
    )

  const deleteExecutive = (pk: number, com = 1, filter?: ExecutiveFilter) =>
    mutateHr(
      () => api.delete(`/executive/${pk}/`),
      async () => {
        await fetchAllExecutiveList(com)
        await fetchExecutiveList({ ...(filter ?? {}), page: 1, com })
        await fetchAllStaffList(com)
      },
      true,
    )

  // PromotionPolicy --------------------------------------------------
  const promotionPolicyList = ref<PromotionPolicy[]>([])
  const allPromotionPolicyList = ref<PromotionPolicy[]>([])
  const promotionPolicy = ref<PromotionPolicy | null>(null)
  const promotionPoliciesCount = ref<number>(0)

  const promotionPolicyPages = (itemsPerPage: number) =>
    Math.ceil(promotionPoliciesCount.value / itemsPerPage)

  const fetchPromotionPolicyList = (payload: PromotionPolicyFilter) => {
    const {
      page = 1,
      com = 1,
      current_grade = '',
      target_grade = '',
      is_active = '',
      q = '',
    } = payload
    const queryStr = toQueryString({
      limit: 10,
      page,
      company: com,
      current_grade,
      target_grade,
      is_active,
      search: q,
    })
    return fetchPaged(
      `/promotion-policy/${queryStr}`,
      promotionPolicyList,
      promotionPoliciesCount,
    )
  }

  const fetchAllPromotionPolicyList = (com = 1) =>
    fetchAllItems(
      `/promotion-policy/${toQueryString({ company: com, limit: 500 })}`,
      allPromotionPolicyList,
    )

  const fetchPromotionPolicy = (pk: number) =>
    api
      .get(`/promotion-policy/${pk}/`)
      .then(res => (promotionPolicy.value = res.data))
      .catch(err => errorHandle(err))

  const createPromotionPolicy = (
    payload: PromotionPolicy,
    page = 1,
    com = 1,
    filter?: PromotionPolicyFilter,
  ) =>
    mutateHr(
      () => api.post('/promotion-policy/', payload),
      async pk => {
        await fetchAllPromotionPolicyList(com)
        await fetchPromotionPolicyList({ ...(filter ?? {}), page, com })
        if (pk) await fetchPromotionPolicy(pk)
      },
    )

  const updatePromotionPolicy = (
    payload: PromotionPolicy,
    page = 1,
    com = 1,
    filter?: PromotionPolicyFilter,
  ) =>
    mutateHr(
      () => api.put(`/promotion-policy/${payload.pk}/`, payload),
      async pk => {
        await fetchAllPromotionPolicyList(com)
        await fetchPromotionPolicyList({ ...(filter ?? {}), page, com })
        if (pk) await fetchPromotionPolicy(pk)
      },
    )

  const deletePromotionPolicy = (pk: number, com = 1, filter?: PromotionPolicyFilter) =>
    mutateHr(
      () => api.delete(`/promotion-policy/${pk}/`),
      async () => {
        await fetchAllPromotionPolicyList(com)
        await fetchPromotionPolicyList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  // StaffEvaluation --------------------------------------------------
  const staffEvaluationList = ref<StaffEvaluation[]>([])
  const allStaffEvaluationList = ref<StaffEvaluation[]>([])
  const staffEvaluation = ref<StaffEvaluation | null>(null)
  const staffEvaluationsCount = ref<number>(0)

  const staffEvaluationPages = (itemsPerPage: number) =>
    Math.ceil(staffEvaluationsCount.value / itemsPerPage)

  const fetchStaffEvaluationList = (payload: StaffEvaluationFilter) => {
    const {
      page = 1,
      com = 1,
      eval_year = '',
      eval_period = '',
      grade = '',
      staff: staffId = '',
      q = '',
    } = payload
    const queryStr = toQueryString({
      limit: 10,
      page,
      company: com,
      staff: staffId,
      eval_year,
      eval_period,
      grade,
      search: q,
    })
    return fetchPaged(
      `/staff-evaluation/${queryStr}`,
      staffEvaluationList,
      staffEvaluationsCount,
    )
  }

  const fetchAllStaffEvaluationList = (com = 1, year?: number) =>
    fetchAllItems(
      `/staff-evaluation/${toQueryString({ company: com, limit: 500, eval_year: year })}`,
      allStaffEvaluationList,
    )

  const fetchStaffEvaluation = (pk: number) =>
    api
      .get(`/staff-evaluation/${pk}/`)
      .then(res => (staffEvaluation.value = res.data))
      .catch(err => errorHandle(err))

  const createStaffEvaluation = (
    payload: StaffEvaluation,
    page = 1,
    com = 1,
    filter?: StaffEvaluationFilter,
  ) =>
    mutateHr(
      () => api.post('/staff-evaluation/', payload),
      async pk => {
        await fetchAllStaffEvaluationList(com)
        await fetchStaffEvaluationList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffEvaluation(pk)
      },
    )

  const updateStaffEvaluation = (
    payload: StaffEvaluation,
    page = 1,
    com = 1,
    filter?: StaffEvaluationFilter,
  ) =>
    mutateHr(
      () => api.put(`/staff-evaluation/${payload.pk}/`, payload),
      async pk => {
        await fetchAllStaffEvaluationList(com)
        await fetchStaffEvaluationList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffEvaluation(pk)
      },
    )

  const deleteStaffEvaluation = (pk: number, com = 1, filter?: StaffEvaluationFilter) =>
    mutateHr(
      () => api.delete(`/staff-evaluation/${pk}/`),
      async () => {
        await fetchAllStaffEvaluationList(com)
        await fetchStaffEvaluationList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  // PromotionCandidate -----------------------------------------------
  const promotionCandidateList = ref<PromotionCandidate[]>([])
  const allPromotionCandidateList = ref<PromotionCandidate[]>([])
  const promotionCandidate = ref<PromotionCandidate | null>(null)
  const promotionCandidatesCount = ref<number>(0)

  const promotionCandidatePages = (itemsPerPage: number) =>
    Math.ceil(promotionCandidatesCount.value / itemsPerPage)

  const fetchPromotionCandidateList = (payload: PromotionCandidateFilter) => {
    const {
      page = 1,
      com = 1,
      eval_year = '',
      status: candStatus = '',
      policy = '',
      staff: staffId = '',
      q = '',
    } = payload
    const queryStr = toQueryString({
      limit: 10,
      page,
      company: com,
      eval_year,
      status: candStatus,
      policy,
      staff: staffId,
      search: q,
    })
    return fetchPaged(
      `/promotion-candidate/${queryStr}`,
      promotionCandidateList,
      promotionCandidatesCount,
    )
  }

  const fetchAllPromotionCandidateList = (com = 1, year?: number) =>
    fetchAllItems(
      `/promotion-candidate/${toQueryString({ company: com, limit: 500, eval_year: year })}`,
      allPromotionCandidateList,
    )

  const fetchPromotionCandidate = (pk: number) =>
    api
      .get(`/promotion-candidate/${pk}/`)
      .then(res => (promotionCandidate.value = res.data))
      .catch(err => errorHandle(err))

  const createPromotionCandidate = (
    payload: PromotionCandidate,
    page = 1,
    com = 1,
    filter?: PromotionCandidateFilter,
  ) =>
    mutateHr(
      () => api.post('/promotion-candidate/', payload),
      async pk => {
        await fetchAllPromotionCandidateList(com)
        await fetchPromotionCandidateList({ ...(filter ?? {}), page, com })
        if (pk) await fetchPromotionCandidate(pk)
      },
    )

  const updatePromotionCandidate = (
    payload: PromotionCandidate,
    page = 1,
    com = 1,
    filter?: PromotionCandidateFilter,
  ) =>
    mutateHr(
      () => api.put(`/promotion-candidate/${payload.pk}/`, payload),
      async pk => {
        await fetchAllPromotionCandidateList(com)
        await fetchPromotionCandidateList({ ...(filter ?? {}), page, com })
        if (pk) await fetchPromotionCandidate(pk)
      },
    )

  const deletePromotionCandidate = (pk: number, com = 1, filter?: PromotionCandidateFilter) =>
    mutateHr(
      () => api.delete(`/promotion-candidate/${pk}/`),
      async () => {
        await fetchAllPromotionCandidateList(com)
        await fetchPromotionCandidateList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  // Staff ------------------------------------------------------------
  const staffList = ref<Staff[]>([])
  const allStaffList = ref<Staff[]>([])
  const staff = ref<Staff | null>(null)
  const staffsCount = ref<number>(0)

  const getAllStaffs = computed(() =>
    allStaffList.value.map(s => ({
      value: s.pk,
      label: s.name,
    })),
  )

  // actions
  const staffPages = (itemsPerPage: number) => Math.ceil(staffsCount.value / itemsPerPage)

  const fetchAllStaffList = (com = 1, sts = '1') =>
    fetchAllItems(`/staff/${toQueryString({ company: com, limit: 500, status: sts })}`, allStaffList)

  const fetchStaffList = (payload: StaffFilter) => {
    const {
      page = 1,
      com = 1,
      sort = '',
      dep = '',
      gra = '',
      pos = '',
      dut = '',
      sts = '1',
      q = '',
    } = payload
    const queryStr = toQueryString({
      limit: 10,
      page,
      company: com,
      sort,
      department: dep,
      grade: gra,
      position: pos,
      duty: dut,
      status: sts,
      search: q,
    })
    return fetchPaged(`/staff/${queryStr}`, staffList, staffsCount)
  }

  const fetchStaff = (pk: number) =>
    api
      .get(`/staff/${pk}/`)
      .then(res => (staff.value = res.data))
      .catch(err => errorHandle(err))

  const createStaff = (payload: Staff, page = 1, com = 1, filter?: StaffFilter) =>
    mutateHr(
      () => api.post('/staff/', payload),
      async pk => {
        await fetchAllStaffList(com)
        await fetchStaffList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaff(pk)
      },
    )

  const updateStaff = (payload: Staff, page = 1, com = 1, filter?: StaffFilter) =>
    mutateHr(
      () => api.put(`/staff/${payload.pk}/`, payload),
      async pk => {
        await fetchAllStaffList(com)
        await fetchStaffList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaff(pk)
      },
    )

  const deleteStaff = (pk: number, com = 1, filter?: StaffFilter) =>
    mutateHr(
      () => api.delete(`/staff/${pk}/`),
      async () => {
        await fetchAllStaffList(com)
        await fetchStaffList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  // PersonnelOrder ---------------------------------------------------
  const personnelOrderList = ref<PersonnelOrder[]>([])
  const allPersonnelOrderList = ref<PersonnelOrder[]>([])
  const personnelOrder = ref<PersonnelOrder | null>(null)
  const personnelOrdersCount = ref<number>(0)

  const personnelOrderPages = (itemsPerPage: number) =>
    Math.ceil(personnelOrdersCount.value / itemsPerPage)

  const fetchPersonnelOrderList = (payload: PersonnelOrderFilter) => {
    const {
      page = 1,
      com = 1,
      staff: staffId = '',
      order_type = '',
      department = '',
      is_processed = '',
      q = '',
    } = payload
    const queryStr = toQueryString({
      limit: 10,
      page,
      company: com,
      staff: staffId,
      order_type,
      new_department: department,
      is_processed,
      search: q,
    })
    return fetchPaged(`/personnel-order/${queryStr}`, personnelOrderList, personnelOrdersCount)
  }

  const fetchAllPersonnelOrderList = (com = 1) =>
    fetchAllItems(
      `/personnel-order/${toQueryString({ company: com, limit: 500 })}`,
      allPersonnelOrderList,
    )

  const fetchPersonnelOrder = (pk: number) =>
    api
      .get(`/personnel-order/${pk}/`)
      .then(res => (personnelOrder.value = res.data))
      .catch(err => errorHandle(err))

  const createPersonnelOrder = (
    payload: PersonnelOrder,
    page = 1,
    com = 1,
    filter?: PersonnelOrderFilter,
  ) =>
    mutateHr(
      () => api.post('/personnel-order/', payload),
      async pk => {
        await fetchAllPersonnelOrderList(com)
        await fetchPersonnelOrderList({ ...(filter ?? {}), page, com })
        if (pk) await fetchPersonnelOrder(pk)
        // 직원 상태가 자동 반영될 수 있으므로 직원 목록도 갱신
        await fetchAllStaffList(com, '')
      },
    )

  const updatePersonnelOrder = (
    payload: PersonnelOrder,
    page = 1,
    com = 1,
    filter?: PersonnelOrderFilter,
  ) =>
    mutateHr(
      () => api.put(`/personnel-order/${payload.pk}/`, payload),
      async pk => {
        await fetchAllPersonnelOrderList(com)
        await fetchPersonnelOrderList({ ...(filter ?? {}), page, com })
        if (pk) await fetchPersonnelOrder(pk)
        await fetchAllStaffList(com, '')
      },
    )

  const deletePersonnelOrder = (pk: number, com = 1, filter?: PersonnelOrderFilter) =>
    mutateHr(
      () => api.delete(`/personnel-order/${pk}/`),
      async () => {
        await fetchAllPersonnelOrderList(com)
        await fetchPersonnelOrderList({ ...(filter ?? {}), page: 1, com })
        await fetchAllStaffList(com, '')
      },
      true,
    )

  // StaffCareer ------------------------------------------------------
  const staffCareerList = ref<StaffCareer[]>([])
  const allStaffCareerList = ref<StaffCareer[]>([])
  const staffCareer = ref<StaffCareer | null>(null)
  const staffCareersCount = ref<number>(0)

  const staffCareerPages = (itemsPerPage: number) =>
    Math.ceil(staffCareersCount.value / itemsPerPage)

  const fetchStaffCareerList = (payload: StaffRecordFilter) => {
    const { page = 1, com = 1, staff: staffId = '', q = '' } = payload
    const queryStr = toQueryString({
      limit: 10,
      page,
      company: com,
      staff: staffId,
      search: q,
    })
    return fetchPaged(`/staff-career/${queryStr}`, staffCareerList, staffCareersCount)
  }

  const fetchAllStaffCareerList = (com = 1, staffId?: number) =>
    fetchAllItems(
      `/staff-career/${toQueryString({ company: com, limit: 500, staff: staffId })}`,
      allStaffCareerList,
    )

  const fetchStaffCareer = (pk: number) =>
    api
      .get(`/staff-career/${pk}/`)
      .then(res => (staffCareer.value = res.data))
      .catch(err => errorHandle(err))

  const createStaffCareer = (
    payload: StaffCareer,
    page = 1,
    com = 1,
    filter?: StaffRecordFilter,
  ) =>
    mutateHr(
      () => api.post('/staff-career/', payload),
      async pk => {
        await fetchAllStaffCareerList(com)
        await fetchStaffCareerList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffCareer(pk)
      },
    )

  const updateStaffCareer = (
    payload: StaffCareer,
    page = 1,
    com = 1,
    filter?: StaffRecordFilter,
  ) =>
    mutateHr(
      () => api.put(`/staff-career/${payload.pk}/`, payload),
      async pk => {
        await fetchAllStaffCareerList(com)
        await fetchStaffCareerList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffCareer(pk)
      },
    )

  const deleteStaffCareer = (pk: number, com = 1, filter?: StaffRecordFilter) =>
    mutateHr(
      () => api.delete(`/staff-career/${pk}/`),
      async () => {
        await fetchAllStaffCareerList(com)
        await fetchStaffCareerList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  // StaffCertificate -------------------------------------------------
  const staffCertificateList = ref<StaffCertificate[]>([])
  const allStaffCertificateList = ref<StaffCertificate[]>([])
  const staffCertificate = ref<StaffCertificate | null>(null)
  const staffCertificatesCount = ref<number>(0)

  const staffCertificatePages = (itemsPerPage: number) =>
    Math.ceil(staffCertificatesCount.value / itemsPerPage)

  const fetchStaffCertificateList = (payload: StaffRecordFilter) => {
    const { page = 1, com = 1, staff: staffId = '', q = '' } = payload
    const queryStr = toQueryString({
      limit: 10,
      page,
      company: com,
      staff: staffId,
      search: q,
    })
    return fetchPaged(
      `/staff-certificate/${queryStr}`,
      staffCertificateList,
      staffCertificatesCount,
    )
  }

  const fetchAllStaffCertificateList = (com = 1, staffId?: number) =>
    fetchAllItems(
      `/staff-certificate/${toQueryString({ company: com, limit: 500, staff: staffId })}`,
      allStaffCertificateList,
    )

  const fetchStaffCertificate = (pk: number) =>
    api
      .get(`/staff-certificate/${pk}/`)
      .then(res => (staffCertificate.value = res.data))
      .catch(err => errorHandle(err))

  const createStaffCertificate = (
    payload: StaffCertificate,
    page = 1,
    com = 1,
    filter?: StaffRecordFilter,
  ) =>
    mutateHr(
      () => api.post('/staff-certificate/', payload),
      async pk => {
        await fetchAllStaffCertificateList(com)
        await fetchStaffCertificateList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffCertificate(pk)
      },
    )

  const updateStaffCertificate = (
    payload: StaffCertificate,
    page = 1,
    com = 1,
    filter?: StaffRecordFilter,
  ) =>
    mutateHr(
      () => api.put(`/staff-certificate/${payload.pk}/`, payload),
      async pk => {
        await fetchAllStaffCertificateList(com)
        await fetchStaffCertificateList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffCertificate(pk)
      },
    )

  const deleteStaffCertificate = (pk: number, com = 1, filter?: StaffRecordFilter) =>
    mutateHr(
      () => api.delete(`/staff-certificate/${pk}/`),
      async () => {
        await fetchAllStaffCertificateList(com)
        await fetchStaffCertificateList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  // StaffRewardPunishment --------------------------------------------
  const staffRewardPunishmentList = ref<StaffRewardPunishment[]>([])
  const allStaffRewardPunishmentList = ref<StaffRewardPunishment[]>([])
  const staffRewardPunishment = ref<StaffRewardPunishment | null>(null)
  const staffRewardPunishmentsCount = ref<number>(0)

  const staffRewardPunishmentPages = (itemsPerPage: number) =>
    Math.ceil(staffRewardPunishmentsCount.value / itemsPerPage)

  const fetchStaffRewardPunishmentList = (payload: StaffRecordFilter) => {
    const { page = 1, com = 1, staff: staffId = '', sort = '', q = '' } = payload
    const queryStr = toQueryString({
      limit: 10,
      page,
      company: com,
      staff: staffId,
      sort,
      search: q,
    })
    return fetchPaged(
      `/staff-reward-punishment/${queryStr}`,
      staffRewardPunishmentList,
      staffRewardPunishmentsCount,
    )
  }

  const fetchAllStaffRewardPunishmentList = (com = 1, staffId?: number) =>
    fetchAllItems(
      `/staff-reward-punishment/${toQueryString({ company: com, limit: 500, staff: staffId })}`,
      allStaffRewardPunishmentList,
    )

  const fetchStaffRewardPunishment = (pk: number) =>
    api
      .get(`/staff-reward-punishment/${pk}/`)
      .then(res => (staffRewardPunishment.value = res.data))
      .catch(err => errorHandle(err))

  const createStaffRewardPunishment = (
    payload: StaffRewardPunishment,
    page = 1,
    com = 1,
    filter?: StaffRecordFilter,
  ) =>
    mutateHr(
      () => api.post('/staff-reward-punishment/', payload),
      async pk => {
        await fetchAllStaffRewardPunishmentList(com)
        await fetchStaffRewardPunishmentList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffRewardPunishment(pk)
      },
    )

  const updateStaffRewardPunishment = (
    payload: StaffRewardPunishment,
    page = 1,
    com = 1,
    filter?: StaffRecordFilter,
  ) =>
    mutateHr(
      () => api.put(`/staff-reward-punishment/${payload.pk}/`, payload),
      async pk => {
        await fetchAllStaffRewardPunishmentList(com)
        await fetchStaffRewardPunishmentList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffRewardPunishment(pk)
      },
    )

  const deleteStaffRewardPunishment = (pk: number, com = 1, filter?: StaffRecordFilter) =>
    mutateHr(
      () => api.delete(`/staff-reward-punishment/${pk}/`),
      async () => {
        await fetchAllStaffRewardPunishmentList(com)
        await fetchStaffRewardPunishmentList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  // StaffLeaveQuota --------------------------------------------------
  const staffLeaveQuotaList = ref<StaffLeaveQuota[]>([])
  const allStaffLeaveQuotaList = ref<StaffLeaveQuota[]>([])
  const staffLeaveQuota = ref<StaffLeaveQuota | null>(null)
  const staffLeaveQuotasCount = ref<number>(0)

  const staffLeaveQuotaPages = (itemsPerPage: number) =>
    Math.ceil(staffLeaveQuotasCount.value / itemsPerPage)

  const fetchStaffLeaveQuotaList = (payload: StaffLeaveQuotaFilter) => {
    const { page = 1, com = 1, staff: staffId = '', year = '', q = '' } = payload
    const queryStr = toQueryString({
      limit: 10,
      page,
      company: com,
      staff: staffId,
      year,
      search: q,
    })
    return fetchPaged(
      `/staff-leave-quota/${queryStr}`,
      staffLeaveQuotaList,
      staffLeaveQuotasCount,
    )
  }

  const fetchAllStaffLeaveQuotaList = (com = 1, year?: number) =>
    fetchAllItems(
      `/staff-leave-quota/${toQueryString({ company: com, limit: 500, year })}`,
      allStaffLeaveQuotaList,
    )

  const fetchStaffLeaveQuota = (pk: number) =>
    api
      .get(`/staff-leave-quota/${pk}/`)
      .then(res => (staffLeaveQuota.value = res.data))
      .catch(err => errorHandle(err))

  const createStaffLeaveQuota = (
    payload: StaffLeaveQuota,
    page = 1,
    com = 1,
    filter?: StaffLeaveQuotaFilter,
  ) =>
    mutateHr(
      () => api.post('/staff-leave-quota/', payload),
      async pk => {
        await fetchAllStaffLeaveQuotaList(com)
        await fetchStaffLeaveQuotaList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffLeaveQuota(pk)
      },
    )

  const updateStaffLeaveQuota = (
    payload: StaffLeaveQuota,
    page = 1,
    com = 1,
    filter?: StaffLeaveQuotaFilter,
  ) =>
    mutateHr(
      () => api.put(`/staff-leave-quota/${payload.pk}/`, payload),
      async pk => {
        await fetchAllStaffLeaveQuotaList(com)
        await fetchStaffLeaveQuotaList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffLeaveQuota(pk)
      },
    )

  const deleteStaffLeaveQuota = (pk: number, com = 1, filter?: StaffLeaveQuotaFilter) =>
    mutateHr(
      () => api.delete(`/staff-leave-quota/${pk}/`),
      async () => {
        await fetchAllStaffLeaveQuotaList(com)
        await fetchStaffLeaveQuotaList({ ...(filter ?? {}), page: 1, com })
      },
      true,
    )

  // StaffLeaveUsage --------------------------------------------------
  const staffLeaveUsageList = ref<StaffLeaveUsage[]>([])
  const allStaffLeaveUsageList = ref<StaffLeaveUsage[]>([])
  const staffLeaveUsage = ref<StaffLeaveUsage | null>(null)
  const staffLeaveUsagesCount = ref<number>(0)

  const staffLeaveUsagePages = (itemsPerPage: number) =>
    Math.ceil(staffLeaveUsagesCount.value / itemsPerPage)

  const fetchStaffLeaveUsageList = (payload: StaffLeaveUsageFilter) => {
    const {
      page = 1,
      com = 1,
      staff: staffId = '',
      leave_type = '',
      start_date = '',
      end_date = '',
      is_cancelled = '',
      q = '',
    } = payload
    const queryStr = toQueryString({
      limit: 10,
      page,
      company: com,
      staff: staffId,
      leave_type,
      start_date,
      end_date,
      is_cancelled,
      search: q,
    })
    return fetchPaged(
      `/staff-leave-usage/${queryStr}`,
      staffLeaveUsageList,
      staffLeaveUsagesCount,
    )
  }

  const fetchAllStaffLeaveUsageList = (com = 1, staffId?: number) =>
    fetchAllItems(
      `/staff-leave-usage/${toQueryString({ company: com, limit: 500, staff: staffId })}`,
      allStaffLeaveUsageList,
    )

  const fetchStaffLeaveUsage = (pk: number) =>
    api
      .get(`/staff-leave-usage/${pk}/`)
      .then(res => (staffLeaveUsage.value = res.data))
      .catch(err => errorHandle(err))

  const createStaffLeaveUsage = (
    payload: StaffLeaveUsage,
    page = 1,
    com = 1,
    filter?: StaffLeaveUsageFilter,
  ) =>
    mutateHr(
      () => api.post('/staff-leave-usage/', payload),
      async pk => {
        await fetchAllStaffLeaveUsageList(com)
        await fetchStaffLeaveUsageList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffLeaveUsage(pk)
        // 연차 잔여일수 갱신을 위해 Quota 목록도 재조회
        await fetchAllStaffLeaveQuotaList(com)
        await fetchStaffLeaveQuotaList({ com })
      },
    )

  const updateStaffLeaveUsage = (
    payload: StaffLeaveUsage,
    page = 1,
    com = 1,
    filter?: StaffLeaveUsageFilter,
  ) =>
    mutateHr(
      () => api.put(`/staff-leave-usage/${payload.pk}/`, payload),
      async pk => {
        await fetchAllStaffLeaveUsageList(com)
        await fetchStaffLeaveUsageList({ ...(filter ?? {}), page, com })
        if (pk) await fetchStaffLeaveUsage(pk)
        // 연차 잔여일수 갱신을 위해 Quota 목록도 재조회
        await fetchAllStaffLeaveQuotaList(com)
        await fetchStaffLeaveQuotaList({ com })
      },
    )

  const deleteStaffLeaveUsage = (pk: number, com = 1, filter?: StaffLeaveUsageFilter) =>
    mutateHr(
      () => api.delete(`/staff-leave-usage/${pk}/`),
      async () => {
        await fetchAllStaffLeaveUsageList(com)
        await fetchStaffLeaveUsageList({ ...(filter ?? {}), page: 1, com })
        // 연차 잔여일수 갱신을 위해 Quota 목록도 재조회
        await fetchAllStaffLeaveQuotaList(com)
        await fetchStaffLeaveQuotaList({ com })
      },
      true,
    )

  return {
    companyList,
    company,
    initComId,
    comSelect,
    fetchCompanyList,
    fetchCompany,
    removeCompany,
    createCompany,
    updateCompany,
    deleteCompany,

    logo,
    fetchLogo,
    createLogo,
    updateLogo,
    deleteLogo,

    departmentList,
    department,
    departmentsCount,
    allDepartList,
    getPkDeparts,
    getSlugDeparts,
    getUpperDeps,
    departmentPages,
    fetchDepartmentList,
    fetchAllDepartList,
    fetchDepartment,
    createDepartment,
    updateDepartment,
    deleteDepartment,

    gradeList,
    allGradeList,
    grade,
    gradesCount,
    getGrades,
    getPkGrades,
    gradePages,
    fetchGradeList,
    fetchAllGradeList,
    fetchGrade,
    createGrade,
    updateGrade,
    deleteGrade,

    positionList,
    allPositionList,
    position,
    positionsCount,
    getPositions,
    getPkPositions,
    positionPages,
    fetchPositionList,
    fetchAllPositionList,
    fetchPosition,
    createPosition,
    updatePosition,
    deletePosition,

    dutyList,
    allDutyList,
    duty,
    dutysCount,
    getDutys,
    getPkDutys,
    dutyPages,
    fetchDutyList,
    fetchAllDutyList,
    fetchDuty,
    createDuty,
    updateDuty,
    deleteDuty,

    executiveRankList,
    allExecutiveRankList,
    executiveRank,
    executiveRanksCount,
    getExecutiveRanks,
    getPkExecutiveRanks,
    executiveRankPages,
    fetchExecutiveRankList,
    fetchAllExecutiveRankList,
    fetchExecutiveRank,
    createExecutiveRank,
    updateExecutiveRank,
    deleteExecutiveRank,

    executiveList,
    allExecutiveList,
    executive,
    executivesCount,
    executivePages,
    fetchExecutiveList,
    fetchAllExecutiveList,
    fetchExecutive,
    createExecutive,
    updateExecutive,
    deleteExecutive,

    promotionPolicyList,
    allPromotionPolicyList,
    promotionPolicy,
    promotionPoliciesCount,
    promotionPolicyPages,
    fetchPromotionPolicyList,
    fetchAllPromotionPolicyList,
    fetchPromotionPolicy,
    createPromotionPolicy,
    updatePromotionPolicy,
    deletePromotionPolicy,

    staffEvaluationList,
    allStaffEvaluationList,
    staffEvaluation,
    staffEvaluationsCount,
    staffEvaluationPages,
    fetchStaffEvaluationList,
    fetchAllStaffEvaluationList,
    fetchStaffEvaluation,
    createStaffEvaluation,
    updateStaffEvaluation,
    deleteStaffEvaluation,

    promotionCandidateList,
    allPromotionCandidateList,
    promotionCandidate,
    promotionCandidatesCount,
    promotionCandidatePages,
    fetchPromotionCandidateList,
    fetchAllPromotionCandidateList,
    fetchPromotionCandidate,
    createPromotionCandidate,
    updatePromotionCandidate,
    deletePromotionCandidate,

    staffList,
    allStaffList,
    staff,
    staffsCount,
    getAllStaffs,
    staffPages,
    fetchStaffList,
    fetchAllStaffList,
    fetchStaff,
    createStaff,
    updateStaff,
    deleteStaff,

    personnelOrderList,
    allPersonnelOrderList,
    personnelOrder,
    personnelOrdersCount,
    personnelOrderPages,
    fetchPersonnelOrderList,
    fetchAllPersonnelOrderList,
    fetchPersonnelOrder,
    createPersonnelOrder,
    updatePersonnelOrder,
    deletePersonnelOrder,

    // StaffCareer
    staffCareerList,
    allStaffCareerList,
    staffCareer,
    staffCareersCount,
    staffCareerPages,
    fetchStaffCareerList,
    fetchAllStaffCareerList,
    fetchStaffCareer,
    createStaffCareer,
    updateStaffCareer,
    deleteStaffCareer,

    // StaffCertificate
    staffCertificateList,
    allStaffCertificateList,
    staffCertificate,
    staffCertificatesCount,
    staffCertificatePages,
    fetchStaffCertificateList,
    fetchAllStaffCertificateList,
    fetchStaffCertificate,
    createStaffCertificate,
    updateStaffCertificate,
    deleteStaffCertificate,

    // StaffRewardPunishment
    staffRewardPunishmentList,
    allStaffRewardPunishmentList,
    staffRewardPunishment,
    staffRewardPunishmentsCount,
    staffRewardPunishmentPages,
    fetchStaffRewardPunishmentList,
    fetchAllStaffRewardPunishmentList,
    fetchStaffRewardPunishment,
    createStaffRewardPunishment,
    updateStaffRewardPunishment,
    deleteStaffRewardPunishment,

    // StaffLeaveQuota
    staffLeaveQuotaList,
    allStaffLeaveQuotaList,
    staffLeaveQuota,
    staffLeaveQuotasCount,
    staffLeaveQuotaPages,
    fetchStaffLeaveQuotaList,
    fetchAllStaffLeaveQuotaList,
    fetchStaffLeaveQuota,
    createStaffLeaveQuota,
    updateStaffLeaveQuota,
    deleteStaffLeaveQuota,

    // StaffLeaveUsage
    staffLeaveUsageList,
    allStaffLeaveUsageList,
    staffLeaveUsage,
    staffLeaveUsagesCount,
    staffLeaveUsagePages,
    fetchStaffLeaveUsageList,
    fetchAllStaffLeaveUsageList,
    fetchStaffLeaveUsage,
    createStaffLeaveUsage,
    updateStaffLeaveUsage,
    deleteStaffLeaveUsage,

    // CompanySeal
    sealList,
    seal,
    fetchCompanySealList,
    fetchCompanySeal,
    createCompanySeal,
    updateCompanySeal,
    deleteCompanySeal,
  }
})
