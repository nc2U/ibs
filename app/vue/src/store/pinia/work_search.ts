import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import api from '@/api'
import type { SearchParams, SearchResults } from '@/store/types/work_search.ts'

export const useSearch = defineStore('work_search', () => {
  const results = ref<SearchResults | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  let abortController: AbortController | null = null
  let searchSeq = 0

  const totalCount = computed(() => {
    if (!results.value) return 0
    return Object.values(results.value).reduce((sum, arr) => sum + (arr?.length ?? 0), 0)
  })

  const hasResults = computed(() => totalCount.value > 0)

  async function fetchSearch(params: SearchParams) {
    if (!params.q || params.q.trim().length < 2) {
      if (abortController) {
        abortController.abort()
        abortController = null
      }
      searchSeq += 1
      results.value = null
      loading.value = false
      error.value = '검색어는 2자 이상 입력하세요.'
      return
    }
    if (abortController) {
      abortController.abort()
    }
    const controller = new AbortController()
    abortController = controller
    const seq = ++searchSeq

    loading.value = true
    error.value = null
    try {
      const searchParams = new URLSearchParams()
      searchParams.append('q', params.q.trim())
      searchParams.append('scope', params.scope ?? 'all')
      if (params.slug) {
        searchParams.append('slug', params.slug)
      }
      searchParams.append('title_only', params.title_only ?? '0')
      searchParams.append('opened_only', params.opened_only ?? '0')
      searchParams.append('attach_mode', params.attach_mode ?? '1')

      const targets = params.t ?? ['issues', 'comments', 'meetings', 'news', 'documents', 'posts']
      targets.forEach(t => searchParams.append('t', t))

      const res = await api.get('/issue-search/run/', {
        params: searchParams,
        signal: controller.signal,
      })
      if (seq !== searchSeq) return
      results.value = res.data
    } catch (err: unknown) {
      if (
        seq !== searchSeq ||
        (err instanceof Error && (err.name === 'CanceledError' || err.name === 'AbortError')) ||
        (typeof err === 'object' && err !== null && (err as { code?: string }).code === 'ERR_CANCELED')
      ) {
        return
      }
      error.value = '검색 중 오류가 발생했습니다.'
      results.value = null
    } finally {
      if (seq === searchSeq) {
        loading.value = false
      }
    }
  }

  function reset() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    searchSeq += 1
    results.value = null
    loading.value = false
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
