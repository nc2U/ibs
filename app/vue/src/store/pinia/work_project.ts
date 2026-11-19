import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import { useCompany } from '@/store/pinia/company.ts'
import { usePermission } from '@/store/pinia/work_permission.ts'
import type {
  ProjectFilter,
  ProjectSubscription,
  IssueProject,
  Role,
  Permission,
  GroupedPermissions,
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
  const myProjects = ref<IssueProject[]>([]) // 내가 멤버인 프로젝트(권한 기본 적용)
  const projectResults = ref<IssueProject[]>([]) // 검색 결과 - 표시 목록용(필터 기본 값은 상태: 사용중 - 권한 기본 적용, 모든 필터 사용)

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
  const allActiveProjectsTree = computed(() => buildProjectTree(allActiveProjects.value))
  const myProjectsTree = computed(() => buildProjectTree(myProjects.value))
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
  const allActiveProjectsFlat = computed(() => flattenTree(allActiveProjectsTree.value))
  const myProjectsFlat = computed(() => flattenTree(myProjectsTree.value))
  const myActiveProjectsFlat = computed(() => myProjectsFlat.value.filter(p => p.status === '1'))
  const projectResultsFlat = computed(() => flattenTree(projectResultsTree.value))

  // 4. 셀렉박스 UI 옵션 가공 상태 - PK + SLUG 형태 (Computed)
  const getAllReadableProjects = computed(() =>
    allReadableProjectsFlat.value.map(i => ({
      value: i.pk as number,
      label:
        (i.depth && i.parent_visible ? '\u00A0'.repeat(i.depth * 2) + '» \u00A0' : '') + i.name,
      pk: i.pk as number,
      slug: i.slug as string,
      module: i.module,
      status: i.status,
    })),
  )
  const getAllActiveProjects = computed(() =>
    allActiveProjectsFlat.value.map(i => ({
      value: i.pk as number,
      label:
        (i.depth && i.parent_visible ? '\u00A0'.repeat(i.depth * 2) + '» \u00A0' : '') + i.name,
      pk: i.pk as number,
      slug: i.slug as string,
      module: i.module,
      status: i.status,
    })),
  )
  const getMyProjects = computed(() =>
    myProjectsFlat.value.map(i => ({
      value: i.pk as number,
      label:
        (i.depth && i.parent_visible ? '\u00A0'.repeat(i.depth * 2) + '» \u00A0' : '') + i.name,
      pk: i.pk as number,
      slug: i.slug as string,
      module: i.module,
      status: i.status,
    })),
  )
  const getMyActiveProjects = computed(() =>
    myActiveProjectsFlat.value.map(i => ({
      value: i.pk as number,
      label:
        (i.depth && i.parent_visible ? '\u00A0'.repeat(i.depth * 2) + '» \u00A0' : '') + i.name,
      pk: i.pk as number,
      slug: i.slug as string,
      module: i.module,
      status: i.status,
    })),
  )

  const getAllReadableProjectSlugs = computed(() =>
    getAllReadableProjects.value.map(p => ({
      value: p.slug,
      label: p.label,
    })),
  )
  const getAllActiveProjectSlugs = computed(() =>
    getAllActiveProjects.value.map(p => ({
      value: p.slug,
      label: p.label,
    })),
  )
  const getMyProjectSlugs = computed(() =>
    getMyProjects.value.map(p => ({
      value: p.slug,
      label: p.label,
    })),
  )
  const getMyActiveProjectSlugs = computed(() =>
    getMyActiveProjects.value.map(p => ({
      value: p.slug,
      label: p.label,
    })),
  )

  const getDevProjects = computed(() =>
    myProjectsFlat.value
      .filter(i => i.type === '2' && i.project !== null && i.project !== undefined)
      .map(i => ({
        value: i.project as number,
        label:
          (i.depth && i.parent_visible ? '\u00A0'.repeat(i.depth * 2) + '» \u00A0' : '') + i.name,
        slug: i.slug as string,
        module: i.module,
      })),
  )

  // actions
  let fetchProjectSeq = 0

  const fetchAllProjectList = async (
    type: '' | '1' | '2' | '3' = '',
    company: '' | number = '',
  ) => {
    const params: Record<string, string | number> = {
      status__exclude: '9',
      limit: 500,
    }
    if (type) params.type = type
    if (company) params.company = company
    return await api
      .get('/issue-project/', { params })
      .then(res => (allReadableProjects.value = res.data.results ?? res.data ?? []))
      .catch(err => errorHandle(err))
  }

  const fetchIssueProjectList = async (payload: ProjectFilter) => {
    activeFilters.value = { ...payload }
    const params: Record<string, string | number | boolean> = { limit: 500 }
    if (payload.company) params.company = payload.company
    if (payload.status) params.status = payload.status
    else if (payload.status__exclude) params.status__exclude = payload.status__exclude
    if (payload.parent__isnull !== undefined) params.parent__isnull = payload.parent__isnull
    if (payload.parent) params.parent__slug = payload.parent
    else if (payload.parent__exclude) params.parent__exclude = payload.parent__exclude
    if (payload.project) params.project = payload.project
    else if (payload.project__exclude) params.project__exclude = payload.project__exclude
    if (payload.is_public) params.is_public = payload.is_public
    else if (payload.is_public__exclude) params.is_public__exclude = payload.is_public__exclude
    if (payload.is_hidden !== undefined) params.is_hidden = payload.is_hidden
    if (payload.include_hidden) params.include_hidden = true
    if (payload.name) params.name = payload.name
    else if (payload.name__exclude) params.name__exclude = payload.name__exclude
    else if (payload.name__startswith) params.name__startswith = payload.name__startswith
    else if (payload.name__endswith) params.name__endswith = payload.name__endswith
    else if (payload.name__isnull !== undefined) params.name__isnull = payload.name__isnull

    if (payload.member) params.members__user = payload.member

    if (payload.description) params.description = payload.description
    else if (payload.description__exclude) params.description__exclude = payload.description__exclude
    else if (payload.description__startswith)
      params.description__startswith = payload.description__startswith
    else if (payload.description__endswith)
      params.description__endswith = payload.description__endswith
    else if (payload.description__isnull !== undefined)
      params.description__isnull = payload.description__isnull

    if (payload.from_created) params.from_created = payload.from_created
    if (payload.to_created) params.to_created = payload.to_created
    if (payload.from_updated) params.from_updated = payload.from_updated
    if (payload.to_updated) params.to_updated = payload.to_updated

    if (payload.bookmark !== undefined) params.bookmark = payload.bookmark
    if (payload.my_project !== undefined) params.my_project = payload.my_project

    return await api
      .get('/issue-project/', { params })
      .then(res => (projectResults.value = res.data.results ?? res.data ?? []))
      .catch(err => errorHandle(err))
  }

  const fetchMyProjectsList = async () => {
    return await api
      .get(`/issue-project/my_projects/`)
      .then(res => (myProjects.value = res.data))
      .catch(err => errorHandle(err))
  }

  const fetchIssueProject = (slug: string) => {
    const seq = ++fetchProjectSeq
    return api
      .get(`/issue-project/${slug}/`)
      .then(async res => {
        if (seq !== fetchProjectSeq) return res.data
        currentProject.value = res.data
        permStore.setProjectPermissions(res.data.my_perms || [])
        permStore.setProjectRole(res.data.my_role || null)
        if (
          res.data.company &&
          typeof res.data.company === 'number' &&
          comStore.company?.pk !== res.data.company
        ) {
          await comStore.fetchCompany(res.data.company)
        }
        return res.data
      })
      .catch(err => {
        if (seq === fetchProjectSeq) {
          currentProject.value = null
          permStore.setProjectPermissions([])
          permStore.setProjectRole(null)
        }
        errorHandle(err)
        return null
      })
  }

  const removeIssueProject = () => {
    fetchProjectSeq += 1
    currentProject.value = null
    permStore.setProjectPermissions([])
    permStore.setProjectRole(null)
  }

  const clearProjectResults = () => {
    projectResults.value = []
  }

  const createIssueProject = (payload: IssueProject) =>
    api
      .post(`/issue-project/`, payload)
      .then(async res => {
        await Promise.all([
          fetchIssueProject(res.data.slug),
          fetchAllProjectList(),
          fetchMyProjectsList(),
        ])
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updateIssueProject = (payload: IssueProject) =>
    api
      .put(`/issue-project/${payload.slug}/`, payload)
      .then(async res => {
        await Promise.all([
          fetchIssueProject(res.data.slug),
          fetchAllProjectList(),
          fetchMyProjectsList(),
        ])
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

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
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  }

  const updateMembers = async (payload: {
    slug: string
    users: number[]
    roles: number[]
    del_mem?: number
  }) => {
    return await api
      .post(`/issue-project/${payload.slug}/update_members/`, payload)
      .then(async res => {
        await Promise.all([fetchIssueProject(payload.slug), fetchMyProjectsList()])
        message('success', '성공!', '구성원 정보가 업데이트되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  }

  const deleteIssueProject = (slug: string) =>
    api
      .delete(`/issue-project/${slug}/`)
      .then(async res => {
        if (currentProject.value?.slug === slug) {
          removeIssueProject()
        }
        await Promise.all([
          fetchIssueProjectList({ ...activeFilters.value }),
          fetchAllProjectList(),
          fetchMyProjectsList(),
        ])
        if (res.data && res.data.action === 'archived') {
          message(
            'warning',
            '잠금보관 안내',
            res.data.message || "이력이 보존되어 '잠금보관' 처리되었습니다.",
          )
        } else {
          message('danger', '삭제 완료', '해당 워크스페이스가 성공적으로 삭제되었습니다.')
        }
        return res.data ?? { action: 'deleted' }
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const toggleProjectClose = (slug: string) =>
    api
      .post(`/issue-project/${slug}/toggle_close/`)
      .then(async res => {
        const tasks: Promise<unknown>[] = [
          fetchIssueProjectList({ ...activeFilters.value }),
          fetchAllProjectList(),
          fetchMyProjectsList(),
        ]
        if (currentProject.value?.slug === slug) {
          tasks.push(fetchIssueProject(slug))
        }
        await Promise.all(tasks)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const toggleProjectLock = (slug: string) =>
    api
      .post(`/issue-project/${slug}/toggle_lock/`)
      .then(async res => {
        const tasks: Promise<unknown>[] = [
          fetchIssueProjectList({ ...activeFilters.value }),
          fetchAllProjectList(),
          fetchMyProjectsList(),
        ]
        if (currentProject.value?.slug === slug) {
          tasks.push(fetchIssueProject(slug))
        }
        await Promise.all(tasks)
        message('warning', '상태 변경 완료', '워크스페이스 잠금보관 상태가 변경되었습니다.')
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const toggleProjectPublic = (slug: string, showMessage = false) =>
    api
      .post(`/issue-project/${slug}/toggle_public/`)
      .then(async res => {
        const tasks: Promise<unknown>[] = [fetchAllProjectList()]
        if (currentProject.value?.slug === slug) {
          tasks.push(fetchIssueProject(slug))
        }
        if (projectResults.value.length > 0) {
          tasks.push(fetchIssueProjectList({ ...activeFilters.value }))
        }
        await Promise.all(tasks)
        if (showMessage) message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  // Role & Permission states & getters
  const role = ref<Role | null>(null)
  const roleList = ref<Role[]>([])
  const getRoles = computed(() => roleList.value.map(r => ({ value: r.pk, label: r.name })))

  const fetchRole = (pk: number) =>
    api
      .get(`/role/${pk}/`)
      .then(res => (role.value = res.data))
      .catch(err => errorHandle(err))

  const fetchRoleList = (category?: 'work_space' | 'ibs_hq_manage' | 'ibs_pr_manage') => {
    const params: Record<string, string | number> = { limit: 500 }
    if (category) params.category = category
    return api
      .get('/role/', { params })
      .then(res => (roleList.value = res.data.results ?? res.data ?? []))
      .catch(err => errorHandle(err))
  }

  const createRole = (payload: Partial<Role>) =>
    api
      .post(`/role/`, payload)
      .then(async res => {
        await fetchRoleList()
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updateRole = (payload: Partial<Role>) =>
    api
      .put(`/role/${payload.pk}/`, payload)
      .then(async res => {
        await Promise.all([fetchRoleList(), fetchMyProjectsList()])
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const patchRole = (payload: { pk: number; permissions: number[] }) =>
    api
      .patch(`/role/${payload.pk}/`, payload)
      .then(async res => {
        await Promise.all([fetchRoleList(), fetchMyProjectsList()])
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteRole = (pk: number) =>
    api
      .delete(`/role/${pk}/`)
      .then(async () => {
        await Promise.all([fetchRoleList(), fetchMyProjectsList()])
        message('warning', '알림!', '해당 역할이 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const permissionList = ref<Permission[]>([])
  const groupedPermissions = ref<GroupedPermissions | null>(null)

  const fetchPermissionList = async (
    category?: 'work_space' | 'ibs_hq_manage' | 'ibs_pr_manage',
  ) => {
    const params: Record<string, string | number> = { limit: 500 }
    if (category) params.category = category
    try {
      const res = await api.get('/permission/', { params })
      return (permissionList.value = res.data.results || res.data)
    } catch (err: unknown) {
      return errorHandle(err)
    }
  }

  const fetchGroupedPermissions = async () => {
    try {
      const [rawRes, groupedRes] = await Promise.all([
        api.get('/permission/', { params: { limit: 500 } }),
        api.get('/permission/grouped/'),
      ])
      permissionList.value = rawRes.data.results || rawRes.data
      groupedPermissions.value = groupedRes.data
    } catch (err: unknown) {
      return errorHandle(err)
    }
  }

  // member states & getters
  const member = ref<Member | null>(null)
  const memberList = ref<Member[]>([])

  const fetchMember = (pk: number) =>
    api
      .get(`/member/${pk}/`)
      .then(res => (member.value = res.data))
      .catch(err => errorHandle(err))

  const fetchMemberList = (user?: number) => {
    const params: Record<string, number> = { limit: 500 }
    if (user !== undefined) params.user = user
    return api
      .get('/member/', { params })
      .then(res => (memberList.value = res.data.results ?? res.data ?? []))
      .catch(err => errorHandle(err))
  }

  const projectMembers = ref<ProjectMember[]>([])

  const fetchProjectMembers = (slug: string) =>
    api
      .get(`/issue-project/${slug}/members/`)
      .then(res => (projectMembers.value = res.data))
      .catch(err => errorHandle(err))

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
        if (currentProject.value?.slug === payload.slug) {
          await fetchIssueProject(payload.slug)
        }
        await fetchMember(res.data.pk)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
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
        if (res.data?.project?.slug && currentProject.value?.slug === res.data.project.slug) {
          await fetchIssueProject(res.data.project.slug)
        }
        await fetchMember(res.data.pk)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })
  }

  const deleteMember = async (pk: number, userPk?: number) => {
    return api
      .delete(`/member/${pk}/`)
      .then(async () => {
        await fetchMemberList(userPk)
        message('warning', '알림!', '해당 구성원이 워크스페이스에서 제거되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })
  }

  // subscribed_projects
  const subscribedProjects = ref<ProjectSubscription[]>([])

  const fetchSubscribedProjects = async (userPk: number) =>
    api
      .get('/project-subscription/', { params: { user: userPk } })
      .then(res => (subscribedProjects.value = res.data?.results ?? res.data ?? []))
      .catch(err => errorHandle(err))

  const createSubscribedProjects = async (payload: { user: number; project_ids: number[] }) =>
    api
      .post(`/project-subscription/bulk-update/`, payload)
      .then(async res => {
        subscribedProjects.value = res.data?.results ?? res.data ?? []
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  // bookmarked_projects
  const bookmarkedProjects = ref<ProjectBookmark[]>([])

  const fetchBookmarks = async () =>
    api
      .get('/project-bookmark/', { params: { limit: 500 } })
      .then(res => (bookmarkedProjects.value = res.data.results ?? res.data ?? []))
      .catch(err => errorHandle(err))

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
      .catch(err => errorHandle(err))
  }

  const reorderBookmarks = async (orderedIds: number[]) =>
    api
      .post(`/project-bookmark/reorder/`, { ordered_ids: orderedIds })
      .then(res => (bookmarkedProjects.value = res.data))
      .catch(err => errorHandle(err))

  // version states & getters
  const version = ref<Version | null>(null)
  const versionList = ref<Version[]>([])
  const getVersions = computed(() =>
    versionList.value.map(v => ({
      value: v.pk as number,
      label: `${v.project?.name} - ${v.name}`,
    })),
  )

  const removeVersion = () => (version.value = null)

  const fetchVersion = (pk: number) =>
    api
      .get(`/version/${pk}/`)
      .then(res => (version.value = res.data))
      .catch(err => errorHandle(err))

  const fetchVersionList = async (
    payload?:
      | string
      | {
          project?: string
          status?: '' | '1' | '2' | '3'
          exclude?: '' | '1' | '2' | '3'
          search?: string
          limit?: number
        },
  ) => {
    const params: Record<string, string | number> = { limit: 500 }

    if (typeof payload === 'string') {
      if (payload) params.project__slug = payload
    } else if (payload && typeof payload === 'object') {
      if (payload.project) params.project__slug = payload.project
      if (payload.status) params.status = payload.status
      if (payload.exclude) params.status__exclude = payload.exclude
      if (payload.search) params.search = payload.search
      if (payload.limit) params.limit = payload.limit
    }

    return await api
      .get('/version/', { params })
      .then(res => (versionList.value = res.data.results ?? res.data ?? []))
      .catch(err => errorHandle(err))
  }

  const createVersion = (payload: FormVersion) =>
    api
      .post(`/version/`, payload)
      .then(async res => {
        await fetchVersion(res.data.pk)
        await fetchVersionList(res.data.project.slug)
        if (currentProject.value?.slug === res.data.project.slug) {
          await fetchIssueProject(res.data.project.slug)
        }
        message()
        return res.data.pk
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updateVersion = (payload: FormVersion) =>
    api
      .put(`/version/${payload.pk}/`, payload)
      .then(async res => {
        await fetchVersion(res.data.pk)
        await fetchVersionList(res.data.project.slug)
        if (currentProject.value?.slug === res.data.project.slug) {
          await fetchIssueProject(res.data.project.slug)
        }
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteVersion = (pk: number, project = '') =>
    api
      .delete(`/version/${pk}/`)
      .then(async () => {
        await fetchVersionList({ project, status: '', exclude: '' })
        if (project && currentProject.value?.slug === project) {
          await fetchIssueProject(project)
        }
        message('warning', '알림!', '해당 단계가 삭제되었습니다!')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  const reset = () => {
    fetchProjectSeq += 1
    currentProject.value = null
    allReadableProjects.value = []
    myProjects.value = []
    projectResults.value = []
    activeFilters.value = {}
    role.value = null
    roleList.value = []
    permissionList.value = []
    groupedPermissions.value = null
    member.value = null
    memberList.value = []
    projectMembers.value = []
    subscribedProjects.value = []
    bookmarkedProjects.value = []
    version.value = null
    versionList.value = []
    permStore.reset()
  }

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
    myActiveProjectsFlat,

    allActiveProjects,

    getAllReadableProjects,
    getAllActiveProjects,
    getMyProjects,
    getMyActiveProjects,
    getDevProjects,

    getAllReadableProjectSlugs,
    getAllActiveProjectSlugs,
    getMyProjectSlugs,
    getMyActiveProjectSlugs,

    fetchAllProjectList,
    fetchIssueProjectList,
    fetchMyProjectsList,
    fetchIssueProject,
    removeIssueProject,
    clearProjectResults,
    createIssueProject,
    updateIssueProject,
    patchIssueProject,
    updateMembers,
    deleteIssueProject,
    toggleProjectClose,
    toggleProjectLock,
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
    groupedPermissions,
    fetchPermissionList,
    fetchGroupedPermissions,

    reset,

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
    removeVersion,
    fetchVersion,
    fetchVersionList,
    createVersion,
    updateVersion,
    deleteVersion,
  }
})
