import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { PermissionCode } from '@/store/constants/permissions';

export const usePermission = defineStore('permission', () => {
  // 권한을 Set으로 관리하여 검색 성능 O(1) 보장
  const myPermSet = ref<Set<PermissionCode>>(new Set());

  // 권한 데이터 세팅 (프로젝트 로드 시 호출)
  const setPermissions = (perms: PermissionCode[]) => {
    myPermSet.value = new Set(perms);
  };

  // 권한 체크 로직
  const can = (code: PermissionCode | PermissionCode[]) => {
    if (Array.isArray(code)) {
      return code.every(c => myPermSet.value.has(c));
    }
    return myPermSet.value.has(code);
  };

  return { myPermSet, setPermissions, can };
});
