import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle } from '@/utils/helper'
import type { CommitInfo, Tree } from '@/store/types/work_github.ts'

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
  const master = ref<CommitInfo | null>(null)
  const master_tree = ref<any[]>([])

  const fetchDefBranch = async (repo: number, branch: string) =>
    await api
      .get(`/repo/${repo}/branch/${branch}/`)
      .then(res => {
        master.value = res.data.branch
        master_tree.value = res.data.trees
      })
      .catch(err => errorHandle(err.response))

  const branches = ref<CommitInfo[]>([])

  const fetchBranches = async (url: string, token: string = '') => {
    const headers = { Accept: 'application/vnd.github+json', Authorization: `token ${token}` }
    await api
      .get(`${url}/branches`, { headers })
      .then(async res => {
        if (default_branch.value === '') await fetchRepoApi(url, token) // deault_branch 데이터 추출

        // 일반 브랜치 데이터 추출 // 브랜치명
        const bList = res.data.filter((b: CommitInfo) => b.name !== default_branch.value)
        // 브랜치 데이터 추출 -> 저자, 수정일, 메시지, 트리 주소
        branches.value = []
        for (const b of bList) {
          try {
            const { data: branch } = await api.get(`${url}/branches/${b.name}`, { headers })
            branches.value.push({
              name: b.name,
              commit: {
                sha: b.commit.sha.substring(0, 5),
                url: b.commit.url,
                author: branch.commit.commit.author.name,
                date: branch.commit.commit.author.date,
                message: branch.commit.commit.message,
              },
            })
          } catch (error) {
            console.log('Error fetching branch:', error)
          }
        }
      })
      .catch(err => errorHandle(err.response))
  }

  // tags api
  const tags = ref<CommitInfo[]>([])

  const fetchTags = async (url: string, token: string = '') => {
    const headers = { Accept: 'application/vnd.github+json', Authorization: `token ${token}` }
    await api
      .get(`${url}/tags`, { headers })
      .then(async res => {
        // tags.value = res.data

        // tags 데이터 -> CommitInfo 데이터 추출 -> 저자, 수정일, 메시지, 트리 주소
        tags.value = []
        for (const tag of res.data) {
          try {
            const { data: commit } = await api.get(`${tag.commit.url}`, { headers })
            tags.value.push({
              name: tag.name,
              commit: {
                sha: tag.commit.sha.substring(0, 5),
                url: tag.commit.url,

                author: commit.commit.author.name,
                date: commit.commit.author.date,
                message: commit.commit.message,
              },
            })
          } catch (error) {
            console.log('Error fetching tag:', error)
          }
        }
      })
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

    master,
    master_tree,
    fetchDefBranch,

    branches,
    fetchBranches,

    tags,
    fetchTags,

    diffApi,
    removeDiffApi,
    fetchDiffApi,
  }
})
