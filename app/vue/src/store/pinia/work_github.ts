import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import type { Commit, BranchInfo, RepoApi, Repository } from '@/store/types/work_github.ts'

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
  const tags = ref<BranchInfo[]>([])

  const fetchTags = async (repoPk: number) => {
    await api
      .get(`/repo/${repoPk}/tags/`)
      .then(async res => (tags.value = res.data))
      .catch(err => errorHandle(err.response))
  }

  const master = ref<BranchInfo | null>(null)
  const master_tree = ref<any[]>([])

  const fetchDefBranch = async (repo: number, branch: string) =>
    await api
      .get(`/repo/${repo}/branch/${branch}/`)
      .then(res => {
        master.value = res.data.branch
        master_tree.value = res.data.trees
      })
      .catch(err => errorHandle(err.response))

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

    repoApi,
    default_branch,
    fetchRepoApi,

    branches,
    fetchBranches,

    tags,
    fetchTags,

    master,
    master_tree,
    fetchDefBranch,
    fetchSubTree,
    fetchFileView,

    gitDiff,
    removeGitDiff,
    fetchGitDiff,
  }
})
