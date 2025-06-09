import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import type { Commit, BranchInfo, RepoApi, Repository } from '@/store/types/work_github.ts'
import { moveElementAwayFromCollision } from 'grid-layout-plus/es/helpers/common'

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
        await fetchRepoList(res.data.project)
        message()
      })
      .catch(err => errorHandle(err.response.data))

  const patchRepo = async (payload: Repository) =>
    await api
      .patch(`/repository/${payload.pk as number}/`, payload)
      .then(async res => {
        await fetchRepo(res.data.pk)
        await fetchRepoList(res.data.project)
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
    search?: string
  }) => {
    const { project, repo, issues, page, limit, search } = payload
    const filterQuery = `repo__project=${project ?? ''}&repo=${repo ?? ''}`
    const issueQuery = issues?.length ? issues.map(n => `&issues=${n}`).join('') : ''
    const paginationQuery = `page=${page}&limit=${limit ?? ''}`
    const searchQuery = `search=${search ?? ''}`
    return await api
      .get(`/commit/?${filterQuery}&${issueQuery}&${paginationQuery}${searchQuery}`)
      .then(res => {
        commitList.value = res.data.results
        commitCount.value = res.data.count
      })
      .catch(err => errorHandle(err.response.data))
  }

  const fetchCommitBySha = async (sha: string) => {
    try {
      const { data } = await api.get(`/commit/?search=${sha}`)
      return data.results[0]
    } catch (error: any) {
      console.error('[fetchCommitBySha] Failed:', error)
      throw error
    }
  }

  // repo api
  const repoApi = ref<RepoApi | null>(null)
  const default_branch = computed<string>(() => repoApi.value?.default_branch ?? 'master')

  const fetchRepoApi = async (pk: number) =>
    await api
      .get(`/repo/${pk}/`)
      .then(res => (repoApi.value = res.data))
      .catch(err => errorHandle(err.response))

  // branches api
  const branchList = ref<BranchInfo[]>([])
  const branches = computed(() => branchList.value.map(b => b.name))

  const fetchBranches = async (repoPk: number) =>
    await api
      .get(`/repo/${repoPk}/branches/`)
      .then(res => (branchList.value = res.data))
      .catch(err => errorHandle(err.response))

  // tags api
  const tagList = ref<BranchInfo[]>([])
  const tags = computed(() => tagList.value.map(b => b.name))

  const fetchTags = async (repoPk: number) => {
    await api
      .get(`/repo/${repoPk}/tags/`)
      .then(async res => (tagList.value = res.data))
      .catch(err => errorHandle(err.response))
  }

  const curr_branch = ref<BranchInfo | null>(null)
  const branch_tree = ref<any[]>([])

  const fetchBranchTree = async (repo: number, branch: string, tag = '') => {
    const is_tag = tag ? `?is_tag=${tag}` : ''
    await api
      .get(`/repo/${repo}/branch/${branch}/${is_tag}`)
      .then(res => {
        curr_branch.value = res.data.branch
        branch_tree.value = res.data.trees
      })
      .catch(err => errorHandle(err.response))
  }

  const fetchSubTree = async (repo: number, sha: string, path: string | null = null) => {
    const encodedPath = path ? encodeURIComponent(path) : ''
    const url = path
      ? `/repo/${repo}/tree/${encodedPath}?sha=${sha}`
      : `/repo/${repo}/tree/?sha=${sha}`
    try {
      const { data } = await api.get(url)
      return data
    } catch (error: any) {
      console.error('[fetchSubTree] Failed:', error.response?.data || error.message)
      throw error
    }
  }

  const fetchFileView = async (repo: number, path: string, sha: string) => {
    const encodedPath = encodeURIComponent(path)
    const url = `/repo/${repo}/file/${encodedPath}?sha=${sha}`
    try {
      const { data } = await api.get(url)
      return data
    } catch (error: any) {
      console.error('[fetchFile] Failed:', error.response?.data || error.message)
    }
  }

  // diff api
  const gitDiff = ref<any>(null)

  const removeGitDiff = () => (gitDiff.value = null)

  const fetchGitDiff = (pk: number, diff_hash: string, full = false) =>
    api
      .get(`/repo/${pk}/compare/${diff_hash}${full ? '?full=1' : ''}`)
      .then(res => (gitDiff.value = res.data))
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
    fetchCommitBySha,

    repoApi,
    default_branch,
    fetchRepoApi,

    branches,
    fetchBranches,

    tags,
    fetchTags,

    curr_branch,
    branch_tree,
    fetchBranchTree,
    fetchSubTree,
    fetchFileView,

    gitDiff,
    removeGitDiff,
    fetchGitDiff,
  }
})
