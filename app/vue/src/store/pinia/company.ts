import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { errorHandle, message } from '@/utils/helper'
import { type Company, type Logo } from '@/store/types/settings'
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
  type StaffEvaluation,
  type PromotionCandidate,
  type PersonnelOrder,
  type PersonnelOrderFilter,
  type StaffCareer,
  type StaffCertificate,
  type StaffRewardPunishment,
  type StaffRecordFilter,
  type StaffLeaveQuota,
  type StaffLeaveQuotaFilter,
  type ComFilter,
} from '@/store/types/company'

export const useCompany = defineStore('company', () => {
  const accountStore = useAccount()

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
      .catch(err => errorHandle(err.response.data))

  const fetchCompany = async (pk: number) => {
    try {
      const res = await api.get(`/company/${pk}/`)
      company.value = res.data
      // Update the localStorage to prevent future errors
      localStorage.setItem('curr-company', res.data.pk.toString())
      console.log(`Switched to company: ${res.data.name} (ID: ${res.data.pk})`)
    } catch (err: any) {
      console.warn(`Company with ID ${pk} not found, trying to fetch first available company`)

      // If company fetch fails, try to get the first available company
      try {
        const companyListRes = await api.get('/company/')
        if (companyListRes.data.results && companyListRes.data.results.length > 0) {
          const firstCompany = companyListRes.data.results[0]
          company.value = firstCompany

          // Update the localStorage to prevent future errors
          localStorage.setItem('curr-company', firstCompany.pk.toString())
          console.log(`Switched to company: ${firstCompany.name} (ID: ${firstCompany.pk})`)
        } else {
          errorHandle(err.response?.data || { detail: 'No companies available' })
        }
      } catch (fallbackErr: any) {
        errorHandle(fallbackErr.response?.data || { detail: 'Failed to fetch companies' })
      }
    }
  }

  const removeCompany = () => (company.value = null)

  const createCompany = (payload: Company) =>
    api
      .post(`/company/`, payload)
      .then(res => fetchCompanyList().then(() => fetchCompany(res.data.pk).then(() => message())))
      .catch(err => errorHandle(err.response.data))

  const updateCompany = (payload: Company) =>
    api
      .put(`/company/${payload.pk}/`, payload)
      .then(res => fetchCompany(res.data.pk).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const deleteCompany = (pk: number) =>
    api
      .delete(`/company/${pk}/`)
      .then(() =>
        fetchCompanyList().then(() => message('warning', '', '해당 오브젝트가 삭제되었습니다.')),
      )
      .catch(err => errorHandle(err.response.data))

  // states & getters
  const logo = ref<Logo | null>(null)

  const fetchLogo = (pk: number) =>
    api
      .get(`/logo/${pk}/`)
      .then(res => (logo.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createLogo = (payload: Logo) =>
    api
      .post(`/logo/`, payload)
      .then(res => fetchLogo(res.data.pk).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const updateLogo = (payload: Logo) =>
    api
      .put(`/logo/${payload.pk}/`, payload)
      .then(res => fetchLogo(res.data.pk).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const deleteLogo = (pk: number) =>
    api
      .delete(`/logo/${pk}/`)
      .then(() => message('warning', '', '해당 오브젝트가 삭제되었습니다.'))
      .catch(err => errorHandle(err.response.data))

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

  const fetchDepartmentList = async (payload: DepFilter) => {
    const { page = 1, com = 1, upp = '', q = '' } = payload
    const queryStr = `?limit=10&page=${page}&company=${com}&upper_depart=${upp}&search=${q}`

    return await api
      .get(`/department/${queryStr}`)
      .then(res => {
        departmentList.value = res.data.results
        departmentsCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllDepartList = (com = 1) =>
    api
      .get(`/department/?company=${com}`)
      .then(res => {
        allDepartList.value = res.data.results
      })
      .catch(err => errorHandle(err.response.data))

  const fetchDepartment = (pk: number) =>
    api
      .get(`/department/${pk}/`)
      .then(res => (department.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createDepartment = (payload: Department, page = 1, com = 1) =>
    api
      .post(`/department/`, payload)
      .then(async res => {
        await fetchAllDepartList(com)
        await fetchDepartmentList({ page, com })
        await fetchDepartment(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateDepartment = (payload: Department, page = 1, com = 1) =>
    api
      .put(`/department/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllDepartList(com)
        await fetchDepartmentList({ page, com })
        await fetchDepartment(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteDepartment = (pk: number, com = 1) =>
    api
      .delete(`/department/${pk}/`)
      .then(async () => {
        await fetchAllDepartList(com)
        await fetchDepartmentList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

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

  const fetchGradeList = async (payload: ComFilter) => {
    const { page = 1, com = 1, q = '' } = payload
    const queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    return await api
      .get(`/grade/${queryStr}`)
      .then(res => {
        gradeList.value = res.data.results
        gradesCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllGradeList = (com = 1) =>
    api
      .get(`/grade/?company=${com}`)
      .then(res => {
        allGradeList.value = res.data.results
      })
      .catch(err => errorHandle(err.response.data))

  const fetchGrade = (pk: number) =>
    api
      .get(`/grade/${pk}/`)
      .then(res => (grade.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createGrade = (payload: Grade, page = 1, com = 1) =>
    api
      .post(`/grade/`, payload)
      .then(async res => {
        await fetchAllGradeList(com)
        await fetchGradeList({ page, com })
        await fetchGrade(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateGrade = (payload: Grade, page = 1, com = 1) =>
    api
      .put(`/grade/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllGradeList(com)
        await fetchGradeList({ page, com })
        await fetchGrade(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteGrade = (pk: number, com = 1) =>
    api
      .delete(`/grade/${pk}/`)
      .then(async () => {
        await fetchAllGradeList(com)
        await fetchGradeList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

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

  const fetchPositionList = async (payload: ComFilter) => {
    const { page = 1, com = 1, q = '' } = payload
    const queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    return await api
      .get(`/position/${queryStr}`)
      .then(res => {
        positionList.value = res.data.results
        positionsCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllPositionList = (com = 1) =>
    api
      .get(`/position/?company=${com}`)
      .then(res => {
        allPositionList.value = res.data.results
      })
      .catch(err => errorHandle(err.response.data))

  const fetchPosition = (pk: number) =>
    api
      .get(`/position/${pk}/`)
      .then(res => (position.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createPosition = (payload: Position, page = 1, com = 1) =>
    api
      .post(`/position/`, payload)
      .then(async res => {
        await fetchAllPositionList(com)
        await fetchPositionList({ page, com })
        await fetchPosition(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updatePosition = (payload: Position, page = 1, com = 1) =>
    api
      .put(`/position/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllPositionList(com)
        await fetchPositionList({ page, com })
        await fetchPosition(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deletePosition = (pk: number, com = 1) =>
    api
      .delete(`/position/${pk}/`)
      .then(async () => {
        await fetchAllPositionList(com)
        await fetchPositionList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

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

  const fetchDutyList = async (payload: ComFilter) => {
    const { page = 1, com = 1, q = '' } = payload
    const queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    return await api
      .get(`/duty-title/${queryStr}`)
      .then(res => {
        dutyList.value = res.data.results
        dutysCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllDutyList = (com = 1) =>
    api
      .get(`/duty-title/?company=${com}`)
      .then(res => {
        allDutyList.value = res.data.results
      })
      .catch(err => errorHandle(err.response.data))

  const fetchDuty = (pk: number) =>
    api
      .get(`/duty-title/${pk}/`)
      .then(res => (duty.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createDuty = (payload: Duty, page = 1, com = 1) =>
    api
      .post(`/duty-title/`, payload)
      .then(async res => {
        await fetchAllDutyList(com)
        await fetchDutyList({ page, com })
        await fetchDuty(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateDuty = (payload: Duty, page = 1, com = 1) =>
    api
      .put(`/duty-title/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllDutyList(com)
        await fetchDutyList({ page, com })
        await fetchDuty(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteDuty = (pk: number, com = 1) =>
    api
      .delete(`/duty-title/${pk}/`)
      .then(async () => {
        await fetchAllDutyList(com)
        await fetchDutyList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

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

  const fetchExecutiveRankList = async (payload: ComFilter) => {
    const { page = 1, com = 1, q = '' } = payload
    const queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    return await api
      .get(`/executive-rank/${queryStr}`)
      .then(res => {
        executiveRankList.value = res.data.results
        executiveRanksCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllExecutiveRankList = (com = 1) =>
    api
      .get(`/executive-rank/?company=${com}&limit=500`)
      .then(res => {
        allExecutiveRankList.value = res.data.results ?? res.data
      })
      .catch(err => errorHandle(err.response.data))

  const fetchExecutiveRank = (pk: number) =>
    api
      .get(`/executive-rank/${pk}/`)
      .then(res => (executiveRank.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createExecutiveRank = (payload: ExecutiveRank, page = 1, com = 1) =>
    api
      .post(`/executive-rank/`, payload)
      .then(async res => {
        await fetchAllExecutiveRankList(com)
        await fetchExecutiveRankList({ page, com })
        await fetchExecutiveRank(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateExecutiveRank = (payload: ExecutiveRank, page = 1, com = 1) =>
    api
      .put(`/executive-rank/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllExecutiveRankList(com)
        await fetchExecutiveRankList({ page, com })
        await fetchExecutiveRank(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteExecutiveRank = (pk: number, com = 1) =>
    api
      .delete(`/executive-rank/${pk}/`)
      .then(async () => {
        await fetchAllExecutiveRankList(com)
        await fetchExecutiveRankList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // Executive --------------------------------------------------------
  const executiveList = ref<Executive[]>([])
  const allExecutiveList = ref<Executive[]>([])
  const executive = ref<Executive | null>(null)
  const executivesCount = ref<number>(0)

  const executivePages = (itemsPerPage: number) => Math.ceil(executivesCount.value / itemsPerPage)

  const fetchExecutiveList = async (payload: ExecutiveFilter) => {
    const {
      page = 1,
      com = 1,
      rank = '',
      director_type = '',
      is_registered = '',
      is_standing = '',
      represent_type = '',
      q = '',
    } = payload
    let queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    if (rank) queryStr += `&rank=${rank}`
    if (director_type) queryStr += `&director_type=${director_type}`
    if (is_registered !== '') queryStr += `&is_registered=${is_registered}`
    if (is_standing !== '') queryStr += `&is_standing=${is_standing}`
    if (represent_type) queryStr += `&represent_type=${represent_type}`

    return await api
      .get(`/executive/${queryStr}`)
      .then(res => {
        executiveList.value = res.data.results
        executivesCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllExecutiveList = (com = 1) =>
    api
      .get(`/executive/?company=${com}&limit=500`)
      .then(res => {
        allExecutiveList.value = res.data.results ?? res.data
      })
      .catch(err => errorHandle(err.response.data))

  const fetchExecutive = (pk: number) =>
    api
      .get(`/executive/${pk}/`)
      .then(res => (executive.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createExecutive = (payload: Executive, page = 1, com = 1) =>
    api
      .post(`/executive/`, payload)
      .then(async res => {
        await fetchAllExecutiveList(com)
        await fetchExecutiveList({ page, com })
        await fetchExecutive(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateExecutive = (payload: Executive, page = 1, com = 1) =>
    api
      .put(`/executive/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllExecutiveList(com)
        await fetchExecutiveList({ page, com })
        await fetchExecutive(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteExecutive = (pk: number, com = 1) =>
    api
      .delete(`/executive/${pk}/`)
      .then(async () => {
        await fetchAllExecutiveList(com)
        await fetchExecutiveList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // PromotionPolicy --------------------------------------------------
  const promotionPolicyList = ref<PromotionPolicy[]>([])
  const allPromotionPolicyList = ref<PromotionPolicy[]>([])
  const promotionPolicy = ref<PromotionPolicy | null>(null)
  const promotionPoliciesCount = ref<number>(0)

  const promotionPolicyPages = (itemsPerPage: number) =>
    Math.ceil(promotionPoliciesCount.value / itemsPerPage)

  const fetchPromotionPolicyList = async (payload: ComFilter) => {
    const { page = 1, com = 1, q = '' } = payload
    const queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    return await api
      .get(`/promotion-policy/${queryStr}`)
      .then(res => {
        promotionPolicyList.value = res.data.results
        promotionPoliciesCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllPromotionPolicyList = (com = 1) =>
    api
      .get(`/promotion-policy/?company=${com}&limit=500`)
      .then(res => {
        allPromotionPolicyList.value = res.data.results ?? res.data
      })
      .catch(err => errorHandle(err.response.data))

  const fetchPromotionPolicy = (pk: number) =>
    api
      .get(`/promotion-policy/${pk}/`)
      .then(res => (promotionPolicy.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createPromotionPolicy = (payload: PromotionPolicy, page = 1, com = 1) =>
    api
      .post(`/promotion-policy/`, payload)
      .then(async res => {
        await fetchAllPromotionPolicyList(com)
        await fetchPromotionPolicyList({ page, com })
        await fetchPromotionPolicy(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updatePromotionPolicy = (payload: PromotionPolicy, page = 1, com = 1) =>
    api
      .put(`/promotion-policy/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllPromotionPolicyList(com)
        await fetchPromotionPolicyList({ page, com })
        await fetchPromotionPolicy(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deletePromotionPolicy = (pk: number, com = 1) =>
    api
      .delete(`/promotion-policy/${pk}/`)
      .then(async () => {
        await fetchAllPromotionPolicyList(com)
        await fetchPromotionPolicyList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // StaffEvaluation --------------------------------------------------
  const staffEvaluationList = ref<StaffEvaluation[]>([])
  const allStaffEvaluationList = ref<StaffEvaluation[]>([])
  const staffEvaluation = ref<StaffEvaluation | null>(null)
  const staffEvaluationsCount = ref<number>(0)

  const staffEvaluationPages = (itemsPerPage: number) =>
    Math.ceil(staffEvaluationsCount.value / itemsPerPage)

  const fetchStaffEvaluationList = async (
    payload: ComFilter & { staff?: number; year?: number },
  ) => {
    const { page = 1, com = 1, q = '', staff: staffId, year } = payload
    let queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    if (staffId) queryStr += `&staff=${staffId}`
    if (year) queryStr += `&eval_year=${year}`
    return await api
      .get(`/staff-evaluation/${queryStr}`)
      .then(res => {
        staffEvaluationList.value = res.data.results
        staffEvaluationsCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllStaffEvaluationList = (com = 1, year?: number) => {
    let queryStr = `?company=${com}&limit=500`
    if (year) queryStr += `&eval_year=${year}`
    return api
      .get(`/staff-evaluation/${queryStr}`)
      .then(res => {
        allStaffEvaluationList.value = res.data.results ?? res.data
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchStaffEvaluation = (pk: number) =>
    api
      .get(`/staff-evaluation/${pk}/`)
      .then(res => (staffEvaluation.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createStaffEvaluation = (payload: StaffEvaluation, page = 1, com = 1) =>
    api
      .post(`/staff-evaluation/`, payload)
      .then(async res => {
        await fetchAllStaffEvaluationList(com)
        await fetchStaffEvaluationList({ page, com })
        await fetchStaffEvaluation(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateStaffEvaluation = (payload: StaffEvaluation, page = 1, com = 1) =>
    api
      .put(`/staff-evaluation/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllStaffEvaluationList(com)
        await fetchStaffEvaluationList({ page, com })
        await fetchStaffEvaluation(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteStaffEvaluation = (pk: number, com = 1) =>
    api
      .delete(`/staff-evaluation/${pk}/`)
      .then(async () => {
        await fetchAllStaffEvaluationList(com)
        await fetchStaffEvaluationList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // PromotionCandidate -----------------------------------------------
  const promotionCandidateList = ref<PromotionCandidate[]>([])
  const allPromotionCandidateList = ref<PromotionCandidate[]>([])
  const promotionCandidate = ref<PromotionCandidate | null>(null)
  const promotionCandidatesCount = ref<number>(0)

  const promotionCandidatePages = (itemsPerPage: number) =>
    Math.ceil(promotionCandidatesCount.value / itemsPerPage)

  const fetchPromotionCandidateList = async (
    payload: ComFilter & { year?: number; status?: string },
  ) => {
    const { page = 1, com = 1, q = '', year, status: candStatus } = payload
    let queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    if (year) queryStr += `&eval_year=${year}`
    if (candStatus) queryStr += `&status=${candStatus}`
    return await api
      .get(`/promotion-candidate/${queryStr}`)
      .then(res => {
        promotionCandidateList.value = res.data.results
        promotionCandidatesCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllPromotionCandidateList = (com = 1, year?: number) => {
    let queryStr = `?company=${com}&limit=500`
    if (year) queryStr += `&eval_year=${year}`
    return api
      .get(`/promotion-candidate/${queryStr}`)
      .then(res => {
        allPromotionCandidateList.value = res.data.results ?? res.data
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchPromotionCandidate = (pk: number) =>
    api
      .get(`/promotion-candidate/${pk}/`)
      .then(res => (promotionCandidate.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createPromotionCandidate = (payload: PromotionCandidate, page = 1, com = 1) =>
    api
      .post(`/promotion-candidate/`, payload)
      .then(async res => {
        await fetchAllPromotionCandidateList(com)
        await fetchPromotionCandidateList({ page, com })
        await fetchPromotionCandidate(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updatePromotionCandidate = (payload: PromotionCandidate, page = 1, com = 1) =>
    api
      .put(`/promotion-candidate/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllPromotionCandidateList(com)
        await fetchPromotionCandidateList({ page, com })
        await fetchPromotionCandidate(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deletePromotionCandidate = (pk: number, com = 1) =>
    api
      .delete(`/promotion-candidate/${pk}/`)
      .then(async () => {
        await fetchAllPromotionCandidateList(com)
        await fetchPromotionCandidateList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

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

  const fetchAllStaffList = (com = 1) =>
    api
      .get(`/staff/?company=${com}&limit=500&status=1`)
      .then(res => {
        allStaffList.value = res.data.results ?? res.data
      })
      .catch(err => errorHandle(err.response.data))

  const fetchStaffList = async (payload: StaffFilter) => {
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
    const qStr = `?page=${page}&company=${com}&sort=${sort}&department=${dep}&grade=${gra}&position=${pos}&duty=${dut}&status=${sts}&search=${q}`

    return await api
      .get(`/staff/${qStr}`)
      .then(res => {
        staffList.value = res.data.results
        staffsCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchStaff = (pk: number) =>
    api
      .get(`/staff/${pk}/`)
      .then(res => (staff.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createStaff = (payload: Staff, page = 1, com = 1) =>
    api
      .post(`/staff/`, payload)
      .then(res =>
        fetchStaffList({ page, com }).then(() => fetchStaff(res.data.pk).then(() => message())),
      )
      .catch(err => errorHandle(err.response.data))

  const updateStaff = (payload: Staff, page = 1, com = 1) =>
    api
      .put(`/staff/${payload.pk}/`, payload)
      .then(res => {
        fetchStaffList({ page, com }).then(() => fetchStaff(res.data.pk).then(() => message()))
      })
      .catch(err => errorHandle(err.response.data))

  const deleteStaff = (pk: number, com = 1) =>
    api
      .delete(`/staff/${pk}/`)
      .then(() =>
        fetchStaffList({ com }).then(() =>
          message('warning', '', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  // PersonnelOrder ---------------------------------------------------
  const personnelOrderList = ref<PersonnelOrder[]>([])
  const allPersonnelOrderList = ref<PersonnelOrder[]>([])
  const personnelOrder = ref<PersonnelOrder | null>(null)
  const personnelOrdersCount = ref<number>(0)

  const personnelOrderPages = (itemsPerPage: number) =>
    Math.ceil(personnelOrdersCount.value / itemsPerPage)

  const fetchPersonnelOrderList = async (payload: PersonnelOrderFilter) => {
    const {
      page = 1,
      com = 1,
      staff: staffId = '',
      order_type = '',
      department = '',
      is_processed = '',
      q = '',
    } = payload
    let queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    if (staffId) queryStr += `&staff=${staffId}`
    if (order_type) queryStr += `&order_type=${order_type}`
    if (department) queryStr += `&new_department=${department}`
    if (is_processed !== '') queryStr += `&is_processed=${is_processed}`

    return await api
      .get(`/personnel-order/${queryStr}`)
      .then(res => {
        personnelOrderList.value = res.data.results
        personnelOrdersCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllPersonnelOrderList = (com = 1) =>
    api
      .get(`/personnel-order/?company=${com}&limit=500`)
      .then(res => {
        allPersonnelOrderList.value = res.data.results ?? res.data
      })
      .catch(err => errorHandle(err.response.data))

  const fetchPersonnelOrder = (pk: number) =>
    api
      .get(`/personnel-order/${pk}/`)
      .then(res => (personnelOrder.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createPersonnelOrder = (payload: PersonnelOrder, page = 1, com = 1) =>
    api
      .post(`/personnel-order/`, payload)
      .then(async res => {
        await fetchAllPersonnelOrderList(com)
        await fetchPersonnelOrderList({ page, com })
        await fetchPersonnelOrder(res.data.pk)
        // 직원 상태가 자동 반영될 수 있으므로 직원 목록도 갱신
        await fetchAllStaffList(com)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updatePersonnelOrder = (payload: PersonnelOrder, page = 1, com = 1) =>
    api
      .put(`/personnel-order/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllPersonnelOrderList(com)
        await fetchPersonnelOrderList({ page, com })
        await fetchPersonnelOrder(res.data.pk)
        await fetchAllStaffList(com)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deletePersonnelOrder = (pk: number, com = 1) =>
    api
      .delete(`/personnel-order/${pk}/`)
      .then(async () => {
        await fetchAllPersonnelOrderList(com)
        await fetchPersonnelOrderList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // StaffCareer ------------------------------------------------------
  const staffCareerList = ref<StaffCareer[]>([])
  const allStaffCareerList = ref<StaffCareer[]>([])
  const staffCareer = ref<StaffCareer | null>(null)
  const staffCareersCount = ref<number>(0)

  const staffCareerPages = (itemsPerPage: number) =>
    Math.ceil(staffCareersCount.value / itemsPerPage)

  const fetchStaffCareerList = async (payload: StaffRecordFilter) => {
    const { page = 1, com = 1, staff: staffId = '', q = '' } = payload
    let queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    if (staffId) queryStr += `&staff=${staffId}`

    return await api
      .get(`/staff-career/${queryStr}`)
      .then(res => {
        staffCareerList.value = res.data.results
        staffCareersCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllStaffCareerList = (com = 1, staffId?: number) => {
    let queryStr = `?company=${com}&limit=500`
    if (staffId) queryStr += `&staff=${staffId}`
    return api
      .get(`/staff-career/${queryStr}`)
      .then(res => {
        allStaffCareerList.value = res.data.results ?? res.data
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchStaffCareer = (pk: number) =>
    api
      .get(`/staff-career/${pk}/`)
      .then(res => (staffCareer.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createStaffCareer = (payload: StaffCareer, page = 1, com = 1) =>
    api
      .post(`/staff-career/`, payload)
      .then(async res => {
        await fetchAllStaffCareerList(com)
        await fetchStaffCareerList({ page, com })
        await fetchStaffCareer(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateStaffCareer = (payload: StaffCareer, page = 1, com = 1) =>
    api
      .put(`/staff-career/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllStaffCareerList(com)
        await fetchStaffCareerList({ page, com })
        await fetchStaffCareer(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteStaffCareer = (pk: number, com = 1) =>
    api
      .delete(`/staff-career/${pk}/`)
      .then(async () => {
        await fetchAllStaffCareerList(com)
        await fetchStaffCareerList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // StaffCertificate -------------------------------------------------
  const staffCertificateList = ref<StaffCertificate[]>([])
  const allStaffCertificateList = ref<StaffCertificate[]>([])
  const staffCertificate = ref<StaffCertificate | null>(null)
  const staffCertificatesCount = ref<number>(0)

  const staffCertificatePages = (itemsPerPage: number) =>
    Math.ceil(staffCertificatesCount.value / itemsPerPage)

  const fetchStaffCertificateList = async (payload: StaffRecordFilter) => {
    const { page = 1, com = 1, staff: staffId = '', q = '' } = payload
    let queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    if (staffId) queryStr += `&staff=${staffId}`

    return await api
      .get(`/staff-certificate/${queryStr}`)
      .then(res => {
        staffCertificateList.value = res.data.results
        staffCertificatesCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllStaffCertificateList = (com = 1, staffId?: number) => {
    let queryStr = `?company=${com}&limit=500`
    if (staffId) queryStr += `&staff=${staffId}`
    return api
      .get(`/staff-certificate/${queryStr}`)
      .then(res => {
        allStaffCertificateList.value = res.data.results ?? res.data
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchStaffCertificate = (pk: number) =>
    api
      .get(`/staff-certificate/${pk}/`)
      .then(res => (staffCertificate.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createStaffCertificate = (payload: StaffCertificate, page = 1, com = 1) =>
    api
      .post(`/staff-certificate/`, payload)
      .then(async res => {
        await fetchAllStaffCertificateList(com)
        await fetchStaffCertificateList({ page, com })
        await fetchStaffCertificate(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateStaffCertificate = (payload: StaffCertificate, page = 1, com = 1) =>
    api
      .put(`/staff-certificate/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllStaffCertificateList(com)
        await fetchStaffCertificateList({ page, com })
        await fetchStaffCertificate(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteStaffCertificate = (pk: number, com = 1) =>
    api
      .delete(`/staff-certificate/${pk}/`)
      .then(async () => {
        await fetchAllStaffCertificateList(com)
        await fetchStaffCertificateList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // StaffRewardPunishment --------------------------------------------
  const staffRewardPunishmentList = ref<StaffRewardPunishment[]>([])
  const allStaffRewardPunishmentList = ref<StaffRewardPunishment[]>([])
  const staffRewardPunishment = ref<StaffRewardPunishment | null>(null)
  const staffRewardPunishmentsCount = ref<number>(0)

  const staffRewardPunishmentPages = (itemsPerPage: number) =>
    Math.ceil(staffRewardPunishmentsCount.value / itemsPerPage)

  const fetchStaffRewardPunishmentList = async (payload: StaffRecordFilter) => {
    const { page = 1, com = 1, staff: staffId = '', sort = '', q = '' } = payload
    let queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    if (staffId) queryStr += `&staff=${staffId}`
    if (sort) queryStr += `&sort=${sort}`

    return await api
      .get(`/staff-reward-punishment/${queryStr}`)
      .then(res => {
        staffRewardPunishmentList.value = res.data.results
        staffRewardPunishmentsCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllStaffRewardPunishmentList = (com = 1, staffId?: number) => {
    let queryStr = `?company=${com}&limit=500`
    if (staffId) queryStr += `&staff=${staffId}`
    return api
      .get(`/staff-reward-punishment/${queryStr}`)
      .then(res => {
        allStaffRewardPunishmentList.value = res.data.results ?? res.data
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchStaffRewardPunishment = (pk: number) =>
    api
      .get(`/staff-reward-punishment/${pk}/`)
      .then(res => (staffRewardPunishment.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createStaffRewardPunishment = (payload: StaffRewardPunishment, page = 1, com = 1) =>
    api
      .post(`/staff-reward-punishment/`, payload)
      .then(async res => {
        await fetchAllStaffRewardPunishmentList(com)
        await fetchStaffRewardPunishmentList({ page, com })
        await fetchStaffRewardPunishment(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateStaffRewardPunishment = (payload: StaffRewardPunishment, page = 1, com = 1) =>
    api
      .put(`/staff-reward-punishment/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllStaffRewardPunishmentList(com)
        await fetchStaffRewardPunishmentList({ page, com })
        await fetchStaffRewardPunishment(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteStaffRewardPunishment = (pk: number, com = 1) =>
    api
      .delete(`/staff-reward-punishment/${pk}/`)
      .then(async () => {
        await fetchAllStaffRewardPunishmentList(com)
        await fetchStaffRewardPunishmentList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // StaffLeaveQuota --------------------------------------------------
  const staffLeaveQuotaList = ref<StaffLeaveQuota[]>([])
  const allStaffLeaveQuotaList = ref<StaffLeaveQuota[]>([])
  const staffLeaveQuota = ref<StaffLeaveQuota | null>(null)
  const staffLeaveQuotasCount = ref<number>(0)

  const staffLeaveQuotaPages = (itemsPerPage: number) =>
    Math.ceil(staffLeaveQuotasCount.value / itemsPerPage)

  const fetchStaffLeaveQuotaList = async (payload: StaffLeaveQuotaFilter) => {
    const { page = 1, com = 1, staff: staffId = '', year = '', q = '' } = payload
    let queryStr = `?limit=10&page=${page}&company=${com}&search=${q}`
    if (staffId) queryStr += `&staff=${staffId}`
    if (year) queryStr += `&year=${year}`

    return await api
      .get(`/staff-leave-quota/${queryStr}`)
      .then(res => {
        staffLeaveQuotaList.value = res.data.results
        staffLeaveQuotasCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllStaffLeaveQuotaList = (com = 1, year?: number) => {
    let queryStr = `?company=${com}&limit=500`
    if (year) queryStr += `&year=${year}`
    return api
      .get(`/staff-leave-quota/${queryStr}`)
      .then(res => {
        allStaffLeaveQuotaList.value = res.data.results ?? res.data
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchStaffLeaveQuota = (pk: number) =>
    api
      .get(`/staff-leave-quota/${pk}/`)
      .then(res => (staffLeaveQuota.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createStaffLeaveQuota = (payload: StaffLeaveQuota, page = 1, com = 1) =>
    api
      .post(`/staff-leave-quota/`, payload)
      .then(async res => {
        await fetchAllStaffLeaveQuotaList(com)
        await fetchStaffLeaveQuotaList({ page, com })
        await fetchStaffLeaveQuota(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateStaffLeaveQuota = (payload: StaffLeaveQuota, page = 1, com = 1) =>
    api
      .put(`/staff-leave-quota/${payload.pk}/`, payload)
      .then(async res => {
        await fetchAllStaffLeaveQuotaList(com)
        await fetchStaffLeaveQuotaList({ page, com })
        await fetchStaffLeaveQuota(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteStaffLeaveQuota = (pk: number, com = 1) =>
    api
      .delete(`/staff-leave-quota/${pk}/`)
      .then(async () => {
        await fetchAllStaffLeaveQuotaList(com)
        await fetchStaffLeaveQuotaList({ com })
        message('warning', '', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))


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
  }
})
