import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import { useCompany } from '@/store/pinia/company.ts'
import { usePermission } from '@/store/pinia/work_permission.ts'
import type {
  ProjectFilter,
  IssueProject,
  Role,
  Permission,
  Member,
  ProjectMember,
  Version,
  FormVersion,
} from '@/store/types/work_project.ts'

export const useWork = defineStore('work', () => {
  const comStore = useCompany()
  const permStore = usePermission()

  // Issue Project states & getters
  const issueProject = ref<IssueProject | null>(null)

  // 1. 원시 플랫 상태 (Refs)
  const allProjects = ref<IssueProject[]>([])
  const visibleProjects = ref<IssueProject[]>([])
  const myProjects = ref<IssueProject[]>([])

  // 하위 호환성 연결: 기존 issueProjectList는 visibleProjects를 바라봅니다.
  const issueProjectList = visibleProjects

  // 2. 트리 재구성 함수 및 트리 가공 상태 (Computed)
  const buildProjectTree = (projects: IssueProject[]): IssueProject[] => {
    const map = new Map<number, IssueProject>()
    projects.forEach(p => {
      if (p.pk !== undefined) {
        map.set(p.pk, { ...p, sub_projects: [] })
      }
    })

    const roots: IssueProject[] = []
    projects.forEach(p => {
      if (p.pk !== undefined) {
        const cloned = map.get(p.pk)!
        if (p.parent !== null && p.parent !== undefined) {
          const parentNode = map.get(p.parent)
          if (parentNode) {
            parentNode.sub_projects.push(cloned)
          } else {
            roots.push(cloned)
          }
        } else {
          roots.push(cloned)
        }
      }
    })
    return roots
  }

  const allProjectsTree = computed(() => buildProjectTree(allProjects.value))
  const visibleProjectsTree = computed(() => buildProjectTree(visibleProjects.value))
  const myProjectsTree = computed(() => buildProjectTree(myProjects.value))

  // 최상위 루트 노드 바인딩 (parent === null)
  const allProjectsRoot = computed(() => allProjectsTree.value)
  const visibleProjectsRoot = computed(() => visibleProjectsTree.value)
  const myProjectsRoot = computed(() => myProjectsTree.value)

  // 하위 호환성 연결: 기존의 최상위 루트 리스트 issueProjects는 visibleProjectsTree를 반환합니다.
  const issueProjects = computed(() => visibleProjectsTree.value)

  // 3. 재귀적 평탄화 가공 상태 (Computed)
  const flattenTree = (projects: IssueProject[]) => {
    const visited = new Set<number>()
    const result: IssueProject[] = []

    const flatten = (proj: IssueProject) => {
      if (proj?.pk && !visited.has(proj.pk) && proj.visible) {
        visited.add(proj.pk)
        result.push(proj)
      }
      if (Array.isArray(proj.sub_projects)) proj.sub_projects.forEach(flatten)
    }
    projects.forEach(flatten)
    return result
  }

  // 하위 호환성 연결: 기존 AllIssueProjects는 visibleProjects를 평탄화합니다.
  const AllIssueProjects = computed(() => flattenTree(visibleProjects.value))
  const myProjectsFlat = computed(() => flattenTree(myProjects.value))
  const allProjectsFlat = computed(() => flattenTree(allProjects.value))

  // 4. 셀렉박스 UI 옵션 가공 상태 - PK 형태 (Computed)
  const getAllProjPks = computed(() =>
    allProjects.value.map(i => ({
      value: i.pk as number,
      label: i.name as string,
    })),
  )
  const getVisibleProjPks = computed(() =>
    visibleProjects.value.map(i => ({
      value: i.pk as number,
      label: i.name as string,
    })),
  )
  const getMyProjPks = computed(() =>
    myProjects.value.map(i => ({
      value: i.pk as number,
      label: i.name as string,
    })),
  )

  // 5. 셀렉박스 UI 옵션 가공 상태 - Slug 형태 (Computed)
  const getAllProjects = computed(() =>
    allProjects.value.map(i => ({
      pk: i.pk as number,
      value: i.slug as string,
      label: i.name,
      slug: i.slug,
      status: i.status,
      depth: i.depth,
      parent_visible: i.parent_visible,
    })),
  )
  const getVisibleProjects = computed(() =>
    visibleProjects.value.map(i => ({
      pk: i.pk as number,
      value: i.slug as string,
      label: i.name,
      slug: i.slug,
      status: i.status,
      depth: i.depth,
      parent_visible: i.parent_visible,
    })),
  )
  const getMyProjects = computed(() =>
    myProjects.value.map(i => ({
      pk: i.pk as number,
      value: i.slug as string,
      label: i.name,
      slug: i.slug,
      status: i.status,
      depth: i.depth,
      parent_visible: i.parent_visible,
    })),
  )

  // actions
  const fetchAllProjectsList = async (com: '' | number = '') => {
    return await api
      .get(`/issue-project/all_projects/?company=${com}`)
      .then(res => (allProjects.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchVisibleProjectsList = async (payload: ProjectFilter) => {
    let url = `/issue-project/visible_projects/?1=1`
    if (payload.company) url += `&company=${payload.company}`
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
      .then(res => (visibleProjects.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchMyProjectsList = async (com: '' | number = '') => {
    return await api
      .get(`/issue-project/my_projects/?company=${com}`)
      .then(res => (myProjects.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchIssueProjectList = fetchVisibleProjectsList

  const fetchAllIssueProjectList = async (
    com: '' | number = '',
    sort: '' | '1' | '2' | '3' = '',
    p_isnull: '' | '1' = '',
    status: '' | '1' | '9' = '1',
  ) => {
    // 1. 보이는 프로젝트 조회
    const url = `/issue-project/visible_projects/?company=${com}&status=${status}`
    await api.get(url).then(res => (visibleProjects.value = res.data)).catch(err => errorHandle(err.response.data))

    // 2. 내 프로젝트 조회
    const myUrl = `/issue-project/my_projects/?company=${com}&status=${status}`
    await api.get(myUrl).then(res => (myProjects.value = res.data)).catch(err => errorHandle(err.response.data))

    // 3. 전체 프로젝트 조회
    const allUrl = `/issue-project/all_projects/?company=${com}&status=${status}`
    await api.get(allUrl).then(res => (allProjects.value = res.data)).catch(err => errorHandle(err.response.data))
  }

  const fetchIssueProject = (slug: string) =>
    api
      .get(`/issue-project/${slug}/`)
      .then(async res => {
        issueProject.value = res.data
        permStore.setProjectPermissions(res.data.my_perms || [])
        permStore.setProjectRole(res.data.my_role || null)
        await comStore.fetchCompany(res.data.company)
      })
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

  const updateMembers = async (payload: {
    slug: string
    users: number[]
    roles: number[]
    del_mem?: number
  }) => {
    return await api
      .post(`/issue-project/${payload.slug}/update_members/`, payload)
      .then(async () => {
        await fetchIssueProject(payload.slug)
        message('success', '성공!', '구성원 정보가 업데이트되었습니다.')
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

  const toggleProjectStatus = (slug: string) =>
    api
      .post(`/issue-project/${slug}/toggle_status/`)
      .then(async () => {
        await fetchIssueProject(slug)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const toggleProjectPublic = (slug: string) =>
    api
      .post(`/issue-project/${slug}/toggle_public/`)
      .then(async () => {
        await fetchIssueProject(slug)
        message()
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

  const createRole = (payload: Role) =>
    api
      .post(`/role/`, payload)
      .then(res => {
        fetchRoleList().then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const updateRole = (payload: Role) =>
    api
      .put(`/role/${payload.pk}/`, payload)
      .then(res => {
        fetchRoleList().then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const patchRole = (payload: { pk: number; permissions: number[] }) =>
    api
      .patch(`/role/${payload.pk}/`, payload)
      .then(res => {
        fetchRoleList().then(() => message())
      })
      .catch(err => errorHandle(err.response.data))

  const deleteRole = (pk: number) =>
    api
      .delete(`/role/${pk}/`)
      .then(() => {
        fetchRoleList().then(() => message('warning', '알림!', '해당 오브젝트가 삭제되었습니다.'))
      })
      .catch(err => errorHandle(err.response.data))

  const permissionList = ref<Permission[]>([])

  const fetchPermissionList = () =>
    api
      .get(`/permission/`)
      .then(res => (permissionList.value = res.data.results))
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

  const projectMembers = ref<ProjectMember[]>([])

  const fetchProjectMembers = (slug: string) =>
    api
      .get(`/issue-project/${slug}/members/`)
      .then(res => (projectMembers.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const createMember = async (payload: { user?: number; roles?: number[]; slug: string }) => {
    const { roles, ...rest } = payload
    const body = { ...rest, ...(roles !== undefined ? { role_ids: roles } : {}) }
    return api
      .post(`/member/`, body)
      .then(async res => {
        await fetchIssueProject(payload.slug)
        await fetchMember(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const patchMember = async (payload: { pk: number; user?: number; roles?: number[] }) => {
    const { pk, roles, ...rest } = payload
    const body = { ...rest, ...(roles !== undefined ? { role_ids: roles } : {}) }
    return api
      .patch(`/member/${pk}/`, body)
      .then(async res => {
        await fetchIssueProject(res.data.project.slug)
        await fetchMember(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

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

  const createVersion = (payload: FormVersion) =>
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

  const updateVersion = (payload: FormVersion) =>
    api
      .put(`/version/${payload.pk}/`, payload)
      .then(async res => {
        await fetchVersion(res.data.pk)
        await fetchVersionList(res.data.project.slug)
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
    allProjects,
    visibleProjects,
    myProjects,
    issueProjectList,
    issueProjects,
    allProjectsTree,
    visibleProjectsTree,
    myProjectsTree,
    allProjectsRoot,
    visibleProjectsRoot,
    myProjectsRoot,
    AllIssueProjects,
    myProjectsFlat,
    allProjectsFlat,
    getAllProjPks,
    getVisibleProjPks,
    getMyProjPks,
    getAllProjects,
    getVisibleProjects,
    getMyProjects,
    fetchAllProjectsList,
    fetchVisibleProjectsList,
    fetchMyProjectsList,
    fetchIssueProjectList,
    fetchAllIssueProjectList,
    fetchIssueProject,
    removeIssueProject,
    createIssueProject,
    updateIssueProject,
    patchIssueProject,
    updateMembers,
    deleteIssueProject,
    toggleProjectStatus,
    toggleProjectPublic,

    role,
    roleList,
    getRoles,
    fetchRole,
    fetchRoleList,
    createRole,
    updateRole,
    patchRole,
    deleteRole,

    permissionList,
    fetchPermissionList,

    member,
    memberList,
    projectMembers,
    fetchMember,
    fetchMemberList,
    fetchProjectMembers,
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
