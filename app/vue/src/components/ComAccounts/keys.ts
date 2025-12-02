// src/components/account/keys.ts

import type { InjectionKey, Ref, ComputedRef } from 'vue'

export interface AccountD1 {
  id: number
  name: string
  code: string
}

export interface AccountD2 {
  id: number
  name: string
  code: string
  d1: number
}

export interface AccountD3 {
  id: number
  name: string
  code: string
  d2: number
}

export interface AccountSelectionContext {
  // Sort
  sort: Ref<1 | 2>
  handleSortChange: () => Promise<void>

  // D1
  account_d1: Ref<number | null>
  accD1List: ComputedRef<AccountD1[]>
  handleD1Change: () => Promise<void>

  // D2
  account_d2: Ref<number | null>
  accD2List: ComputedRef<AccountD2[]>
  handleD2Change: () => Promise<void>

  // D3
  account_d3: Ref<number | null>
  accD3List: ComputedRef<AccountD3[]>
  handleD3Change: () => Promise<void>

  // Utility
  initialize: () => Promise<void>
  reset: () => void
}

export const AccountSelectionKey: InjectionKey<AccountSelectionContext> = Symbol('AccountSelection')