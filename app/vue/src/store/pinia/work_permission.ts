import { defineStore } from 'pinia'
import { ref } from 'vue'
import { PERM, type PermissionCode } from '@/store/constants/permissions'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project'

export const usePermission = defineStore('permission', () => {
  const accountStore = useAccount()
  // 전역 프로젝트 생성 권한 플래그
  const canCreateProject = ref(false)
  const projectPermSet = ref<Set<PermissionCode>>(new Set())

  // 전역 프로젝트 생성 권한 설정 (로그인 시/앱 시작 시 호출)
  const setGlobalProjectCreatePerm = (can: boolean) => (canCreateProject.value = can)

  // 프로젝트 권한 데이터 세팅 (프로젝트 로드 시 호출)
  const setProjectPermissions = (perms: PermissionCode[]) => (projectPermSet.value = new Set(perms))

  // 권한 체크 로직
  const can = (code: PermissionCode | PermissionCode[], projectIdentifier?: number | string) => {
    // 1. 업무 관리자(workManager)인 경우 무조건 모든 권한 허용
    if (accountStore.workManager) return true

    const check = (c: PermissionCode) => {
      // 전역 생성 권한 체크
      if (c === PERM.PROJECT_CREATE && canCreateProject.value) return true

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
    canCreateProject,
    projectPermSet,
    setGlobalProjectCreatePerm,
    setProjectPermissions,
    can,
  }
})
