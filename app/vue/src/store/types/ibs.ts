export interface AccountSort {
  pk: number
  name: string
  accounts: number[]
}

export interface AccountD1 {
  pk: number
  sorts: number[]
  code: string
  name: string
  description: string
}

export interface AccountD2 {
  pk: number
  d1: number
  code: string
  name: string
  description: string
}

export interface AccountD3 {
  pk: number
  d2: number
  code: string
  name: string
  description: string
  is_hide: boolean
  is_special: boolean
}

export type WiseWord = {
  pk: number
  saying_ko: string
  saying_en: string
  spoked_by: string
}
