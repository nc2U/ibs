import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { cleanupParams, errorHandle, message } from '@/utils/helper'
import { type ProjectAccount } from '@/store/types/proLedger.ts'

export type ProAccountFilter = {
  category?: string
  direction?: string
  parent?: number | null
  is_category_only?: boolean | ''
  is_active?: boolean | ''
  search?: string
}

export const useProLedger = defineStore('proLedger', () => {
  // state & getters
  const proAccountList = ref<ProjectAccount[]>([])
  const proAccountFilter = ref<ProAccountFilter>({})
  const proAccounts = computed(() =>
    proAccountList.value
      .filter(acc => acc.is_active && acc.pk !== undefined)
      .map(acc => ({
        value: acc.pk!,
        label: acc.name,
        parent: acc.parent,
        depth: acc.depth,
        category: acc.category,
        direction: acc.direction_display,
        is_cate_only: acc.is_category_only,
        is_payment: acc.is_payment,
        is_related_contract: acc.is_related_contract,
      })),
  )

  const fetchProjectAccounts = async (payload: ProAccountFilter = {}) => {
    proAccountFilter.value = payload
    const params = cleanupParams({
      category: payload.category,
      direction: payload.direction,
      parent: payload.parent,
      is_category_only: payload.is_category_only,
      is_active: payload.is_active,
      search: payload.search,
    })

    return await api
      .get('/ledger/project-account/', { params })
      .then(res => {
        proAccountList.value = res.data.results
      })
      .catch(err => errorHandle(err.response.data))
  }

  return {
    proAccountList,
    proAccountFilter,
    proAccounts,

    fetchProjectAccounts,
  }
})
