import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle } from '@/utils/helper'
import type { Branch, Tag } from '@/store/types/work_github.ts'

export const useGithub = defineStore('github', () => {
  // repo api
  const repoApi = ref<any>(null)
  const default_branch = computed(() => repoApi.value?.default_branch)

  const fetchRepoApi = async (url: string, token: string = '') =>
    await api
      .get(`${url}`, {
        headers: { Accept: 'application/vnd.github.diff', Authorization: `token ${token}` },
      })
      .then(res => (repoApi.value = res.data))
      .catch(err => errorHandle(err.response))

  // branches api
  const branches = ref<Branch[]>([])
  const trunk_url = ref<string>('')
  const trunk = ref<any | null>(null)

  const fetchBranches = async (url: string, token: string = '') => {
    const headers = { Accept: 'application/vnd.github+json', Authorization: `token ${token}` }
    await api
      .get(`${url}/branches`, { headers })
      .then(async res => {
        await fetchRepoApi(url, token)
        branches.value = res.data.filter((branch: Branch) => branch.name !== default_branch.value)
        await api
          .get(`${url}/branches/${default_branch.value}`, { headers })
          .then(res => (trunk_url.value = res.data.commit.commit.tree.url))
        await api.get(trunk_url.value, { headers }).then(res => (trunk.value = res.data))
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
    repoApi,
    default_branch,
    fetchRepoApi,

    branches,
    trunk,
    fetchBranches,

    tags,
    fetchTags,

    diffApi,
    removeDiffApi,
    fetchDiffApi,
  }
})
