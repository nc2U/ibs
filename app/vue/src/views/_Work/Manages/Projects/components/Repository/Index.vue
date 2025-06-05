<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useGithub } from '@/store/pinia/work_github.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { Repository, Commit, BranchInfo, Tree } from '@/store/types/work_github.ts'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import GitRepository from './components/GitRepository.vue'
import GitFileView from './components/Tree/GitFileView.vue'
import Revisions from './components/Revisions.vue'
import ViewDiff from './components/ViewDiff.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

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

const branches = computed<string[]>(() => gitStore.branches)
const tags = computed<string[]>(() => gitStore.tags)

const default_branch = computed(() => gitStore.default_branch)
const curr_branch = computed(() => gitStore.curr_branch)
const branchTree = computed<Tree[]>(() => gitStore.branch_tree)

const gitDiff = computed<any>(() => gitStore.gitDiff)

const fetchRepoApi = (pk: number) => gitStore.fetchRepoApi(pk)
const fetchGitDiff = (pk: number, diff_hash: string, full = false) =>
  gitStore.fetchGitDiff(pk, diff_hash, full)

const fetchBranches = (repoPk: number) => gitStore.fetchBranches(repoPk)
const fetchTags = (repoPk: number) => gitStore.fetchTags(repoPk)
const fetchBranchTree = (repoPk: number, branch: string, tag = '') =>
  gitStore.fetchBranchTree(repoPk, branch, tag)
const fetchTagTree = (repoPk: number, tag: string = '') => gitStore.fetchTagTree(repoPk, tag)

// file view
const fileView = ref(false)
const fileData = ref<any | null>(null)
const toggleFileView = (payload: any) => {
  fileData.value = payload
  fileView.value = true
}

const changeBranch = (branch: string, tag = '') =>
  fetchBranchTree(repo.value?.pk as number, branch, tag)
const changeTag = (tag: string) => fetchBranchTree(repo.value?.pk as number, tag, true)

// revisons & diff view
const viewPageSort = ref<'revisions' | 'diff'>('revisions')

const route = useRoute()
watch(route, nVal => {
  fileView.value = false
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

onBeforeMount(async () => {
  if (project.value) await dataSetup((project.value as IssueProject).pk as number)
})
</script>

<template>
  <ContentBody ref="cBody" :aside="false">
    <template v-slot:default>
      <GitRepository
        v-if="!fileView"
        :repo="repo as Repository"
        :branches="branches"
        :tags="tags"
        :curr-branch="curr_branch as BranchInfo"
        :def-tree="branchTree"
        @file-view="toggleFileView"
        @change-branch="changeBranch"
        @change-tag="changeTag"
      />

      <GitFileView v-else :file-data="fileData" @file-view-close="fileView = false" />

      <Revisions
        v-if="viewPageSort === 'revisions'"
        :page="cFilter.page"
        :commit-list="commitList"
        :get-list-sort="getListSort"
        :set-head-id="String(headId ?? '')"
        :set-base-id="String(baseId ?? '')"
        @head-set="headSet"
        @base-set="baseSet"
        @get-diff="getDiff"
        @get-list-sort="changeListSort"
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
