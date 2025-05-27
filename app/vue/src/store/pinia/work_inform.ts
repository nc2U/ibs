import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper.ts'
import type { News } from '@/store/types/work_inform.ts'

export const useInform = defineStore('inform', () => {
  // news states & getters
  const news = ref<News | null>(null)
  const newsList = ref<News[]>([])

  const fetchNews = (pk: number) =>
    api
      .get(`/news/${pk}/`)
      .then(res => (news.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchNewsList = (payload: { project?: string; author?: number }) =>
    api
      .get(`/news/?project__slug=${payload.project ?? ''}&author=${payload.author ?? ''}`)
      .then(res => (newsList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createNews = (payload: News) =>
    api
      .post(`/news/`, payload)
      .then(async res => {
        await fetchNews(res.data.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const updateNews = (payload: News) =>
    api
      .put(`/news/`, payload)
      .then(async res => {
        await fetchNews(res.data.pk)
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

  return {
    news,
    newsList,
    fetchNews,
    fetchNewsList,
    createNews,
    updateNews,
    deleteNews,
  }
})
