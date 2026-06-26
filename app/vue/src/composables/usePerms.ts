import { usePermission } from '@/store/pinia/work_permission';
import { PERM } from '@/store/constants/permissions';

export function usePerms() {
  const permStore = usePermission();
  
  const can = permStore.can;
  const setGlobalProjectCreatePerm = permStore.setGlobalProjectCreatePerm;
  const setProjectPermissions = permStore.setProjectPermissions;

  return { can, setGlobalProjectCreatePerm, setProjectPermissions, PERM };
}
