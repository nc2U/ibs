import api from '@/api'
import Cookies from 'js-cookie'
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
  type ComFilter,
} from '@/store/types/company'

export const useCompany = defineStore('company', () => {
  const accountStore = useAccount()

  // states & getters
  const companyList = ref<Company[]>([])
  const company = ref<Company | null>(null)

  const currentCompany = Number(Cookies.get('curr-company'))
  const userCompany = computed(() =>
    accountStore.userInfo?.staffauth?.company ? accountStore.userInfo.staffauth.company : 1,
  )
  const initComId = computed(() => (currentCompany ? currentCompany : userCompany.value))

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
    } catch (err: any) {
      console.warn(`Company with ID ${pk} not found, trying to fetch first available company`)

      // If company fetch fails, try to get the first available company
      try {
        const companyListRes = await api.get('/company/')
        if (companyListRes.data.results && companyListRes.data.results.length > 0) {
          const firstCompany = companyListRes.data.results[0]
          company.value = firstCompany

          // Update the cookie to prevent future errors
          Cookies.set('curr-company', firstCompany.pk.toString(), { expires: 365 })

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
      value: r.name,
      label: r.name,
    })),
  )

  const getPkGrades = computed(() =>
    allGradeList.value.map(r => ({
      value: r.pk,
      label: r.name,
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

  const staffList = ref<Staff[]>([])
  const staff = ref<Staff | null>(null)
  const staffsCount = ref<number>(0)

  // actions
  const staffPages = (itemsPerPage: number) => Math.ceil(staffsCount.value / itemsPerPage)

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

    staffList,
    staff,
    staffsCount,
    staffPages,
    fetchStaffList,
    fetchStaff,
    createStaff,
    updateStaff,
    deleteStaff,
  }
})
