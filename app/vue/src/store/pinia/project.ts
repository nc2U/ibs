import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { errorHandle, message } from '@/utils/helper'
import {
  Project,
  ProIncBudget,
  ProOutBudget,
  ExecAmountToBudget,
} from '@/store/types/project'

const accountStore = useAccount()

export const useProject = defineStore('project', () => {
  // states & getters
  const projectList = ref<Project[]>([])
  const allowed_projects = computed(() =>
    accountStore.userInfo && accountStore.userInfo.staffauth
      ? accountStore.userInfo.staffauth.allowed_projects
      : [],
  )
  const projSelect = computed(() => {
    const getProject = accountStore.superAuth
      ? projectList.value
      : projectList.value.filter((p: Project) =>
          allowed_projects.value.includes(p.pk || 0),
        )

    return getProject.map((p: Project) => ({ value: p.pk, label: p.name }))
  })

  const getProjects = computed(() =>
    projectList.value.map((p: Project) => ({ value: p.pk, label: p.name })),
  )

  // actions
  const fetchProjectList = () =>
    api
      .get('/project/')
      .then(res => (projectList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  // states & getters
  const project = ref<Project | null>(null)
  const initProjId = computed(() =>
    accountStore.userInfo?.staffauth?.assigned_project
      ? accountStore.userInfo.staffauth.assigned_project
      : 1,
  )

  // actions
  const fetchProject = (pk: number) =>
    api
      .get(`/project/${pk}/`)
      .then(res => (project.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createProject = (payload: Project) =>
    api
      .post('/project/', payload)
      .then(res =>
        fetchProjectList().then(() =>
          fetchProject(res.data.pk).then(() => message()),
        ),
      )
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
        fetchProjectList().then(() =>
          message('warning', '', '해당 오브젝트가 삭제되었습니다.'),
        ),
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
    api
      .patch(`/Inc-budget/${pk}/`, { budget })
      .then(() => fetchIncBudgetList(project))

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
        fetchOutBudget(res.data.pk).then(r =>
          fetchOutBudgetList(r.data.project).then(() => message()),
        )
      })
      .catch(err => errorHandle(err.response.data))

  const updateOutBudget = (payload: ProOutBudget) =>
    api
      .put(`/out-budget/${payload.pk}/`, payload)
      .then(res => {
        fetchOutBudget(res.data.pk).then(r =>
          fetchOutBudgetList(r.data.project).then(() => message()),
        )
      })
      .catch(err => errorHandle(err.response.data))

  const patchOutBudgetList = (project: number, pk: number, budget: number) =>
    api
      .patch(`/out-budget/${pk}/`, { budget })
      .then(() => fetchOutBudgetList(project))

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
  const execAmountList = ref<ExecAmountToBudget[]>([])

  // actions
  const fetchExecAmountList = (project: number, date = '') =>
    api
      .get(`/exec-amount/?project=${project}&date=${date}`)
      .then(res => (execAmountList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  return {
    projectList,
    allowed_projects,
    projSelect,
    getProjects,
    fetchProjectList,

    project,
    initProjId,
    fetchProject,
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
    patchOutBudgetList,
    deleteOutBudget,

    execAmountList,
    fetchExecAmountList,
  }
})
