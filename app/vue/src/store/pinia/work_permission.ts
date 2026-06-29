import { defineStore } from 'pinia'
import { ref } from 'vue'
import { type PermissionCode } from '@/store/constants/permissions'
import type { MyRole } from '@/store/types/work_project.ts'
import { useWork } from '@/store/pinia/work_project'
import { useAccount } from '@/store/pinia/account'

export const usePermission = defineStore('permission', () => {
  const accountStore = useAccount()
  const projectPermSet = ref<Set<PermissionCode>>(new Set())
  const projectRole = ref<MyRole | null>(null)

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

    const workStore = useWork()

    // 2. 특정 프로젝트 ID나 Slug가 주어졌을 때는 해당 프로젝트의 역할 정보를 반환
    if (projectIdentifier !== undefined) {
      const targetProj = workStore.AllIssueProjects.find(
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
    // 사용자가 가진 모든 프로젝트 중 가장 높은 수준의 옵션을 병합해 반환
    if (!workStore.issueProject) {
      const issue_visibility_order: Record<string, number> = { ALL: 3, PUB: 2, PRI: 1, NOP: 0 }
      const user_visibility_order: Record<string, number> = { ALL: 2, PRJ: 1, NOP: 0 }

      let assignable = false
      let best_issue_visible: 'ALL' | 'PUB' | 'PRI' | 'NOP' = 'NOP'
      let best_user_visible: 'ALL' | 'PRJ' | 'NOP' = 'NOP'

      workStore.AllIssueProjects.forEach((p: any) => {
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

  // 권한 체크 로직
  const can = (code: PermissionCode | PermissionCode[], projectIdentifier?: number | string) => {
    // 1. 업무 관리자(workManager)인 경우 무조건 모든 권한 허용
    if (accountStore.workManager) return true

    const check = (c: PermissionCode) => {
      const workStore = useWork()

      // 특정 프로젝트 ID나 Slug가 주어졌을 때는 해당 프로젝트의 권한을 체크
      if (projectIdentifier !== undefined) {
        const targetProj = workStore.AllIssueProjects.find(
          (p: any) => p.pk === projectIdentifier || p.slug === projectIdentifier,
        )
        return targetProj?.my_perms ? targetProj.my_perms.includes(c) : false
      }

      // active 프로젝트가 없는 상태(전역 구간)라면,
      // 사용자가 권한을 가진 프로젝트가 최소 하나라도 있으면 true로 반환
      if (!workStore.issueProject)
        return workStore.AllIssueProjects.some((p: any) => p.my_perms && p.my_perms.includes(c))

      // 프로젝트별 권한 세트에서 체크
      return projectPermSet.value.has(c)
    }

    if (Array.isArray(code)) return code.every(c => check(c))
    return check(code)
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
  }
})
