import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { errorHandle, message } from '@/utils/helper'
import type { News, NewsComment, CustomQuery, TargetType } from '@/store/types/work_inform'

export const useInform = defineStore('inform', () => {
  const accountStore = useAccount()

  // news states & getters
  const news = ref<News | null>(null)
  const newsList = ref<News[]>([])
  const newsCount = ref<number>(0)

  const newsPages = (itemPerPage: number) => Math.ceil(newsCount.value / itemPerPage)

  const removeNews = () => (news.value = null)
  const fetchNews = (pk: number) =>
    api
      .get(`/news/${pk}/`)
      .then(res => (news.value = res.data))
      .catch(err => errorHandle(err))

  const fetchNewsList = async (payload: {
    project?: string
    author?: number
    page?: number
    project__status?: string
  }) => {
    const { project, author, page = 1, project__status } = payload
    const params: Record<string, string | number> = { page }
    if (project) {
      params.project__slug = project
    } else {
      params.project__status = project__status ?? '1'
    }
    if (author) params.author = author

    await api
      .get(`/news/`, { params })
      .then(res => {
        newsList.value = res.data.results
        newsCount.value = res.data.count
      })
      .catch(err => errorHandle(err))
  }

  const createNews = (payload: FormData | Partial<News>, proj: null | string = null) =>
    api
      .post(`/news/`, payload)
      .then(async res => {
        await fetchNews(res.data.pk)
        await fetchNewsList({ project: proj ?? '' })
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const updateNews = (pk: number, payload: FormData | Partial<News>) =>
    api
      .put(`/news/${pk}/`, payload)
      .then(async res => {
        await fetchNews(res.data.pk)
        await fetchNewsList({ project: res.data.project?.slug || '' })
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const patchNews = (pk: number, payload: FormData | Partial<News> | Record<string, unknown>) =>
    api
      .patch(`/news/${pk}/`, payload)
      .then(async res => {
        await fetchNews(res.data.pk)
        await fetchNewsList({ project: res.data.project?.slug ?? '' })
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteNews = (pk: number, proj: null | string = null) =>
    api
      .delete(`/news/${pk}/`)
      .then(async () => {
        await fetchNewsList({ project: proj ?? '' })
        message('warning', '알림', '공지 사항이 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  // news comment states & getters
  const newsComment = ref<NewsComment | null>(null)
  const newsCommentList = ref<NewsComment[]>([])

  const removeNewsComment = () => (newsComment.value = null)

  const fetchNewsComment = (pk: number) =>
    api
      .get(`/news-comment/${pk}/`)
      .then(res => (newsComment.value = res.data))
      .catch(err => errorHandle(err))

  const fetchNewsCommentList = (payload: { news: number }) =>
    api
      .get(`/news-comment/`, { params: { news: payload.news } })
      .then(res => (newsCommentList.value = res.data.results))
      .catch(err => errorHandle(err))

  const createNewsComment = (payload: Partial<NewsComment>) =>
    api
      .post(`/news-comment/`, payload)
      .then(async res => {
        if (payload.news) await fetchNews(payload.news)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const patchNewsComment = (payload: { pk: number; news?: number; [key: string]: unknown }) =>
    api
      .patch(`/news-comment/${payload.pk}/`, payload)
      .then(async res => {
        const newsPk = payload.news ?? news.value?.pk
        if (newsPk) await fetchNews(newsPk)
        message()
        return res.data
      })
      .catch(err => {
        errorHandle(err)
        return null
      })

  const deleteNewsComment = (pk: number, newsPk?: number) =>
    api
      .delete(`/news-comment/${pk}/`)
      .then(async () => {
        const targetNewsPk = newsPk ?? news.value?.pk
        if (targetNewsPk) await fetchNews(targetNewsPk)
        message('warning', '알림', '댓글이 삭제되었습니다.')
        return true
      })
      .catch(err => {
        errorHandle(err)
        return false
      })

  // custom query states & actions
  const queries = ref<CustomQuery[]>([])
  const loading = ref(false)

  // getter
  const myQueries = computed(() =>
    queries.value.filter(
      q => !q.is_public && (!accountStore.userInfo?.pk || q.user === accountStore.userInfo.pk),
    ),
  )
  const pubQueries = computed(() => queries.value.filter(q => q.is_public))

  const fetchQueries = async (payload: { projectSlug?: string; targetType?: TargetType }) => {
    loading.value = true
    try {
      const params: Record<string, string | number> = { limit: 200 }
      if (payload.projectSlug) params.project__slug = payload.projectSlug
      if (payload.targetType) params.target_type = payload.targetType

      const res = await api.get('/custom-query/', { params })
      queries.value = res.data.results ?? res.data ?? []
    } catch (err: unknown) {
      errorHandle(err)
    } finally {
      loading.value = false
    }
  }

  const createQuery = async (payload: Partial<CustomQuery>) => {
    try {
      const res = await api.post('/custom-query/', payload)
      message()
      return res.data
    } catch (err: unknown) {
      errorHandle(err)
      return null
    }
  }

  const updateQuery = async (pk: number, payload: Partial<CustomQuery>) => {
    try {
      const res = await api.put(`/custom-query/${pk}/`, payload)
      message()
      return res.data
    } catch (err: unknown) {
      errorHandle(err)
      return null
    }
  }

  const deleteQuery = async (pk: number) => {
    try {
      await api.delete(`/custom-query/${pk}/`)
      message('warning', '알림', '검색양식이 삭제되었습니다.')
      return true
    } catch (err: unknown) {
      errorHandle(err)
      return false
    }
  }

  const reset = () => {
    news.value = null
    newsList.value = []
    newsCount.value = 0
    newsComment.value = null
    newsCommentList.value = []
    queries.value = []
  }

  return {
    news,
    newsList,
    newsCount,

    newsPages,
    removeNews,
    fetchNews,
    fetchNewsList,
    createNews,
    updateNews,
    patchNews,
    deleteNews,

    newsComment,
    newsCommentList,

    removeNewsComment,
    fetchNewsComment,
    fetchNewsCommentList,
    createNewsComment,
    patchNewsComment,
    deleteNewsComment,

    queries,
    myQueries,
    pubQueries,
    loading,
    fetchQueries,
    createQuery,
    updateQuery,
    deleteQuery,
    reset,
  }
})
