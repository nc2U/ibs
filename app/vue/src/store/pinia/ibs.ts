import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'

export type WiseWord = {
  pk: number
  saying_ko: string
  saying_en: string
  spoked_by: string
}

export const useIbs = defineStore('ibs', () => {
  // states
  const wiseWordsList = ref<WiseWord[]>([])
  const wiseWordsCount = ref<number>(0)
  const wiseWord = ref<WiseWord | null>(null)

  // actions
  const fetchWiseWordsList = () =>
    api
      .get('wise-say/')
      .then(res => {
        wiseWordsList.value = res.data.results
        wiseWordsCount.value = res.data.count
      })
      .catch(err => console.log(err.response.data))

  const fetchWiseWord = (pk: number) =>
    api
      .get(`/wise-say/${pk}/`)
      .then(res => (wiseWord.value = res.data))
      .catch(err => console.log(err.response.data))

  return {
    wiseWordsList,
    wiseWordsCount,
    wiseWord,
    fetchWiseWordsList,
    fetchWiseWord,
  }
})
