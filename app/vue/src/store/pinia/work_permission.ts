import { defineStore } from 'pinia'
import { ref } from 'vue'
import { PERM, type PermissionCode } from '@/store/constants/permissions'

export const usePermission = defineStore('permission', () => {
  // 전역 프로젝트 생성 권한 플래그
  const canCreateProject = ref(false)
  const projectPermSet = ref<Set<PermissionCode>>(new Set())

  // 전역 프로젝트 생성 권한 설정 (로그인 시/앱 시작 시 호출)
  const setGlobalProjectCreatePerm = (can: boolean) => {
    canCreateProject.value = can
  }

  // 프로젝트 권한 데이터 세팅 (프로젝트 로드 시 호출)
  const setProjectPermissions = (perms: PermissionCode[]) => {
    projectPermSet.value = new Set(perms)
  }

  // 권한 체크 로직
  const can = (code: PermissionCode | PermissionCode[]) => {
    const check = (c: PermissionCode) => {
      // 전역 생성 권한 체크
      if (c === PERM.PROJECT_CREATE && canCreateProject.value) return true
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
