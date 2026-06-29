import { usePermission } from '@/store/pinia/work_permission'
import { PERM } from '@/store/constants/permissions'

export function usePerms() {
  const permStore = usePermission()

  const can = permStore.can
  const setProjectPermissions = permStore.setProjectPermissions
  const isAssignable = permStore.isAssignable
  const getIssueVisible = permStore.getIssueVisible
  const getUserVisible = permStore.getUserVisible
  const canViewUser = permStore.canViewUser

  return {
    can,
    setProjectPermissions,
    isAssignable,
    getIssueVisible,
    getUserVisible,
    canViewUser,
    PERM,
  }
}
