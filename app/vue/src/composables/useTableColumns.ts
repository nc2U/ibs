import { ref, watch } from 'vue'
import type { ColumnOption } from '@/components/ColumnSelector/Index.vue'

export function useTableColumns(
  storageKey: string,
  allColumns: ColumnOption[],
  defaultKeys?: string[],
) {
  const getInitialColumns = (): string[] => {
    const saved = localStorage.getItem(storageKey)
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed) && parsed.length > 0) return parsed
      } catch {
        // ignore parse error and fallback to default
      }
    }
    return defaultKeys || allColumns.map(c => c.key)
  }

  const selectedColumns = ref<string[]>(getInitialColumns())

  watch(
    selectedColumns,
    nVal => {
      localStorage.setItem(storageKey, JSON.stringify(nVal))
    },
    { deep: true },
  )

  return {
    selectedColumns,
  }
}
