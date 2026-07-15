import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper.ts'
import type { CustomQuery, TargetType } from '@/store/types/work_query.ts'

export const useQueryStore = defineStore('workQuery', () => {
  const queries = ref<CustomQuery[]>([])
  const loading = ref(false)

  const fetchQueries = async (payload: { projectSlug?: string; targetType?: TargetType }) => {
    loading.value = true
    try {
      const params = new URLSearchParams()
      if (payload.projectSlug) params.append('project__slug', payload.projectSlug)
      if (payload.targetType) params.append('target_type', payload.targetType)

      const res = await api.get(`/custom-query/?${params.toString()}`)
      queries.value = res.data.results
    } catch (err: any) {
      errorHandle(err.response.data)
    } finally {
      loading.value = false
    }
  }

  const createQuery = async (payload: Partial<CustomQuery>) => {
    try {
      const res = await api.post('/custom-query/', payload)
      message()
      return res.data
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  const updateQuery = async (pk: number, payload: Partial<CustomQuery>) => {
    try {
      const res = await api.put(`/custom-query/${pk}/`, payload)
      message()
      return res.data
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  const deleteQuery = async (pk: number) => {
    try {
      await api.delete(`/custom-query/${pk}/`)
      message()
    } catch (err: any) {
      errorHandle(err.response.data)
    }
  }

  return {
    queries,
    loading,
    fetchQueries,
    createQuery,
    updateQuery,
    deleteQuery,
  }
})
