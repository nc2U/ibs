import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle } from '@/utils/helper'

export const useGithub = defineStore('github', () => {
  // GET /repos/{owner}/{repo}/branches
  const repoApi = ref<any>(null)

  const fetchRepoApi = async (url: string, token: string = '') =>
    await api
      .get(`${url}`, {
        headers: { Accept: 'application/vnd.github.diff', Authorization: `token ${token}` },
      })
      .then(res => (repoApi.value = res.data))
      .catch(err => errorHandle(err.response))

  const branches = ref<any[]>([])

  const fetchBranches = async (url: string, token: string = '') =>
    await api
      .get(`${url}/branches`, {
        headers: { Accept: 'application/vnd.github+json', Authorization: `token ${token}` },
      })
      .then(res => (branches.value = res.data))
      .catch(err => errorHandle(err.response))

  return {
    repoApi,
    fetchRepoApi,

    branches,
    fetchBranches,
  }
})
