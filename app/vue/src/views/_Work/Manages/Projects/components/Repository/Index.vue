<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useGithub } from '@/store/pinia/work_github.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { Repository, Commit, BranchInfo, Tree } from '@/store/types/work_github.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import BranchTree from './components/BranchTree.vue'
import ViewFile from './components/ViewFile.vue'
import ViewRevision from './components/ViewRevision.vue'
import Revisions from './components/Revisions.vue'
import ViewDiff from './components/ViewDiff.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const headerView = ref<'tree' | 'file' | 'revision'>('tree')

const cFilter = ref({
  project: undefined as number | undefined,
  repo: undefined as number | undefined,
  page: 1,
  limit: 25,
})

const workStore = useWork()
const project = computed<IssueProject | null>(() => workStore.issueProject)
watch(project, nVal => {
  if (nVal) {
    dataSetup(nVal?.pk as number)
  }
})

// get github api
const gitStore = useGithub()
const repo = computed<Repository | null>(() => gitStore.repository)
const repoList = computed<Repository[]>(() => gitStore.repositoryList)
const commitList = computed<Commit[]>(() => gitStore.commitList)

watch(repo, nVal => {
  if (nVal) cFilter.value.repo = nVal.pk as number
})
watch(repoList, nVal => {
  if (nVal.length) fetchRepo(nVal[0].pk as number)
})

const fetchRepo = (pk: number) => gitStore.fetchRepo(pk)
const fetchRepoList = (project?: number, is_def?: string) => gitStore.fetchRepoList(project, is_def)
const fetchCommitList = (payload: {
  project?: number
  repo?: number
  issues?: number[]
  page?: number
  limit?: number
}) => gitStore.fetchCommitList(payload)
const fetchFileView = (repo: number, path: string, sha: string) =>
  gitStore.fetchFileView(repo, path, sha)

const branches = computed<string[]>(() => gitStore.branches)
const tags = computed<string[]>(() => gitStore.tags)

const default_branch = computed(() => gitStore.default_branch)
const curr_branch = computed(() => (gitStore.curr_branch as BranchInfo)?.name ?? '')
const branchTree = computed<Tree[]>(() => gitStore.branch_tree)
const currentTree = computed<Tree[]>(() => (subTree.value ? subTree.value : branchTree.value))

const gitDiff = computed<any>(() => gitStore.gitDiff)

const fetchRepoApi = (pk: number) => gitStore.fetchRepoApi(pk)
const fetchGitDiff = (pk: number, diff_hash: string, full = false) =>
  gitStore.fetchGitDiff(pk, diff_hash, full)
const fetchCommitBySha = (sha: string) => gitStore.fetchCommitBySha(sha)
const fetchBranches = (repoPk: number) => gitStore.fetchBranches(repoPk)
const fetchTags = (repoPk: number) => gitStore.fetchTags(repoPk)
const fetchBranchTree = (repoPk: number, branch: string, tag = '') =>
  gitStore.fetchBranchTree(repoPk, branch, tag)
const fetchSubTree = (payload: { repo: number; sha?: string; path?: string; branch?: string }) =>
  gitStore.fetchSubTree(payload)

const changeBranch = (branch: string, tag = '') => {
  subTree.value = null
  fetchBranchTree(repo.value?.pk as number, branch, tag)
}

const changeTag = (tag: string) => {
  subTree.value = null
  fetchBranchTree(repo.value?.pk as number, tag, '1')
}

// into path
const shaMap = ref<{ path: string; sha: string }[]>([])
const currPath = ref('')
const subTree = ref(null)

const intoRoot = () => {
  headerView.value = 'tree'
  currPath.value = ''
  subTree.value = null
}

const prePath = async (path: string) => {
  const item = shaMap.value.find(item => item.path === path)
  if (item) await intoPath({ path, sha: item.sha })
  else
    subTree.value = await fetchSubTree({
      repo: repo.value?.pk as number,
      path,
      branch: curr_branch.value,
    })
}

const intoPath = async (node: { path: string; sha: string }) => {
  headerView.value = 'tree'
  const exists = shaMap.value.some(item => item.path === node.path && item.sha === node.sha)
  if (!exists) shaMap.value?.push(node)
  const { sha, path } = node
  currPath.value = path
  subTree.value = await fetchSubTree({
    repo: repo.value?.pk as number,
    sha,
    path,
  })
}

// file view
const fileData = ref<any | null>(null)
const toggleFileView = (payload: any) => {
  fileData.value = payload
  headerView.value = 'file'
}

const viewFile = async (node: { path: string; sha: string }) => {
  const fileData = await fetchFileView(
    repo.value?.pk as number,
    node?.path as string,
    node?.sha as string,
  )
  toggleFileView(fileData)
}

// revision view
const getRevision = () => {
  viewPageSort.value = 'revisions'
  headerView.value = 'revision'
}

const revisionView = async (hash: string) => {
  await fetchCommitBySha(hash)
  getRevision()
}

// revisons & diff view
const viewPageSort = ref<'revisions' | 'diff'>('revisions')

const route = useRoute()
watch(route, nVal => {
  headerView.value = 'tree'
  viewPageSort.value = 'revisions'
})

const getListSort = ref<'latest' | 'all'>('latest')
const changeListSort = (sort: 'latest' | 'all') => (getListSort.value = sort)

const headId = ref<number | null>(null)
const baseId = ref<number | null>(null)

const headSet = (revision_id: number) => (headId.value = revision_id)
const baseSet = (revision_id: number) => (baseId.value = revision_id)

const getDiff = (full = false) => {
  const base = commitList.value.find(c => c.revision_id === baseId.value)?.commit_hash
  const head = commitList.value.find(c => c.revision_id === headId.value)?.commit_hash
  const diff_hash = `?base=${base}&head=${head}`

  if (repo.value) {
    fetchGitDiff(repo.value?.pk as number, diff_hash, full)
    viewPageSort.value = 'diff'
  }
}

const getBack = () => {
  viewPageSort.value = 'revisions'
  gitStore.removeGitDiff()
}

const pageSelect = (page: number) => {
  cFilter.value.page = page
  fetchCommitList(cFilter.value)
}

const dataSetup = async (proj: number) => {
  cFilter.value.project = proj
  await fetchRepoList(proj, 'true')
  await fetchRepo(repoList.value[0].pk as number)
  cFilter.value.repo = repo.value?.pk as number
  await fetchRepoApi(repo.value?.pk as number)
  await fetchCommitList(cFilter.value)
  await fetchBranches(cFilter.value.repo)
  await fetchTags(cFilter.value.repo)
  await fetchBranchTree(cFilter.value.repo, default_branch.value)
}

const loading = ref(true)
onBeforeMount(async () => {
  if (project.value) await dataSetup((project.value as IssueProject).pk as number)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :aside="false">
    <template v-slot:default>
      <BranchTree
        v-if="headerView === 'tree'"
        :repo="repo as Repository"
        :curr-path="currPath"
        :branches="branches"
        :tags="tags"
        :curr-branch="curr_branch"
        :branch-tree="currentTree"
        @into-root="intoRoot"
        @pre-path="prePath"
        @into-path="intoPath"
        @file-view="viewFile"
        @revision-view="getRevision"
        @change-branch="changeBranch"
        @change-tag="changeTag"
      />

      <ViewFile
        v-else-if="headerView === 'file'"
        :repo-name="repo?.slug as string"
        :curr-path="currPath"
        :curr-branch="curr_branch"
        :file-data="fileData"
        @into-root="intoRoot"
        @into-path="intoPath"
        @goto-trees="headerView = 'tree'"
      />

      <ViewRevision
        v-else-if="headerView === 'revision'"
        :repo="repo?.pk as number"
        @goto-back="headerView = 'tree'"
        @get-diff="getDiff"
        @get-commit="revisionView"
        @into-path="intoPath"
        @file-view="viewFile"
      />

      <Revisions
        v-if="viewPageSort === 'revisions' && headerView !== 'revision'"
        :page="cFilter.page"
        :commit-list="commitList"
        :get-list-sort="getListSort"
        :set-head-id="String(headId ?? '')"
        :set-base-id="String(baseId ?? '')"
        @head-set="headSet"
        @base-set="baseSet"
        @get-diff="getDiff"
        @get-list-sort="changeListSort"
        @revision-view="getRevision"
        @page-select="pageSelect"
      />

      <ViewDiff
        v-if="viewPageSort === 'diff'"
        :git-diff="gitDiff"
        @get-diff="getDiff"
        @get-back="getBack"
      />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
