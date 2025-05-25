import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle } from '@/utils/helper'
import type { GitData, Tree } from '@/store/types/work_github.ts'

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
  const master = ref<GitData | null>(null)
  const master_tree_url = ref<string>('')
  const master_tree = ref<any[]>([])

  const fetchDefBranch = async (url: string, token: string = '') => {
    const headers = { Accept: 'application/vnd.github+json', Authorization: `token ${token}` }
    if (default_branch.value === '') await fetchRepoApi(url, token) // deault_branch 데이터 추출

    // 기본(master) 브랜치 데이터 추출
    await api // 트리 url 구하기
      .get(`${url}/branches/${default_branch.value}`, { headers })
      .then(async res => {
        master_tree_url.value = res.data.commit.commit.tree.url

        master.value = {
          name: res.data.name,
          commit: {
            sha: res.data.commit.sha.substring(0, 5),
            url: res.data.commit.url,
            author: res.data.commit.commit.author.name,
            date: res.data.commit.commit.author.date,
            message: res.data.commit.commit.message,
          },
        }

        await api // tree 구하기
          .get(`${master_tree_url.value}`, { headers })
          .then(async res => {
            const treeList = sortTree(res.data.tree ?? [])

            master_tree.value = []

            for (const tree of treeList) {
              try {
                const { data: commits } = await api.get(`${url}/commits?path=${tree.path}`, {
                  headers,
                })
                const latest = commits[0]
                master_tree.value.push({
                  path: tree.path,
                  mode: tree.mode,
                  type: tree.type,
                  sha: tree.sha,
                  url: tree.url,
                  size: tree.size,
                  commit: {
                    sha: latest.sha.substring(0, 5),
                    url: latest.url,
                    author: latest.commit.author.name,
                    date: latest.commit.author.date,
                    message: latest.commit.message,
                  },
                  open: false,
                  loaded: tree.type === 'tree' ? false : undefined,
                })
              } catch (error) {
                console.log('Error fetching tree:', error)
              }
            }
          })
          .catch(err => errorHandle(err.response))
      })
      .catch(err => errorHandle(err.response))
  }

  const branches = ref<GitData[]>([])

  const fetchBranches = async (url: string, token: string = '') => {
    const headers = { Accept: 'application/vnd.github+json', Authorization: `token ${token}` }
    await api
      .get(`${url}/branches`, { headers })
      .then(async res => {
        if (default_branch.value === '') await fetchRepoApi(url, token) // deault_branch 데이터 추출

        // 일반 브랜치 데이터 추출 // 브랜치명
        const bList = res.data.filter((b: GitData) => b.name !== default_branch.value)
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

  // const fetchBranch = async (url: string, headers: any) => api.get(url, { headers })

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
  const tags = ref<GitData[]>([])

  const fetchTags = async (url: string, token: string = '') => {
    const headers = { Accept: 'application/vnd.github+json', Authorization: `token ${token}` }
    await api
      .get(`${url}/tags`, { headers })
      .then(async res => {
        // tags.value = res.data

        // tags 데이터 추출
        // const tList = res.data.filter((t: GitData) => t.name !== default_branch.value)
        // 브랜치 데이터 추출 -> 저자, 수정일, 메시지, 트리 주소
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
    master_tree_url,
    fetchDefBranch,
    branches,
    fetchBranches,
    fetchSubTree,

    tags,
    fetchTags,

    diffApi,
    removeDiffApi,
    fetchDiffApi,
  }
})
