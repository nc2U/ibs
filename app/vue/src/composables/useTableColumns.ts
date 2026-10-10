import { ref, watch } from 'vue'
import type { ColumnOption } from '@/components/ColumnSelector/Index.vue'

export function useTableColumns(
  storageKey: string,
  allColumns: ColumnOption[],
  defaultKeys?: string[],
) {
  const getDefaultColumns = (): string[] => defaultKeys || allColumns.map(c => c.key)

  const getInitialColumns = (): string[] => {
    const defaultCols = getDefaultColumns()
    const validKeySet = new Set(allColumns.map(c => c.key))

    const saved = localStorage.getItem(storageKey)
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length > 0) {
          // 현재 allColumns에 존재하는 유효한 키만 필터링 (삭제/변경된 레거시 키 제거)
          const validColumns = parsed.filter(key => typeof key === 'string' && validKeySet.has(key))
          if (validColumns.length > 0) return validColumns
        }
      } catch {
        // ignore parse error and fallback to default
      }
    }
    return defaultCols
  }

  const selectedColumns = ref<string[]>(getInitialColumns())

  const resetColumns = () => {
    selectedColumns.value = getDefaultColumns()
  }

  watch(
    selectedColumns,
    nVal => {
      localStorage.setItem(storageKey, JSON.stringify(nVal))
    },
    { deep: true },
  )

  return {
    selectedColumns,
    resetColumns,
  }
}
