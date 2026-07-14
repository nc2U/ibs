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
      const searchParams = new URLSearchParams()
      searchParams.append('q', params.q)
      searchParams.append('scope', params.scope ?? 'all')
      if (params.slug) {
        searchParams.append('slug', params.slug)
      }
      searchParams.append('title_only', params.title_only ?? '0')

      const targets = params.t ?? ['issues', 'comments', 'meetings', 'news', 'documents', 'posts']
      targets.forEach(t => searchParams.append('t', t))

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
