import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project'
import type { MyRole } from '@/store/types/work_project.ts'
import { PERM, type PermissionCode } from '@/store/constants/permissions'

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
    workStore.myProjects.forEach((p: any) => {
      if (Array.isArray(p.my_perms)) {
        p.my_perms.forEach((perm: PermissionCode) => set.add(perm))
      }
    })
    return set
  })

  // 프로젝트 권한 데이터 세팅 (프로젝트 로드 시 호출)
  const setProjectPermissions = (perms: PermissionCode[]) => (projectPermSet.value = new Set(perms))

  // 프로젝트 역할 속성 세팅 (프로젝트 로드 시 호출)
  const setProjectRole = (role: MyRole | null) => (projectRole.value = role)

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
      const targetProj = workStore.allReadableProjectsFlat.find(
        (p: any) => p.pk === projectIdentifier || p.slug === projectIdentifier,
      )
      return (
        targetProj?.my_role || {
          assignable: false,
          issue_visible: 'NOP',
          user_visible: 'NOP',
        }
      )
    }

    // 3. active 프로젝트가 없는 상태(전역 구간)라면,
    // 사용자가 가진 모든 프로젝트 및 일반사용자(PK 2)의 권한 중 가장 높은 수준의 옵션을 병합해 반환
    if (!workStore.currentProject) {
      const issue_visibility_order: Record<string, number> = { ALL: 3, PUB: 2, PRI: 1, NOP: 0 }
      const user_visibility_order: Record<string, number> = { ALL: 2, PRJ: 1, NOP: 0 }

      const authRole = workStore.roleList.find((r: any) => r.pk === 2)

      let assignable = authRole ? authRole.assignable : false
      let best_issue_visible: 'ALL' | 'PUB' | 'PRI' | 'NOP' = authRole
        ? authRole.issue_visible
        : 'NOP'
      let best_user_visible: 'ALL' | 'PRJ' | 'NOP' = authRole ? authRole.user_visible : 'NOP'

      workStore.myProjectsFlat.forEach((p: any) => {
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
    if (visibility === 'NOP') {
      return userId !== undefined && userId === accountStore.userInfo?.pk
    }
    return true
  }

  const isReadOnlyPerm = (c: PermissionCode) => {
    return (
      c.endsWith('.read') ||
      c.includes('.view') ||
      c.includes('.download') ||
      c.startsWith('project.')
    )
  }

  // 본사 관리(HQ Manage) 보안 권한 여부 확인 (hq.* 프리픽스 기준: workManager보다 우선하여 실제 권한 검증 필수)
  const isHqPerm = (c: PermissionCode) => {
    return c.startsWith('hq.')
  }

  // 권한 체크 로직
  const can = (code: PermissionCode | PermissionCode[], projectIdentifier?: number | string) => {
    const check = (c: PermissionCode) => {
      // 대상 프로젝트 객체 찾기
      const targetProj =
        projectIdentifier !== undefined
          ? workStore.allReadableProjectsFlat.find(
              (p: any) => p.pk === projectIdentifier || p.slug === projectIdentifier,
            )
          : workStore.currentProject

      // [닫힘('2')] 워크스페이스: 읽기 전용 권한 이외의 쓰기 권한 차단
      if (targetProj?.status === '2' && !isReadOnlyPerm(c)) {
        return false
      }
      // [잠금보관('9')] 워크스페이스: 프로젝트 관리 외 권한 차단
      if (targetProj?.status === '9' && !c.startsWith('project.')) {
        return false
      }

      // 슈퍼유저는 전체 권한 허용
      if (accountStore.superAuth) return true

      // 1. 업무 관리자(workManager)인 경우: 일반 워크스페이스/프로젝트 권한은 허용하되, 본사 관리(HQ) 권한은 제외
      if (accountStore.workManager && !isHqPerm(c)) return true

      // 공개 프로젝트(is_public=true)의 읽기 권한(*.read)은 비멤버도 기본 열람 허용 (work_core 영역)
      if (targetProj?.is_public && (c.endsWith('.read') || c === PERM.NEWS_READ)) {
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

    if (accountStore.workManager) {
      if (Array.isArray(code)) {
        if (code.some(c => isHqPerm(c))) {
          return code.every(c => globalPermSet.value.has(c))
        }
        return true
      }
      if (isHqPerm(code)) {
        return globalPermSet.value.has(code)
      }
      return true
    }

    if (Array.isArray(code)) return code.every(c => globalPermSet.value.has(c))
    return globalPermSet.value.has(code)
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
  }
})
