import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle } from '@/utils/helper'
import type { Branch, Tag, Master, Tree } from '@/store/types/work_github.ts'

const sortTree = (trees: Tree[]) =>
  trees.sort((a, b) => {
    // 디렉터리 먼저
    if (a.type === 'tree' && b.type !== 'tree') return -1
    if (a.type !== 'tree' && b.type === 'tree') return 1
    // 그 다음 이름순 정렬
    return a.path.localeCompare(b.path)
  })

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
  const brancheList = ref<any[]>([])
  const branches = ref<Branch[]>([])
  const master_tree_url = ref<string>('')
  const master = ref<Master | null>(null)
  const master_tree = computed(() => sortTree(master.value?.tree ?? []))

  const fetchBranches = async (url: string, token: string = '') => {
    const headers = { Accept: 'application/vnd.github+json', Authorization: `token ${token}` }
    await api
      .get(`${url}/branches`, { headers })
      .then(async res => {
        await fetchRepoApi(url, token) // deault_branch 데이터 추출

        // 일반 브랜치 데이터 추출 // 브랜치명
        brancheList.value = res.data.filter(
          (branch: Branch) => branch.name !== default_branch.value,
        )
        // 브랜치 데이터 추출 -> 저자, 수정일, 메시지, 트리 주소
        branches.value = []
        for (const b of brancheList.value) {
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
            console.log('Error fetching tree:', error)
          }
        }

        // 기본 브랜치 데이터 추출
        await api
          .get(`${url}/branches/${default_branch.value}`, { headers })
          .then(res => (master_tree_url.value = res.data.commit.commit.tree.url))
        await api
          .get(`${master_tree_url.value}`, { headers })
          .then(res => (master.value = res.data))
          .catch(err => errorHandle(err.response))
      })
      .catch(err => errorHandle(err.response))
  }

  const fetchBranch = async (url: string, headers: any) => api.get(url, { headers })

  const fetchSubTree = async (url: string, token: string) => {
    try {
      const { data } = await api.get(url, {
        headers: { Authorization: `token ${token}` },
      })
      return data.tree.map((item: Tree) => ({
        path: item.path,
        mode: item.mode,
        type: item.type,
        sha: item.sha,
        url: item.url,
        size: item.size,
        open: false,
        loaded: item.type === 'tree' ? false : undefined,
      }))
    } catch (error) {
      console.log('Error fetching tree:', error)
      return []
    }
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
    master,
    master_tree,
    master_tree_url,
    fetchBranches,
    fetchSubTree,

    tags,
    fetchTags,

    diffApi,
    removeDiffApi,
    fetchDiffApi,
  }
})
