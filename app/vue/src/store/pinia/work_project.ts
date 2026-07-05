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

  /**
   * [프로젝트 상세/필터링 목록 상태]
   * `fetchIssueProjectList` 호출을 통해 API 필터링 조건(회사, 부모 프로젝트, 공개여부 등)에 부합하는
   * 프로젝트 목록을 저장하는 상태입니다. (조회 조건에 따라 목록이 동적으로 변경됨)
   */
  const issueProjectList = ref<IssueProject[]>([])

  /**
   * [최상위(루트) 프로젝트 목록]
   * `issueProjectList`에서 부모가 없는(parent === null) 최상위 프로젝트들만 필터링한 컬렉션입니다.
   * 계층 구조(트리뷰)를 렌더링할 때 루트 노드로 활용됩니다.
   */
  const issueProjects = computed(() => issueProjectList.value.filter(proj => proj.parent === null))

  /**
   * [전체 프로젝트 원시 데이터 트리]
   * `fetchAllIssueProjectList` 호출을 통해 회사 내 전체 프로젝트 데이터를 계층 구조(sub_projects가 중첩된 트리 형태)로
   * 로드하여 메모리에 저장해 두는 마스터 리스트 상태입니다.
   */
  const allProjects = ref<IssueProject[]>([])

  /**
   * [평탄화된(Flattened) 전체 프로젝트 목록]
   * 트리 구조로 중첩되어 있는 `allProjects`를 재귀적으로 탐색(flatten)하여 1차원 배열로 평탄화한 컬렉션입니다.
   * 중복을 방지(visited Set 사용)하고 활성화된(visible: true) 프로젝트만 필터링하여 전역에서 빠른 탐색이 필요할 때 사용됩니다.
   */
  const AllIssueProjects = computed(() => {
    const visited = new Set<number>()
    const result: IssueProject[] = []

    const flatten = (proj: IssueProject) => {
      if (proj?.pk && !visited.has(proj.pk) && proj.visible) {
        visited.add(proj.pk)
        result.push(proj)
      }
      if (Array.isArray(proj.sub_projects)) proj.sub_projects.forEach(flatten)
    }
    allProjects.value.forEach(flatten)
    return result
  })

  /**
   * [UI 옵션용 ID-이름 매핑 리스트 (PK 형태)]
   * `allProjects` 목록을 기반으로 Multiselect 등 셀렉트 박스 컴포넌트 규격에 부합하게
   * `{ value: pk, label: name }` 형태로 매핑한 옵션용 컬렉션입니다.
   */
  const getAllProjPks = computed(() =>
    allProjects.value.map(i => ({
      value: i.pk as number,
      label: i.name as string,
    })),
  )

  /**
   * [UI 옵션용 상세 프로젝트 속성 리스트 (Slug 형태)]
   * `allProjects` 목록을 기반으로 컴포넌트(예: 필터, 사이드바 등)에서 참조할 수 있는 주요 속성들
   * (pk, value=slug, label=name, status, depth, parent_visible 등)만 가공하여 노출해 주는 컬렉션입니다.
   */
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

  // actions
  const fetchIssueProjectList = async (payload: ProjectFilter) => {
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
    issueProjectList,
    issueProjects,
    AllIssueProjects,
    getAllProjPks,
    getAllProjects,
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
