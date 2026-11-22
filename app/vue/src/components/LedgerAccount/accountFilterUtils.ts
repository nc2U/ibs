import type { AccountPicker } from '@/store/types/comLedger.ts'

export type AccountCateType =
  'asset' | 'liability' | 'equity' | 'revenue' | 'expense' | 'transfer' | 'cancel' | null

export type AccountSortType = 'deposit' | 'withdraw' | null

/** 조건(predicate)에 매칭되는 실제 계정과 그 부모 카테고리 체인만 추출 (순환 참조 방어) */
const filterWithParents = (
  options: AccountPicker[],
  predicate: (option: AccountPicker) => boolean,
): AccountPicker[] => {
  const matchingAccounts = options.filter(opt => !opt.is_cate_only && predicate(opt))
  const neededParents = new Set<number>()

  matchingAccounts.forEach(account => {
    let currentParent = account.parent
    let currentOption = currentParent ? options.find(opt => opt.value === currentParent) : undefined

    while (currentOption) {
      if (neededParents.has(currentOption.value)) break
      neededParents.add(currentOption.value)
      if (currentOption.parent === null) break
      currentParent = currentOption.parent
      currentOption = options.find(opt => opt.value === currentParent)
    }
  })

  return options.filter(
    opt =>
      (!opt.is_cate_only && predicate(opt)) || (opt.is_cate_only && neededParents.has(opt.value)),
  )
}

/** cateType / sortType 조건에 따라 계정 목록 필터링 */
export const filterAccountOptions = (
  options: AccountPicker[],
  filters: { cateType?: AccountCateType; sortType?: AccountSortType },
): AccountPicker[] => {
  let filtered = options
  if (filters.cateType) {
    const targetCate = filters.cateType
    filtered = filterWithParents(filtered, opt => opt.category === targetCate)
  }
  if (filters.sortType) {
    const targetDirection = filters.sortType === 'deposit' ? '입금' : '출금'
    filtered = filterWithParents(filtered, opt => opt.direction === targetDirection)
  }
  return filtered
}

/** 검색어 매칭 (부모-자식 계층 유지) */
export const searchAccountOptions = (
  options: AccountPicker[],
  rawQuery: string,
): AccountPicker[] => {
  const query = rawQuery.trim().toLowerCase()
  if (!query) return options

  const matchingIds = new Set<number>()

  options.forEach(option => {
    if (option.label.toLowerCase().includes(query)) {
      matchingIds.add(option.value)

      let currentParent = option.parent
      let parentOption = currentParent
        ? options.find(opt => opt.value === currentParent)
        : undefined

      while (parentOption) {
        if (matchingIds.has(parentOption.value)) break
        matchingIds.add(parentOption.value)
        if (parentOption.parent === null) break
        currentParent = parentOption.parent
        parentOption = options.find(opt => opt.value === currentParent)
      }
    }
  })

  options.forEach(option => {
    if (option.is_cate_only) {
      const hasMatchingChildren = options.some(
        child => child.parent === option.value && matchingIds.has(child.value),
      )
      if (hasMatchingChildren) matchingIds.add(option.value)
    }
  })

  return options.filter(option => matchingIds.has(option.value))
}
