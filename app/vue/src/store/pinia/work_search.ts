import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import api from '@/api'
import type { SearchParams, SearchResults } from '@/store/types/work_search.ts'

export const useSearch = defineStore('work_search', () => {
  const results = ref<SearchResults | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const totalCount = computed(() => {
    if (!results.value) return 0
    return Object.values(results.value).reduce((sum, arr) => sum + (arr?.length ?? 0), 0)
  })

  const hasResults = computed(() => totalCount.value > 0)

  async function fetchSearch(params: SearchParams) {
    if (!params.q || params.q.trim().length < 2) {
      error.value = '검색어는 2자 이상 입력하세요.'
      return
    }
    loading.value = true
    error.value = null
    try {
      const searchParams: Record<string, unknown> = {
        q: params.q,
        scope: params.scope ?? 'all',
        ...(params.slug && { slug: params.slug }),
        t: params.t ?? ['issues', 'comments', 'meetings', 'news'],
        title_only: params.title_only ?? '0',
      }
      const res = await api.get('/issue-search/run/', { params: searchParams })
      results.value = res.data
    } catch {
      error.value = '검색 중 오류가 발생했습니다.'
      results.value = null
    } finally {
      loading.value = false
    }
  }

  function reset() {
    results.value = null
    error.value = null
  }

  return {
    results,
    loading,
    error,
    totalCount,
    hasResults,
    fetchSearch,
    reset,
  }
})
