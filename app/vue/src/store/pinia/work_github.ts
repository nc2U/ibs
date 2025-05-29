import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import type { Commit, CommitInfo, Repository } from '@/store/types/work_github.ts'

export const useGithub = defineStore('github', () => {
  // Repository states & getters
  const repository = ref<Repository | null>(null)
  const repositoryList = ref<Repository[]>([])

  const fetchRepo = async (pk: number) =>
    await api
      .get(`/repository/${pk}/`)
      .then(async res => {
        repository.value = res.data
      })
      .catch(err => errorHandle(err.response.data))

  const fetchRepoList = async (project: number | '' = '', is_default = '', is_report = '') =>
    await api
      .get(`/repository/?project=${project}&is_default=${is_default}&is_report=${is_report}`)
      .then(res => (repositoryList.value = res.data.results))
      .catch(err => errorHandle(err.response.data))

  const createRepo = async (payload: Repository) =>
    await api
      .post(`/repository/`, payload)
      .then(async res => {
        await fetchRepo(res.data.pk)
        await fetchRepoList(res.data.project.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const patchRepo = async (payload: Repository) =>
    await api
      .patch(`/repository/${payload.pk as number}/`, payload)
      .then(async res => {
        await fetchRepo(res.data.pk)
        await fetchRepoList(res.data.project.pk)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const deleteRepo = async (pk: number, proj: number | null = null) =>
    await api
      .delete(`/repository/${pk}/`)
      .then(async () => {
        await fetchRepoList(proj ?? '')
        message('warning', '알림!', '해당 저장소가 삭제되었습니다!')
      })
      .catch(err => errorHandle(err.response.data))

  // commit states & getters
  const commit = ref<Commit | null>(null)
  const commitList = ref<Commit[]>([])
  const commitCount = ref<number>(0)

  const commitPages = (itemPerPage: number) => Math.ceil(commitCount.value / itemPerPage)

  const fetchCommit = async (pk: number) =>
    await api
      .get(`/commit/${pk}/`)
      .then(res => (commit.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchCommitList = async (payload: {
    project?: number
    repo?: number
    issues?: number[]
    page?: number
    limit?: number
  }) => {
    const { project, repo, issues, page, limit } = payload
    const filterQuery = `repo__project=${project ?? ''}&repo=${repo ?? ''}`
    const issueQuery = issues?.length ? issues.map(n => `&issues=${n}`).join('') : ''
    const paginationQuery = `page=${page}&limit=${limit ?? ''}`
    return await api
      .get(`/commit/?${filterQuery}&${issueQuery}&${paginationQuery}`)
      .then(res => {
        commitList.value = res.data.results
        commitCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  // repo api
  const repoApi = ref<any>(null)
  const default_branch = computed<string>(() => repoApi.value?.default_branch ?? 'master')

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

  const fetchSubTree = async (repo: number, sha: string) => {
    const { data: tree } = await api.get(`/repo/${repo}/tree/${sha}`)
    return tree
  }

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

  const fetchDiffApi = (pk: number, diff_hash: string) =>
    api
      .get(`/repo/${pk}/compare/${diff_hash}/`)
      .then(res => (diffApi.value = res.data))
      .catch(err => errorHandle(err.response.data))

  return {
    repository,
    repositoryList,
    fetchRepo,
    fetchRepoList,
    createRepo,
    patchRepo,
    deleteRepo,

    commit,
    commitList,
    commitCount,
    commitPages,
    fetchCommit,
    fetchCommitList,

    repoApi,
    default_branch,
    fetchRepoApi,

    master,
    master_tree,
    fetchDefBranch,
    fetchSubTree,

    branches,
    fetchBranches,

    tags,
    fetchTags,

    diffApi,
    removeDiffApi,
    fetchDiffApi,
  }
})
