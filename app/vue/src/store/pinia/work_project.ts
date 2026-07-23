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
  ProjectBookmark,
} from '@/store/types/work_project.ts'

export const useWork = defineStore('work', () => {
  const comStore = useCompany()
  const permStore = usePermission()

  // Issue Project states & getters
  const currentProject = ref<IssueProject | null>(null)

  // 1. 원시 플랫 상태 (Refs)
  const allReadableProjects = ref<IssueProject[]>([]) // 프로젝트 검색 선택 목록용(상태: 사용중 + 닫힘 - 권한 기본 적용)
  const allActiveProjects = computed(() => allReadableProjects.value.filter(p => p.status === '1'))
  const projectResults = ref<IssueProject[]>([]) // 검색 결과 - 표시 목록용(필터 기본 값은 상태: 사용중 - 권한 기본 적용, 모든 필터 사용)
  const myProjects = ref<IssueProject[]>([]) // 내가 멤버인 프로젝트(권한 기본 적용)

  const activeFilters = ref<ProjectFilter>({})

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

  // 최상위 루트 노드 바인딩 (parent === null)
  const allReadableProjectsTree = computed(() => buildProjectTree(allReadableProjects.value))
  const projectResultsTree = computed(() => {
    let list = projectResults.value

    const filters = activeFilters.value
    if (filters) {
      // 1. parent__isnull 필터
      if (filters.parent__isnull !== undefined) {
        if (filters.parent__isnull) {
          list = list.filter(p => p.parent === null || p.parent === undefined)
        } else {
          list = list.filter(p => p.parent !== null && p.parent !== undefined)
        }
      }
      // 2. parent__slug 필터 (parent가 일치)
      if (filters.parent) {
        const parentProj = allReadableProjects.value.find(p => p.slug === filters.parent)
        if (parentProj) {
          list = list.filter(p => p.parent === parentProj.pk)
        }
      }
      // 3. parent__exclude 필터 (parent가 일치하지 않음)
      if (filters.parent__exclude) {
        const parentProj = allReadableProjects.value.find(p => p.slug === filters.parent__exclude)
        if (parentProj) {
          list = list.filter(p => p.parent !== parentProj.pk)
        }
      }
    }

    return buildProjectTree(list)
  })
  const myProjectsTree = computed(() => buildProjectTree(myProjects.value))

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

  // 재귀적 평탄화 가공 상태 (Computed)
  const allReadableProjectsFlat = computed(() => flattenTree(allReadableProjectsTree.value))
  const projectResultsFlat = computed(() => flattenTree(projectResultsTree.value))
  const myProjectsFlat = computed(() => flattenTree(myProjectsTree.value))

  // 4. 셀렉박스 UI 옵션 가공 상태 - PK + SLUG 형태 (Computed)
  const getAllReadableProjects = computed(() =>
    allReadableProjects.value.map(i => ({
      value: i.pk as number,
      label:
        (i.depth && i.parent_visible ? '\u00A0'.repeat(i.depth * 2) + '» \u00A0' : '') + i.name,
      slug: i.slug as string,
      module: i.module,
    })),
  )
  const getAllActiveProjects = computed(() =>
    allActiveProjects.value.map(i => ({
      value: i.pk as number,
      label:
        (i.depth && i.parent_visible ? '\u00A0'.repeat(i.depth * 2) + '» \u00A0' : '') + i.name,
      slug: i.slug as string,
      module: i.module,
    })),
  )
  const getMyProjects = computed(() =>
    myProjects.value.map(i => ({
      value: i.pk as number,
      label:
        (i.depth && i.parent_visible ? '\u00A0'.repeat(i.depth * 2) + '» \u00A0' : '') + i.name,
      slug: i.slug as string,
      module: i.module,
    })),
  )

  // actions
  const fetchAllProjectList = async (
    type: '' | '1' | '2' | '3' = '',
    company: '' | number = '',
  ) => {
    return await api
      .get(`/issue-project/?type=${type}&company=${company}&status__exclude='9'`)
      .then(res => (allReadableProjects.value = res.data.results || res.data))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchIssueProjectList = async (payload: ProjectFilter) => {
    activeFilters.value = payload
    let url = `/issue-project/?1=1`
    if (payload.company) url += `&company=${payload.company}`
    if (payload?.status) url += `&status=${payload?.status}`
    else if (payload?.status__exclude) url += `&status__exclude=${payload?.status__exclude}`
    if (payload?.parent) url += `&parent__slug=${payload.parent}`
    if (payload.project) url += `&project=${payload.project}`
    else if (payload.project__exclude) url += `&project__exclude=${payload.project__exclude}`
    if (payload.is_public) url += `&is_public=${payload.is_public}`
    else if (payload.is_public__exclude) url += `&is_public__exclude=${payload.is_public__exclude}`
    if (payload.name) url += `&name=${payload.name}`
    else if (payload.name__exclude) url += `&name__exclude=${payload.name__exclude}`
    else if (payload.name__startswith) url += `&name__startswith=${payload.name__startswith}`
    else if (payload.name__endswith) url += `&name__endswith=${payload.name__endswith}`
    else if (payload.name__isnull !== undefined) url += `&name__isnull=${payload.name__isnull}`

    if (payload.member) url += `&members__user=${payload.member}`

    if (payload.description) url += `&description=${payload.description}`
    else if (payload.description__exclude)
      url += `&description__exclude=${payload.description__exclude}`
    else if (payload.description__startswith)
      url += `&description__startswith=${payload.description__startswith}`
    else if (payload.description__endswith)
      url += `&description__endswith=${payload.description__endswith}`
    else if (payload.description__isnull !== undefined)
      url += `&description__isnull=${payload.description__isnull}`

    if (payload.from_created) url += `&from_created=${payload.from_created}`
    if (payload.to_created) url += `&to_created=${payload.to_created}`
    if (payload.from_updated) url += `&from_updated=${payload.from_updated}`
    if (payload.to_updated) url += `&to_updated=${payload.to_updated}`

    if (payload.bookmark !== undefined) url += `&bookmark=${payload.bookmark}`
    if (payload.my_project !== undefined) url += `&my_project=${payload.my_project}`

    return await api
      .get(url)
      .then(res => (projectResults.value = res.data.results || res.data))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchMyProjectsList = async () => {
    return await api
      .get(`/issue-project/my_projects/`)
      .then(res => (myProjects.value = res.data))
      .catch(err => errorHandle(err.response.data))
  }

  const fetchIssueProject = (slug: string) =>
    api
      .get(`/issue-project/${slug}/`)
      .then(async res => {
        currentProject.value = res.data
        permStore.setProjectPermissions(res.data.my_perms || [])
        permStore.setProjectRole(res.data.my_role || null)
        await comStore.fetchCompany(res.data.company)
      })
      .catch(err => errorHandle(err.response.data))

  const removeIssueProject = () => (currentProject.value = null)

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

  const setProjectStatus = (slug: string, status: '1' | '2' | '9') =>
    api
      .post(`/issue-project/${slug}/set_status/`, { status })
      .then(async () => {
        await fetchIssueProject(slug)
        message('success', '성공!', '프로젝트 상태가 변경되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))

  const toggleProjectPublic = (slug: string, showMessage = false) =>
    api
      .post(`/issue-project/${slug}/toggle_public/`)
      .then(async () => {
        await fetchIssueProject(slug)
        if (showMessage) message()
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

  const fetchRoleList = (category?: 'work_core' | 'ibs_global') => {
    const url = category ? `/role/?category=${category}` : `/role/`
    return api
      .get(url)
      .then(res => (roleList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

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

  const fetchPermissionList = (category?: 'work_core' | 'ibs_global') => {
    const url = category ? `/permission/?category=${category}` : `/permission/`
    return api
      .get(url)
      .then(res => (permissionList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

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
    const { user, roles, ...rest } = payload
    const body = {
      ...rest,
      ...(user !== undefined ? { user_id: user } : {}),
      ...(roles !== undefined ? { role_ids: roles } : {}),
    }
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
    const { pk, user, roles, ...rest } = payload
    const body = {
      ...rest,
      ...(user !== undefined ? { user_id: user } : {}),
      ...(roles !== undefined ? { role_ids: roles } : {}),
    }
    return api
      .patch(`/member/${pk}/`, body)
      .then(async res => {
        await fetchIssueProject(res.data.project.slug)
        await fetchMember(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))
  }

  const deleteMember = async (pk: number, userPk?: number) => {
    return api
      .delete(`/member/${pk}/`)
      .then(async () => {
        await fetchMemberList(userPk)
        message('warning', '알림!', '해당 구성원이 프로젝트에서 제거되었습니다.')
      })
      .catch(err => errorHandle(err.response.data))
  }

  // subscribed_projects
  const subscribedProjects = ref([])

  const fetchSubscribedProjects = async (userPk: number) =>
    api
      .get(`/project-subscription/?user=${userPk}`)
      .then(res => (subscribedProjects.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createSubscribedProjects = async (payload: { user: number; project_ids: number[] }) => {
    await api
      .post(`/project-subscription/bulk-update/`, payload)
      .then(() => fetchSubscribedProjects(payload.user))
      .catch(err => errorHandle(err.response.data))
  }

  // bookmarked_projects
  const bookmarkedProjects = ref<ProjectBookmark[]>([])

  const fetchBookmarks = async () =>
    api
      .get(`/project-bookmark/`)
      .then(res => (bookmarkedProjects.value = res.data.results ?? res.data))
      .catch(err => errorHandle(err.response.data))

  const toggleBookmark = async (projectId: number) => {
    return api
      .post(`/project-bookmark/toggle/`, { project: projectId })
      .then(async res => {
        await fetchBookmarks()
        const isBookmarked = res.data.bookmarked

        // 1. 단일 활성 프로젝트 상세 정보 갱신
        if (currentProject.value && currentProject.value.pk === projectId) {
          currentProject.value.is_bookmarked = isBookmarked
        }

        // 2. allReadableProjects 리스트 갱신
        const targetAll = allReadableProjects.value.find(p => p.pk === projectId)
        if (targetAll) targetAll.is_bookmarked = isBookmarked

        // 3. projectResults 리스트 갱신
        const targetIssue = projectResults.value.find(p => p.pk === projectId)
        if (targetIssue) targetIssue.is_bookmarked = isBookmarked

        // 4. myProjects 리스트 갱신
        const targetMy = myProjects.value.find(p => p.pk === projectId)
        if (targetMy) targetMy.is_bookmarked = isBookmarked

        return res.data as { bookmarked: boolean }
      })
      .catch(err => errorHandle(err.response.data))
  }

  const reorderBookmarks = async (orderedIds: number[]) =>
    api
      .post(`/project-bookmark/reorder/`, { ordered_ids: orderedIds })
      .then(res => (bookmarkedProjects.value = res.data))
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

  const fetchVersionList = async (
    payload?:
      | string
      | {
          project?: string
          status?: '' | '1' | '2' | '3'
          exclude?: '' | '1' | '2' | '3'
          search?: string
        },
  ) => {
    let url = `/version/`
    const params = new URLSearchParams()

    if (typeof payload === 'string') {
      params.append('project__slug', payload)
    } else if (payload && typeof payload === 'object') {
      if (payload.project) params.append('project__slug', payload.project)
      if (payload.status) params.append('status', payload.status)
      if (payload.exclude) params.append('status__exclude', payload.exclude)
      if (payload.search) params.append('search', payload.search)
    }

    const queryString = params.toString()
    if (queryString) url += `?${queryString}`

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
    currentProject,

    allReadableProjects,
    myProjects,

    allReadableProjectsTree,
    projectResultsTree,
    myProjectsTree,

    allReadableProjectsFlat,
    projectResultsFlat,
    myProjectsFlat,

    allActiveProjects,

    getAllReadableProjects,
    getAllActiveProjects,
    getMyProjects,

    fetchAllProjectList,
    fetchIssueProjectList,
    fetchMyProjectsList,
    fetchIssueProject,
    removeIssueProject,
    createIssueProject,
    updateIssueProject,
    patchIssueProject,
    updateMembers,
    deleteIssueProject,
    toggleProjectStatus,
    setProjectStatus,
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
    deleteMember,

    subscribedProjects,
    fetchSubscribedProjects,
    createSubscribedProjects,

    bookmarkedProjects,
    fetchBookmarks,
    toggleBookmark,
    reorderBookmarks,

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
