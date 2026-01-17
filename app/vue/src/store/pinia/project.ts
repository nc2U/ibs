import api from '@/api'
import Cookies from 'js-cookie'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { errorHandle, message } from '@/utils/helper'
import {
  type ExecAmountToBudget,
  type LedgerExecAmountToBudget,
  type ProIncBudget,
  type Project,
  type ProOutBudget,
  type StatusOutBudget,
} from '@/store/types/project'

export const useProject = defineStore('project', () => {
  const accountStore = useAccount()

  // states & getters
  const projectList = ref<Project[]>([])
  const projectsCount = ref(0)
  const allowed_projects = computed(() =>
    accountStore.userInfo && accountStore.userInfo.staffauth
      ? accountStore.userInfo.staffauth.allowed_projects
      : [],
  )
  const projSelect = computed(() => {
    const getProject = accountStore.superAuth
      ? projectList.value
      : projectList.value.filter((p: Project) => allowed_projects.value.includes(p.pk || 0))

    return getProject.map((p: Project) => ({ value: p.pk, label: p.name }))
  })

  const getProjects = computed(() =>
    projectList.value.map((p: Project) => ({ value: p.pk, label: p.name })),
  )

  // actions
  const fetchProjectList = (status: '' | '1' | '9' = '1') =>
    api
      .get(`/project/?issue_project__status=${status}`)
      .then(res => {
        projectList.value = res.data.results
        projectsCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))

  // states & getters
  const project = ref<Project | null>(null)
  const assingedProject = computed(() =>
    accountStore.userInfo?.staffauth?.assigned_project
      ? accountStore.userInfo.staffauth.assigned_project
      : 0,
  )

  const currentProject = Number(Cookies.get('curr-project'))
  const initProjId = computed(() => (currentProject ? currentProject : assingedProject.value))

  // actions
  const fetchProject = (pk: number) =>
    api
      .get(`/project/${pk}/`)
      .then(res => (project.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const removeProject = () => (project.value = null)

  const createProject = (payload: Project) =>
    api
      .post('/project/', payload)
      .then(res => fetchProjectList().then(() => fetchProject(res.data.pk).then(() => message())))
      .catch(err => errorHandle(err.response.data))

  const updateProject = (payload: Project) =>
    api
      .put(`/project/${payload.pk}/`, payload)
      .then(res => fetchProject(res.data.pk).then(() => message()))
      .catch(err => errorHandle(err.response.data))

  const deleteProject = (pk: number) =>
    api
      .delete(`/project/${pk}/`)
      .then(() =>
        fetchProjectList().then(() => message('warning', '', '해당 오브젝트가 삭제되었습니다.')),
      )
      .catch(err => errorHandle(err.response.data))

  // states & getters
  const proIncBudgetList = ref<ProIncBudget[]>([])
  const proIncBudget = ref<ProIncBudget | null>(null)

  // actions
  const fetchIncBudgetList = (project: number) =>
    api
      .get(`/inc-budget/?project=${project}`)
      .then(res => (proIncBudgetList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchIncBudget = (pk: number) =>
    api
      .get(`/inc-budget/${pk}/`)
      .then(res => (proIncBudget.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createIncBudget = (payload: ProIncBudget) =>
    api
      .post('/inc-budget/', payload)
      .then(res => {
        fetchIncBudgetList(res.data.project).then(() =>
          fetchIncBudget(res.data.pk).then(() => message()),
        )
      })
      .catch(err => errorHandle(err.response.data))

  const updateIncBudget = (payload: ProIncBudget) =>
    api
      .put(`/inc-budget/${payload.pk}/`, payload)
      .then(res => {
        fetchIncBudgetList(res.data.project).then(() =>
          fetchIncBudget(res.data.pk).then(() => message()),
        )
      })
      .catch(err => errorHandle(err.response.data))

  const patchIncBudgetList = (project: number, pk: number, budget: number) =>
    api.patch(`/Inc-budget/${pk}/`, { budget }).then(() => fetchIncBudgetList(project))

  const deleteIncBudget = (pk: number, project: number) =>
    api
      .delete(`/inc-budget/${pk}/`)
      .then(() =>
        fetchIncBudgetList(project).then(() =>
          message('warning', '', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  // states & getters
  const proOutBudgetList = ref<ProOutBudget[]>([])
  const proOutBudget = ref<ProOutBudget | null>(null)

  // actions
  const fetchOutBudgetList = (project: number) =>
    api
      .get(`/out-budget/?project=${project}`)
      .then(res => (proOutBudgetList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchOutBudget = (pk: number) =>
    api
      .get(`/out-budget/${pk}/`)
      .then(res => (proOutBudget.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createOutBudget = (payload: ProOutBudget) =>
    api
      .post('/out-budget/', payload)
      .then(res => {
        fetchOutBudgetList(res.data.project).then(() =>
          fetchOutBudget(res.data.pk).then(() => message()),
        )
      })
      .catch(err => errorHandle(err.response.data))

  const updateOutBudget = (payload: ProOutBudget) =>
    api
      .put(`/out-budget/${payload.pk}/`, payload)
      .then(res => {
        fetchOutBudgetList(res.data.project).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const patchOutBudget = (project: number, pk: number, budget: number) =>
    api.patch(`/out-budget/${pk}/`, { budget }).then(() => fetchOutBudgetList(project))

  const deleteOutBudget = (pk: number, project: number) =>
    api
      .delete(`/out-budget/${pk}/`)
      .then(() =>
        fetchOutBudgetList(project).then(() =>
          message('warning', '', '해당 오브젝트가 삭제되었습니다.'),
        ),
      )
      .catch(err => errorHandle(err.response.data))

  // states & getters
  const statusOutBudgetList = ref<StatusOutBudget[]>([])

  // actions
  const fetchStatusOutBudgetList = (project: number, useLedger = false) =>
    api
      .get(`/status-budget/?project=${project}&use_ledger=${useLedger}`)
      .then(res => (statusOutBudgetList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const patchStatusOutBudget = (
    payload: {
      project: number
      pk: number
      budget?: number
      revised_budget?: number
    },
    useLedger = false,
  ) =>
    api
      .patch(`/status-budget/${payload.pk}/`, payload)
      .then(() => fetchStatusOutBudgetList(payload.project, useLedger))

  // states & getters (ibs 기반)
  const execAmountList = ref<ExecAmountToBudget[]>([])
  // states & getters (ledger 기반)
  const ledgerExecAmountList = ref<LedgerExecAmountToBudget[]>([])

  // actions
  const fetchExecAmountList = (project: number, date = '', useLedger = false) =>
    api
      .get(`/exec-amount/?project=${project}&date=${date}&use_ledger=${useLedger}`)
      .then(res => {
        if (useLedger) {
          ledgerExecAmountList.value = res.data.results
        } else {
          execAmountList.value = res.data.results
        }
      })
      .catch(err => errorHandle(err.response.data))

  return {
    projectList,
    projectsCount,
    allowed_projects,
    projSelect,
    getProjects,
    fetchProjectList,

    project,
    initProjId,
    fetchProject,
    removeProject,
    createProject,
    updateProject,
    deleteProject,

    proIncBudgetList,
    proIncBudget,
    fetchIncBudgetList,
    fetchIncBudget,
    createIncBudget,
    updateIncBudget,
    patchIncBudgetList,
    deleteIncBudget,

    proOutBudgetList,
    proOutBudget,
    fetchOutBudgetList,
    fetchOutBudget,
    createOutBudget,
    updateOutBudget,
    patchOutBudget,
    deleteOutBudget,

    statusOutBudgetList,
    fetchStatusOutBudgetList,
    patchStatusOutBudget,

    execAmountList,
    ledgerExecAmountList,
    fetchExecAmountList,
  }
})
