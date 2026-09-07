import { computed, unref, type Ref, type ComputedRef } from 'vue'
import { usePerms } from '@/composables/usePerms'

export const pageTitle = '분양 대행 관리'

export const navMenuAll = [
  '계약 실적 관리',
  '수수료 정산 관리',
  '수수료 지급 관리',
  '수수료 정책 관리',
  '영업 조직 관리',
]

// 기존 정적 배열 호환용
export const navMenu = navMenuAll

/**
 * 사이드바 메뉴 권한 매핑과 동일한 기준(sales.* 권한)으로 상단 탭 메뉴를 동적 필터링하는 컴포저블
 *
 * 권한 매핑:
 * - 계약 실적 관리: sales.read
 * - 수수료 정산 관리: sales.settle
 * - 수수료 지급 관리: sales.payout
 * - 수수료 정책 관리: sales.policy
 * - 영업 조직 관리: sales.manage
 *
 * @param projectRef (선택) 프로젝트 ID Ref 또는 원시값. 미전달 시 전역 권한 기준으로 판정.
 */
export const useSalesNavMenu = (
  projectRef?: Ref<number | undefined | null> | number | null,
): ComputedRef<string[]> => {
  const { can, PERM } = usePerms()

  return computed(() => {
    const projId = projectRef ? (unref(projectRef) ?? undefined) : undefined
    const menus: string[] = []

    if (can(PERM.SALES_READ, projId)) {
      menus.push('계약 실적 관리')
    }
    if (can(PERM.SALES_SETTLE, projId)) {
      menus.push('수수료 정산 관리')
    }
    if (can(PERM.SALES_PAYOUT, projId)) {
      menus.push('수수료 지급 관리')
    }
    if (can(PERM.SALES_POLICY, projId)) {
      menus.push('수수료 정책 관리')
    }
    if (can(PERM.SALES_MANAGE, projId)) {
      menus.push('영업 조직 관리')
    }

    return menus
  })
}
