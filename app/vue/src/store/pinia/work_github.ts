import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle } from '@/utils/helper'
import { useWork } from '@/store/pinia/work.ts'
import type { Commit } from '@/store/types/work.ts'

const workStore = useWork()

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
  const commits = ref<any[]>([])

  const fetchBranches = async (url: string, token: string = '') => {
    const headers = { Accept: 'application/vnd.github+json', Authorization: `token ${token}` }
    await api
      .get(`${url}/branches`, { headers })
      .then(async res => {
        branches.value = res.data
        res.data.forEach(b => {
          const commit = api.get(`${b.commit.url}`, { headers })
          commits.value.push(commit)
        })
      })
      .catch(err => errorHandle(err.response))
  }

  return {
    repoApi,
    fetchRepoApi,

    branches,
    commits,
    fetchBranches,
  }
})
