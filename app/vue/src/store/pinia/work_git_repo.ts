import api from '@/api'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { errorHandle, message } from '@/utils/helper'
import type {
  Commit,
  BranchInfo,
  RepoApi,
  Repository,
  ChangedFile,
} from '@/store/types/work_git_repo.ts'

export const useGitRepo = defineStore('git_repo', () => {
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

  const assignCommit = (commitObj: Commit) => (commit.value = commitObj)
  const removeCommit = () => (commit.value = null)

  const fetchCommit = async (pk: number) =>
    await api
      .get(`/commit/${pk}/`)
      .then(res => (commit.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const fetchCommitBySha = async (sha: string) => {
    try {
      const { data } = await api.get(`/commit/?search=${sha}`)
      commit.value = data.results[0]
    } catch (error: any) {
      console.error('[fetchCommitBySha] Failed:', error)
      throw error
    }
  }

  const fetchCommitList = async (payload: {
    repo: number
    branch?: string
    project?: number
    issues?: number[]
    page?: number
    limit?: number
    search?: string
    up_to?: string
  }) => {
    const { repo, branch, project, issues, page = 1, limit, search, up_to } = payload
    const filter = `?repo=${repo}`
    const branchQry = branch ? `&branches__name=${branch}` : ''
    const projQry = project ? `&repo__project=${project}` : ''
    const issueQry = issues?.length ? issues.map(n => `&issues=${n}`).join('') : ''
    const pageQry = `&page=${page}&limit=${limit ?? ''}`
    const searchQry = search ? `&search=${search}` : ''
    const upToQry = up_to ? `&up_to=${up_to}` : ''
    return await api
      .get(`/commit/${filter}${branchQry}${projQry}${issueQry}${pageQry}${searchQry}${upToQry}`)
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
  const tagList = ref<BranchInfo[]>([])
  const tags = computed(() => tagList.value.map(b => b.name))

  const fetchTags = async (repoPk: number) => {
    await api
      .get(`/repo/${repoPk}/tags/`)
      .then(async res => (tagList.value = res.data))
      .catch(err => errorHandle(err.response))
  }

  const curr_path = ref<string>('')
  const refs_sort = ref<'branch' | 'tag' | 'sha'>('branch')
  const curr_refs = ref<string>('')
  const branch_refs = ref<BranchInfo | null>(null)
  const branch_tree = ref<any[]>([])
  const up_to_sha = ref<string>('')

  const setCurrPath = (path: string) => (curr_path.value = path)
  const setRefsSort = (sort: 'branch' | 'tag' | 'sha') => (refs_sort.value = sort)
  const setCurrRefs = (refs: string) => (curr_refs.value = refs)

  const fetchRefTree = async (payload: {
    repo: number
    refs: string
    path?: string
    sub?: boolean
  }) => {
    const { repo, refs, path = '', sub = false } = payload

    const url = path
      ? `/repo/${repo}/tree/${encodeURIComponent(path)}?refs=${refs}`
      : `/repo/${repo}/tree/?refs=${refs}`

    try {
      const { data } = await api.get(url)
      if (sub) return data.trees
      else {
        branch_refs.value = data.refs
        branch_tree.value = data.trees
        up_to_sha.value = data.refs.commit.sha
      }
    } catch (err: any) {
      errorHandle(err.response)
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
  const baseSha = ref('')
  const headSha = ref('')
  const gitDiff = ref<any>(null)

  const setBaseSha = (sha: string) => (baseSha.value = sha)
  const setHeadSha = (sha: string) => (headSha.value = sha)

  const removeGitDiff = () => (gitDiff.value = null)
  const fetchGitDiff = (pk: number, diff_hash: string, full = false) =>
    api
      .get(`/repo/${pk}/compare/${diff_hash}${full ? '&full=1' : ''}`)
      .then(res => (gitDiff.value = res.data))
      .catch(err => errorHandle(err.response.data))

  const changedFile = ref<ChangedFile | null>(null)

  const fetchChangedFiles = async (repo: number, sha: string) => {
    try {
      const { data } = await api.get(`/repo/${repo}/changed/?sha=${sha}`)
      changedFile.value = data
    } catch (error: any) {
      console.error('[fetchChangedFils] Failed:', error)
      throw error
    }
  }

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
    assignCommit,
    removeCommit,
    fetchCommit,
    fetchCommitBySha,
    fetchCommitList,

    repoApi,
    default_branch,
    fetchRepoApi,

    branches,
    fetchBranches,

    tags,
    fetchTags,

    curr_path,
    curr_refs,
    refs_sort,
    branch_refs,
    branch_tree,
    up_to_sha,
    setCurrPath,
    setRefsSort,
    setCurrRefs,
    fetchRefTree,
    fetchFileView,

    baseSha,
    headSha,
    gitDiff,
    setBaseSha,
    setHeadSha,
    removeGitDiff,
    fetchGitDiff,

    changedFile,
    fetchChangedFiles,
  }
})
