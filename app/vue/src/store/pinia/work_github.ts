import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle } from '@/utils/helper'
import type { Branch, Tag } from '@/store/types/work_github.ts'

export const useGithub = defineStore('github', () => {
  // branches api
  const branches = ref<Branch[]>([])
  const trunk = ref<Branch | null>(null)

  const fetchBranches = async (url: string, token: string = '') => {
    const headers = { Accept: 'application/vnd.github+json', Authorization: `token ${token}` }
    await api
      .get(`${url}/branches`, { headers })
      .then(async res => {
        branches.value = res.data.filter((branch: Branch) => !branch.protected)
        trunk.value = res.data.filter((branch: Branch) => branch.protected)[0]
      })
      .catch(err => errorHandle(err.response))
  }

  // tags api
  const tags = ref<Tag[]>([])

  const fetchTags = async (url: string, token: string = '') => {
    const headers = { Accept: 'application/vnd.github+json', Authorization: `token ${token}` }
    await api
      .get(`${url}/tags`, { headers })
      .then(res => (tags.value = res.data))
      .catch(err => errorHandle(err.response))
  }

  // repo api
  const repoApi = ref<any>(null)

  const fetchRepoApi = async (url: string, token: string = '') =>
    await api
      .get(`${url}`, {
        headers: { Accept: 'application/vnd.github.diff', Authorization: `token ${token}` },
      })
      .then(res => (repoApi.value = res.data))
      .catch(err => errorHandle(err.response))

  // diff api
  const diffApi = ref<any>(null)

  const removeDiffApi = () => (diffApi.value = null)
  const fetchDiffApi = (url: string, token: string) =>
    api
      .get(url, {
        headers: {
          Accept: 'application/vnd.github.diff',
          Authorization: `token ${token}`,
        },
      })
      .then(res => (diffApi.value = res.data))
      .catch(err => errorHandle(err.response.data))

  return {
    branches,
    trunk,
    fetchBranches,

    tags,
    fetchTags,

    repoApi,
    fetchRepoApi,

    diffApi,
    removeDiffApi,
    fetchDiffApi,
  }
})
