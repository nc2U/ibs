import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper.ts'
import type { AccountD1, AccountD2, AccountD3, AccountSort, WiseWord } from '@/store/types/ibs.ts'

export const useIbs = defineStore('ibs', () => {
  const sortList = ref<AccountSort[]>([])

  const fetchAccSortList = async () =>
    await api
      .get(`/account-sort/`)
      .then(res => (sortList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const listAccD1List = ref<AccountD1[]>([])

  const fetchAllAccD1List = async () =>
    await api
      .get(`/account-depth1/`)
      .then(res => (listAccD1List.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const listAccD2List = ref<AccountD2[]>([])

  const fetchAllAccD2List = async () =>
    await api
      .get(`/account-depth2/`)
      .then(res => (listAccD2List.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const listAccD3List = ref<AccountD3[]>([])

  const fetchAllAccD3List = async () =>
    await api
      .get(`/account-depth3/`)
      .then(res => (listAccD3List.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const patchAccD3 = async (payload: { pk: number; is_hide: boolean }) => {
    const { pk, ...hideData } = payload
    return await api
      .patch(`/account-depth3/${pk}/`, hideData)
      .then(async () => {
        await fetchAllAccD3List()
        await fetchFormAccD3List(null, null, null).then(() => message())
      })
      .catch(err => errorHandle(err.response.data))
  }

  const formAccD1List = ref<AccountD1[]>([])

  const fetchFormAccD1List = async (sort?: number | null) => {
    const uSort = sort ? `?sorts=${sort}` : ''
    return await api
      .get(`/account-depth1/${uSort}`)
      .then(res => (formAccD1List.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const formAccD2List = ref<AccountD2[]>([])

  const fetchFormAccD2List = async (sort: number | null, d1: number | null) => {
    const uSort = sort ? `d1__sorts=${sort}` : ''
    const uD1 = d1 ? `&d1=${d1}` : ''
    return await api
      .get(`/account-depth2/?${uSort}${uD1}`)
      .then(res => (formAccD2List.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

  const formAccD3List = ref<AccountD3[]>([])

  const fetchFormAccD3List = async (sort: number | null, d1: number | null, d2: number | null) => {
    const uSort = sort ? `sort=${sort}` : ''
    const uD1 = d1 ? `&d2__d1=${d1}` : ''
    const uD2 = d2 ? `&d2=${d2}` : ''
    return await api
      .get(`/account-depth3/?${uSort}${uD1}${uD2}&is_hide=false`)
      .then(res => (formAccD3List.value = res.data.results))
      .catch(err => errorHandle(err.response.data))
  }

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
    sortList,
    fetchAccSortList,

    formAccD1List,
    fetchAllAccD1List,
    formAccD2List,
    fetchAllAccD2List,
    formAccD3List,
    fetchAllAccD3List,
    patchAccD3,

    listAccD1List,
    fetchFormAccD1List,
    listAccD2List,
    fetchFormAccD2List,
    listAccD3List,
    fetchFormAccD3List,

    wiseWordsList,
    wiseWordsCount,
    wiseWord,
    fetchWiseWordsList,
    fetchWiseWord,
  }
})
