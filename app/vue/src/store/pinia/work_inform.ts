import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper.ts'
import type { News, NewsComment } from '@/store/types/work_inform.ts'

export const useInform = defineStore('inform', () => {
  // news states & getters
  const news = ref<News | null>(null)
  const newsList = ref<News[]>([])
  const newsCount = ref<number>(0)

  const newsPages = (itemPerPage: number) => Math.ceil(newsCount.value / itemPerPage)

  const fetchNews = (pk: number) =>
    api
      .get(`/news/${pk}/`)
      .then(res => (news.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchNewsList = async (payload: { project?: string; author?: number; page?: number }) => {
    const { project, author, page = 1 } = payload
    await api
      .get(`/news/?project__slug=${project ?? ''}&author=${author ?? ''}&page=${page}`)
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

  const updateNews = (payload: News, proj: null | string = null) =>
    api
      .put(`/news/`, payload)
      .then(async res => {
        await fetchNews(res.data.pk)
        await fetchNewsList({ project: proj ?? '' })
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteNews = (pk: number) =>
    api
      .delete(`/news/${pk}/`)
      .then(async () => {
        message('warning', '알림', 'deleted!!')
      })
      .catch(err => errorHandle(err.response.data))

  // news comment states & getters
  const newsComment = ref<NewsComment | null>(null)
  const newsCommentList = ref<NewsComment[]>([])

  const removeNewsComment = () => (newsComment.value = null)

  const fetchNewsComment = (pk: number) =>
    api
      .get(`/news-comment/${pk}`)
      .then(res => (newsComment.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchNewsCommentList = (payload: any) =>
    api
      .get(`/news-comments/?news=${payload.news}`)
      .then(res => (newsCommentList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createNewsComment = (payload: NewsComment) =>
    api
      .post(`/news-comment`, payload)
      .then(() => message())
      .catch(err => errorHandle(err.response.data))

  const patchNewsComment = (payload: any) =>
    api
      .patch(`/news-comment/${payload.pk}`, payload)
      .then(() => message())
      .catch(err => errorHandle(err.response.data))

  const deleteNewsComment = (pk: number) =>
    api
      .delete(`/news-comment/${pk}`)
      .then(() => message('warning', '알림', 'deleted!!'))
      .catch(err => errorHandle(err.response.data))

  return {
    news,
    newsList,
    newsCount,

    newsPages,
    fetchNews,
    fetchNewsList,
    createNews,
    updateNews,
    deleteNews,

    newsComment,
    newsCommentList,

    removeNewsComment,
    fetchNewsComment,
    fetchNewsCommentList,
    createNewsComment,
    patchNewsComment,
    deleteNewsComment,
  }
})
