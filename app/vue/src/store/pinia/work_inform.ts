import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper.ts'
import type { News, NewsComment, CustomQuery, TargetType } from '@/store/types/work_inform.ts'

export const useInform = defineStore('inform', () => {
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
      .catch(err => errorHandle(err.response.data))

  const fetchNewsList = async (payload: { project?: string; author?: number; page?: number }) => {
    const { project, author, page = 1 } = payload
    const params: Record<string, any> = { page }
    if (project) params.project__slug = project
    if (author) params.author = author

    await api
      .get(`/news/`, { params })
      .then(res => {
        newsList.value = res.data.results
        newsCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const createNews = (payload: News, proj: null | string = null) =>
    api
      .post(`/news/`, payload)
      .then(async res => {
        await fetchNews(res.data.pk)
        await fetchNewsList({ project: proj ?? '' })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateNews = (pk: number, payload: News) =>
    api
      .put(`/news/${pk}/`, payload)
      .then(async res => {
        await fetchNews(res.data.pk)
        await fetchNewsList({ project: res.data.project.slug || '' })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const patchNews = (pk: number, payload: any) =>
    api
      .patch(`/news/${pk}/`, payload)
      .then(async res => {
        await fetchNews(res.data.pk)
        await fetchNewsList({ project: res.data.project.slug ?? '' })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteNews = (pk: number, proj: null | string = null) =>
    api
      .delete(`/news/${pk}/`)
      .then(async () => {
        await fetchNewsList({ project: proj ?? '' })
        message('warning', '알림', 'deleted!!')
      })
      .catch(err => errorHandle(err.response.data))

  // news comment states & getters
  const newsComment = ref<NewsComment | null>(null)
  const newsCommentList = ref<NewsComment[]>([])

  const removeNewsComment = () => (newsComment.value = null)

  const fetchNewsComment = (pk: number) =>
    api
      .get(`/news-comment/${pk}/`)
      .then(res => (newsComment.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchNewsCommentList = (payload: any) =>
    api
      .get(`/news-comment/?news=${payload.news}`)
      .then(res => (newsCommentList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createNewsComment = (payload: NewsComment) =>
    api
      .post(`/news-comment/`, payload)
      .then(async () => {
        if (payload.news) await fetchNews(payload.news)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const patchNewsComment = (payload: any) =>
    api
      .patch(`/news-comment/${payload.pk}/`, payload)
      .then(() => message())
      .catch(err => errorHandle(err.response.data))

  const deleteNewsComment = (pk: number) =>
    api
      .delete(`/news-comment/${pk}/`)
      .then(() => message('warning', '알림', 'deleted!!'))
      .catch(err => errorHandle(err.response.data))

  // custom query states & actions
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
    loading,
    fetchQueries,
    createQuery,
    updateQuery,
    deleteQuery,
  }
})
