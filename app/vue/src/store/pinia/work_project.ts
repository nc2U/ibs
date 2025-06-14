import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import type {
  IssueProject,
  Member,
  ProjectFilter,
  Role,
  Version,
} from '@/store/types/work_project.ts'

export const useWork = defineStore('work', () => {
  // Issue Project states & getters
  const issueProject = ref<IssueProject | null>(null)
  const issueProjectList = ref<IssueProject[]>([])
  const issueProjects = computed(() => issueProjectList.value.filter(proj => proj.parent === null))

  const allProjects = ref<IssueProject[]>([])
  const AllIssueProjects = computed(() => {
    const reg_arr: number[] = [] // 등록된 프로젝트 / 중복 방지용
    const result: IssueProject[] = []

    function flatten(proj: IssueProject) {
      if (proj?.pk && !reg_arr.includes(proj.pk) && proj.visible) {
        reg_arr.push(proj.pk)
        result.push(proj)
      }

      if (!!proj.sub_projects?.length) proj.sub_projects.forEach(sub => flatten(sub))
    }

    allProjects.value.forEach(rootProj => flatten(rootProj))
    return result
  })

  const getAllProjects = computed(() =>
    allProjects.value.map(i => ({
      value: i.pk as number,
      label: i.name,
      slug: i.slug,
      status: i.status,
      repo: i.module?.repository,
    })),
  )

  // actions
  const fetchIssueProjectList = async (payload: ProjectFilter) => {
    let url = `/issue-project/?1=1`
    if (payload.company) `&company=${payload.company}`
    if (payload?.status) url += `&status=${payload?.status}`
    else if (payload?.status__exclude) url += `&status__exclude=${payload?.status__exclude}`
    if (payload?.parent) url += `&parent__slug=${payload.parent}`
    if (payload.project) url += `&project=${payload.project}`
    else if (payload.project__exclude) url += `&project__exclude=${payload.project__exclude}`
    if (payload.is_public) url += `&is_public=${payload.is_public}`
    else if (payload.is_public__exclude) url += `&is_public__exclude=${payload.is_public__exclude}`
    if (payload.name) url += `&name=${payload.name}`
    if (payload.member) url += `&members__user=${payload.member}`
    if (payload.description) url += `&description=${payload.description}`

    return await api
      .get(url)
      .then(res => (issueProjectList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchAllIssueProjectList = async (
    com: '' | number = '',
    sort: '' | '1' | '2' | '3' = '',
    p_isnull: '' | '1' = '',
    status: '' | '1' | '9' = '1',
  ) =>
    await api
      .get(
        `/issue-project/?company=${com}&sort=${sort}&parent__isnull=${p_isnull}&status=${status}`,
      )
      .then(res => (allProjects.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const fetchIssueProject = (slug: string) =>
    api
      .get(`/issue-project/${slug}/`)
      .then(res => (issueProject.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const removeIssueProject = () => (issueProject.value = null)

  const createIssueProject = (payload: IssueProject) =>
    api
      .post(`/issue-project/`, payload)
      .then(res => {
        fetchIssueProject(res.data.slug).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateIssueProject = (payload: IssueProject) =>
    api
      .put(`/issue-project/${payload.slug}/`, payload)
      .then(async res => {
        await fetchIssueProject(res.data.slug)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const patchIssueProject = async (payload: {
    slug: string
    activities?: number[]
    users?: number[]
    roles?: number[]
    del_mem?: number
    status?: '1' | '9'
  }) => {
    const type = payload.del_mem ? 'warning' : 'success'
    return await api
      .patch(`/issue-project/${payload.slug}/`, payload)
      .then(async res => {
        await fetchIssueProject(res.data.slug)
        message(type)
      })
      .catch(err => errorHandle(err.response.data))
  }

  const deleteIssueProject = (pk: number) =>
    api
      .delete(`/issue-project/${pk}/`)
      .then(async () => {
        await fetchIssueProjectList({})
        message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  // Role & Permission states & getters
  const role = ref<Role | null>(null)
  const roleList = ref<Role[]>([])
  const getRoles = computed(() => roleList.value.map(r => ({ value: r.pk, label: r.name })))

  const fetchRole = (pk: number) =>
    api
      .get(`/role/${pk}/`)
      .then(res => (role.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchRoleList = () =>
    api
      .get(`/role/`)
      .then(res => (roleList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  // member states & getters
  const member = ref<Member | null>(null)
  const memberList = ref<Member[]>([])

  const fetchMember = (pk: number) =>
    api
      .get(`/member/${pk}/`)
      .then(res => (member.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchMemberList = (user?: number) =>
    api
      .get(`/member/?user=${user ?? ''}`)
      .then(res => (memberList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createMember = (payload: { user?: number; roles?: number[]; slug: string }) =>
    api
      .post(`/member/`, payload)
      .then(async res => {
        await fetchIssueProject(payload.slug)
        await fetchMember(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const patchMember = (payload: { pk: number; user?: number; roles?: number[] }) =>
    api
      .patch(`/member/${payload.pk}/`, payload)
      .then(async res => {
        await fetchIssueProject(res.data.project.slug)
        await fetchMember(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  // version states & getters
  const version = ref<Version | null>(null)
  const versionList = ref<Version[]>([])
  const getVersions = computed(() =>
    versionList.value.map(v => ({
      value: v.pk as number,
      label: `${v.project?.name} - ${v.name}`,
    })),
  )

  const fetchVersion = (pk: number) =>
    api
      .get(`/version/${pk}/`)
      .then(res => (version.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchVersionList = async (payload: {
    project: string
    status?: '' | '1' | '2' | '3'
    exclude?: '' | '1' | '2' | '3'
    search?: string
  }) => {
    const { project } = payload
    let url = `/version/?project__slug=${project}`
    if (payload.status) url += `&status=${payload.status}`
    if (payload.exclude) url += `&status__exclude=${payload.exclude}`
    if (payload.search) url += `&search=${payload.search}`
    return await api
      .get(url)
      .then(res => (versionList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const createVersion = (payload: Version) =>
    api
      .post(`/version/`, payload)
      .then(async res => {
        await fetchVersion(res.data.pk)
        await fetchVersionList(res.data.project.slug)
        await fetchIssueProject(res.data.project.slug)
        message()
        return res.data.pk
      })
      .catch(err => errorHandle(err.response.data))

  const updateVersion = (payload: Version) =>
    api
      .put(`/version/${payload.pk}/`, payload)
      .then(async res => {
        await fetchVersion(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteVersion = (pk: number, project = '') =>
    api
      .delete(`/version/${pk}/`)
      .then(async () => {
        await fetchVersionList({ project, status: '', exclude: '' })
        await fetchIssueProject(project)
        message('warning', '알림!', '해당 버전이 삭제되었습니다!')
      })
      .catch(err => errorHandle(err.response.data))

  return {
    issueProject,
    issueProjectList,
    issueProjects,
    AllIssueProjects,
    getAllProjects,
    fetchIssueProjectList,
    fetchAllIssueProjectList,
    fetchIssueProject,
    removeIssueProject,
    createIssueProject,
    updateIssueProject,
    patchIssueProject,
    deleteIssueProject,

    role,
    roleList,
    getRoles,
    fetchRole,
    fetchRoleList,

    member,
    memberList,
    fetchMember,
    fetchMemberList,
    createMember,
    patchMember,

    version,
    versionList,
    getVersions,
    fetchVersion,
    fetchVersionList,
    createVersion,
    updateVersion,
    deleteVersion,
  }
})
