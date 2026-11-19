import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project'
import type { IssueProject, MyRole, Role } from '@/store/types/work_project.ts'
import { PERM, type PermissionCode } from '@/store/constants/permissions'

const WORK_CORE_READ_PERMS = new Set<PermissionCode>([
  PERM.MEETING_READ,
  PERM.ISSUE_READ,
  PERM.NEWS_READ,
  PERM.DOCS_READ,
  PERM.FORUM_READ,
  PERM.CALENDAR_READ,
])

const CLOSED_WORKSPACE_ALLOWED_MGMT_PERMS = new Set<PermissionCode>([
  PERM.PROJECT_CREATE,
  PERM.PROJECT_UPDATE,
  PERM.PROJECT_PUBLIC,
  PERM.PROJECT_CLOSE,
  PERM.PROJECT_DELETE,
  PERM.PROJECT_MODULE,
])

export const usePermission = defineStore('permission', () => {
  const workStore = useWork()
  const accountStore = useAccount()
  const projectPermSet = ref<Set<PermissionCode>>(new Set())
  const projectRole = ref<MyRole | null>(null)

  // 전역 권한 Set: myProjects 원시 배열 기반으로 pre-compute
  // - myProjectsFlat(visible 필터 포함) 대신 사용 → visible 변동에 의한 오동작 방지
  // - myProjects는 App.vue onBeforeMount에서 1회 로드 후 안정적
  // - computed이므로 myProjects 변경 시에만 재계산 (페이지 이동과 무관)
  const globalPermSet = computed<Set<PermissionCode>>(() => {
    const set = new Set<PermissionCode>()
    workStore.myProjects.forEach((p: IssueProject) => {
      if (Array.isArray(p.my_perms)) {
        p.my_perms.forEach(perm => set.add(perm as PermissionCode))
      }
    })
    return set
  })

  // 프로젝트 권한 데이터 세팅 (프로젝트 로드 시 호출)
  const setProjectPermissions = (perms: PermissionCode[]) => (projectPermSet.value = new Set(perms))

  // 프로젝트 역할 속성 세팅 (프로젝트 로드 시 호출)
  const setProjectRole = (role: MyRole | null) => (projectRole.value = role)

  // 대상 프로젝트 객체 탐색 헬퍼 (pk/slug 우선 매칭 후 부동산 프로젝트 FK 폴백)
  const findTargetProject = (pid: number | string) => {
    const matchDirect = (p: IssueProject) =>
      p && (p.pk === pid || String(p.pk) === String(pid) || p.slug === pid)

    const matchRealEstate = (p: IssueProject) =>
      p &&
      p.project !== null &&
      p.project !== undefined &&
      (p.project === pid || String(p.project) === String(pid))

    return (
      workStore.myProjects.find(matchDirect) ||
      workStore.myProjectsFlat.find(matchDirect) ||
      workStore.allReadableProjects.find(matchDirect) ||
      workStore.allReadableProjectsFlat.find(matchDirect) ||
      workStore.myProjects.find(matchRealEstate) ||
      workStore.myProjectsFlat.find(matchRealEstate) ||
      workStore.allReadableProjects.find(matchRealEstate) ||
      workStore.allReadableProjectsFlat.find(matchRealEstate)
    )
  }

  // 역할 속성 조회 로직
  const getProjectRole = (projectIdentifier?: number | string): MyRole => {
    // 1. 업무 관리자(workManager)인 경우 무조건 모든 권한 최고 레벨
    if (accountStore.workManager) {
      return {
        assignable: true,
        issue_visible: 'ALL',
        user_visible: 'ALL',
      }
    }

    // 2. 특정 프로젝트 ID나 Slug가 주어졌을 때는 해당 프로젝트의 역할 정보를 반환
    if (projectIdentifier !== undefined) {
      const targetProj = findTargetProject(projectIdentifier)
      return (
        targetProj?.my_role || {
          assignable: false,
          issue_visible: 'NOP',
          user_visible: 'NOP',
        }
      )
    }

    // 3. active 프로젝트가 없는 상태(전역 구간)라면,
    // 사용자가 소속된 모든 워크스페이스의 역할 속성 중 최고 수준을 병합 (미소속 시에만 일반사용자 Role PK 2 폴백)
    if (!workStore.currentProject) {
      const issue_visibility_order: Record<string, number> = { ALL: 3, PUB: 2, PRI: 1, NOP: 0 }
      const user_visibility_order: Record<string, number> = { ALL: 2, PRJ: 1, NOP: 0 }

      const hasMemberships = workStore.myProjects.length > 0
      const authRole = !hasMemberships
        ? workStore.roleList.find((r: Role) => r.pk === 2)
        : undefined

      let assignable = authRole ? authRole.assignable : false
      let best_issue_visible: 'ALL' | 'PUB' | 'PRI' | 'NOP' = authRole
        ? authRole.issue_visible
        : 'NOP'
      let best_user_visible: 'ALL' | 'PRJ' | 'NOP' = authRole ? authRole.user_visible : 'NOP'

      workStore.myProjects.forEach((p: IssueProject) => {
        if (p.my_role) {
          if (p.my_role.assignable) assignable = true
          if (
            issue_visibility_order[p.my_role.issue_visible] >
            issue_visibility_order[best_issue_visible]
          ) {
            best_issue_visible = p.my_role.issue_visible
          }
          if (
            user_visibility_order[p.my_role.user_visible] > user_visibility_order[best_user_visible]
          ) {
            best_user_visible = p.my_role.user_visible
          }
        }
      })

      return {
        assignable,
        issue_visible: best_issue_visible,
        user_visible: best_user_visible,
      }
    }

    // 4. 활성 프로젝트가 있는 경우, 캐시된 projectRole 반환
    return (
      projectRole.value || {
        assignable: false,
        issue_visible: 'NOP',
        user_visible: 'NOP',
      }
    )
  }

  // 개별 역할 속성에 접근하기 위한 헬퍼 함수들
  const isAssignable = (projectIdentifier?: number | string) =>
    getProjectRole(projectIdentifier).assignable

  const getIssueVisible = (projectIdentifier?: number | string) =>
    getProjectRole(projectIdentifier).issue_visible

  const getUserVisible = (projectIdentifier?: number | string) =>
    getProjectRole(projectIdentifier).user_visible

  const canViewUser = (userId?: number) => {
    if (accountStore.workManager) return true
    const visibility = getUserVisible()
    if (visibility === 'ALL') return true
    if (userId !== undefined && userId === accountStore.userInfo?.pk) return true
    if (visibility === 'NOP') return false
    if (visibility === 'PRJ' && userId !== undefined) {
      return workStore.myProjects.some(p =>
        p.all_members?.some(m => m.user?.pk === userId),
      )
    }
    return true
  }

  const isReadOnlyPerm = (c: PermissionCode) => {
    return c.endsWith('.read') || c.includes('.view') || c.includes('.download') || c === PERM.NEWS_READ
  }

  // 본사 관리(HQ Manage) 보안 권한 여부 확인 (hq.* 프리픽스 기준: workManager보다 우선하여 실제 권한 검증 필수)
  const isHqPerm = (c: PermissionCode) => {
    return c.startsWith('hq.')
  }

  // 실제 Staff(직원) 인스턴스 등록이 필수인 권한 판별 (슈퍼유저 제외한 일반 유저는 Staff 등록 필수)
  const requiresStaff = (c: PermissionCode) => {
    return (
      c === PERM.HQ_HR_WORK_CREATE || c === PERM.HQ_HR_WORK_UPDATE || c === PERM.HQ_HR_WORK_DELETE
    )
  }

  // 권한 체크 로직
  const can = (code: PermissionCode | PermissionCode[], projectIdentifier?: number | string) => {
    const check = (c: PermissionCode) => {
      // 대상 프로젝트 객체 찾기
      const targetProj =
        projectIdentifier !== undefined
          ? findTargetProject(projectIdentifier)
          : workStore.currentProject

      // [닫힘('2')] 워크스페이스: 하위 리소스 쓰기 권한은 슈퍼유저/관리자 포함 차단 (백엔드 work_perms.py 정합)
      if (
        targetProj?.status === '2' &&
        !isReadOnlyPerm(c) &&
        !CLOSED_WORKSPACE_ALLOWED_MGMT_PERMS.has(c)
      ) {
        return false
      }
      // [잠금보관('9')] 워크스페이스: 관리자 전용 프로젝트 수정/삭제 외 모든 권한 차단
      if (targetProj?.status === '9') {
        const isAdmin = Boolean(accountStore.superAuth || accountStore.workManager)
        if (!(isAdmin && (c === PERM.PROJECT_UPDATE || c === PERM.PROJECT_DELETE))) {
          return false
        }
      }

      // 슈퍼유저는 전체 권한 허용 (위 상태 제한 제외)
      if (accountStore.superAuth) return true

      // Staff 인스턴스 연결이 필수인 권한의 경우, 미등록 일반 사용자는 차단
      if (requiresStaff(c) && !accountStore.userInfo?.has_staff) {
        return false
      }

      // 1. 업무 관리자(workManager)인 경우: 일반 워크스페이스/프로젝트 권한은 허용하되, 본사 관리(HQ) 권한은 제외
      if (accountStore.workManager && !isHqPerm(c)) return true

      // 공개 프로젝트(is_public=true)의 work_core 읽기 권한만 비멤버 기본 열람 허용 (HQ/부동산 기밀 읽기 제외)
      if (targetProj?.is_public && WORK_CORE_READ_PERMS.has(c)) {
        return true
      }

      // 특정 프로젝트 ID나 Slug가 주어졌을 때는 해당 프로젝트의 권한을 체크
      if (projectIdentifier !== undefined) {
        return targetProj?.my_perms ? targetProj.my_perms.includes(c) : false
      }

      // active 프로젝트가 없는 상태(전역 구간)에서는 globalPermSet으로 판정
      if (!workStore.currentProject) {
        return globalPermSet.value.has(c)
      }

      // 프로젝트별 권한 세트에서 체크
      return projectPermSet.value.has(c)
    }

    if (Array.isArray(code)) return code.every(c => check(c))
    return check(code)
  }

  // 전역 권한 체크
  // canGlobal: globalPermSet(내가 멤버인 모든 프로젝트의 권한 합집합)만으로 판정
  // 본사 관리(HQ) 권한(hr_work.*, ledger.com_*)은 workManager보다 우선하여 실제 보유 권한으로만 판정
  const canGlobal = (code: PermissionCode | PermissionCode[]) => {
    if (accountStore.superAuth) return true

    const checkOne = (c: PermissionCode) => {
      // Staff 인스턴스 연결이 필수인 권한의 경우, 미등록 일반 사용자는 차단
      if (requiresStaff(c) && !accountStore.userInfo?.has_staff) {
        return false
      }

      if (accountStore.workManager && !isHqPerm(c)) {
        return true
      }

      return globalPermSet.value.has(c)
    }

    if (Array.isArray(code)) return code.every(c => checkOne(c))
    return checkOne(code)
  }

  const reset = () => {
    projectPermSet.value = new Set()
    projectRole.value = null
  }

  return {
    projectPermSet,
    setProjectPermissions,
    projectRole,
    setProjectRole,
    getProjectRole,
    isAssignable,
    getIssueVisible,
    getUserVisible,
    canViewUser,
    can,
    canGlobal,
    globalPermSet,
    reset,
  }
})
