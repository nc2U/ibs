// src/components/account/useAccountSelection.ts

import { ref, computed } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import type { AccountD1, AccountD2, AccountD3 } from './keys'

export interface AccountSelectionCallbacks {
  fetchD1List: (sort: number) => Promise<void>
  fetchD2List: (d1: number) => Promise<void>
  fetchD3List: (d2: number) => Promise<void>
  getD1List: () => AccountD1[]
  getD2List: () => AccountD2[]
  getD3List: () => AccountD3[]
}

export interface InitialValues {
  sort?: 1 | 2
  account_d1?: number | null
  account_d2?: number | null
  account_d3?: number | null
}

export interface UseAccountSelectionReturn {
  // State
  sort: Ref<1 | 2>
  account_d1: Ref<number | null>
  account_d2: Ref<number | null>
  account_d3: Ref<number | null>

  // Lists
  accD1List: ComputedRef<AccountD1[]>
  accD2List: ComputedRef<AccountD2[]>
  accD3List: ComputedRef<AccountD3[]>

  // Handlers
  handleSortChange: () => Promise<void>
  handleD1Change: () => Promise<void>
  handleD2Change: () => Promise<void>
  handleD3Change: () => Promise<void>

  // Utility
  initialize: () => Promise<void>
  reset: () => void
}

export function useAccountSelection(
  callbacks: AccountSelectionCallbacks,
  initialValues?: InitialValues,
): UseAccountSelectionReturn {
  // State
  const sort = ref<1 | 2>(initialValues?.sort || 1)
  const account_d1 = ref<number | null>(initialValues?.account_d1 || null)
  const account_d2 = ref<number | null>(initialValues?.account_d2 || null)
  const account_d3 = ref<number | null>(initialValues?.account_d3 || null)

  // Lists computed
  const accD1List = computed(() => callbacks.getD1List())
  const accD2List = computed(() => callbacks.getD2List())
  const accD3List = computed(() => callbacks.getD3List())

  // Change handlers
  const handleSortChange = async () => {
    account_d1.value = null
    account_d2.value = null
    account_d3.value = null
    await callbacks.fetchD1List(sort.value)
  }

  const handleD1Change = async () => {
    account_d2.value = null
    account_d3.value = null
    if (account_d1.value) {
      await callbacks.fetchD2List(account_d1.value)
    }
  }

  const handleD2Change = async () => {
    account_d3.value = null
    if (account_d2.value) {
      await callbacks.fetchD3List(account_d2.value)
    }
  }

  const handleD3Change = () => {
    // D3 selection completed
  }

  // Initialize
  const initialize = async () => {
    if (sort.value) {
      await callbacks.fetchD1List(sort.value)
    }
    if (account_d1.value) {
      await callbacks.fetchD2List(account_d1.value)
    }
    if (account_d2.value) {
      await callbacks.fetchD3List(account_d2.value)
    }
  }

  // Reset
  const reset = () => {
    sort.value = 1
    account_d1.value = null
    account_d2.value = null
    account_d3.value = null
  }

  return {
    // State
    sort,
    account_d1,
    account_d2,
    account_d3,

    // Lists
    accD1List,
    accD2List,
    accD3List,

    // Handlers
    handleSortChange,
    handleD1Change,
    handleD2Change,
    handleD3Change,

    // Utility
    initialize,
    reset,
  }
}
