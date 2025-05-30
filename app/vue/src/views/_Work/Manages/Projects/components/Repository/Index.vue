<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useWork } from '@/store/pinia/work_project.ts'
import { useGithub } from '@/store/pinia/work_github.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { Repository, Commit, CommitInfo, Tree } from '@/store/types/work_github.ts'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import GitRepository from './components/GitRepository.vue'
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
const ghStore = useGithub()
const repo = computed<Repository | null>(() => ghStore.repository)
const repoList = computed(() => ghStore.repositoryList)
const commitList = computed<Commit[]>(() => ghStore.commitList)

watch(repo, nVal => {
  if (nVal) cFilter.value.repo = nVal.pk as number
})
watch(repoList, nVal => {
  if (nVal.length) fetchRepo(nVal[0].pk as number)
})

const fetchRepo = (pk: number) => ghStore.fetchRepo(pk)
const fetchRepoList = (project?: number, is_def?: string) => ghStore.fetchRepoList(project, is_def)
const fetchCommitList = (payload: {
  project?: number
  repo?: number
  issues?: number[]
  page?: number
  limit?: number
}) => ghStore.fetchCommitList(payload)

const branches = computed<CommitInfo[]>(() => ghStore.branches)
const tags = computed<CommitInfo[]>(() => ghStore.tags)

const default_branch = computed(() => ghStore.default_branch)
const master = computed(() => ghStore.master)
const masterTree = computed<Tree[]>(() => ghStore.master_tree)

const repoApi = computed<any>(() => ghStore.repoApi)
const gitDiff = computed<any>(() => ghStore.gitDiff)

const fetchRepoApi = (pk: number) => ghStore.fetchRepoApi(pk)
const fetchGitDiff = (pk: number, diff_hash: string, full = false) =>
  ghStore.fetchGitDiff(pk, diff_hash, full)

// const fetchBranches = (url: string, token: string = '') => ghStore.fetchBranches(url, token)
// const fetchDefBranch = (repo: number, branch: string = '') => ghStore.fetchDefBranch(repo, branch)
// const fetchTags = (url: string, token: string = '') => ghStore.fetchTags(url, token)

// revisons & diff view
const getListSort = ref<'latest' | 'all'>('latest')
const changeListSort = (sort: 'latest' | 'all') => (getListSort.value = sort)

const viewPageSort = ref<'revisions' | 'diff'>('revisions')

const headPk = ref<number | null>(null)
const basePk = ref<number | null>(null)

const headSet = (pk: number) => (headPk.value = pk)
const baseSet = (pk: number) => (basePk.value = pk)

const getDiff = (full = false) => {
  const base = commitList.value.find(c => c.pk === basePk.value)?.commit_hash
  const head = commitList.value.find(c => c.pk === headPk.value)?.commit_hash
  const diff_hash = `?base=${base}&head=${head}`

  if (repo.value) {
    fetchGitDiff(repo.value?.pk as number, diff_hash, full)
    viewPageSort.value = 'diff'
  }
}

const getBack = () => {
  viewPageSort.value = 'revisions'
  ghStore.removeGitDiff()
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

  // const url = githubApiUrl.value
  // const token = repo.value.github_token ?? ''
  // await fetchBranches(url, token)
  // await fetchDefBranch(repo.value.pk as number, default_branch.value)
  // await fetchTags(url, token)
}

onBeforeMount(async () => {
  if (project.value) await dataSetup(project.value.pk as number)
})
</script>

<template>
  <ContentBody ref="cBody" :aside="false">
    <template v-slot:default>
      {{ repoApi }}
      <GitRepository
        :repo="repo as Repository"
        :branches="branches"
        :tags="tags"
        :def-name="default_branch"
        :def-branch="master as CommitInfo"
        :def-tree="masterTree"
      />

      <Revisions
        v-if="viewPageSort === 'revisions'"
        :page="cFilter.page"
        :commit-list="commitList"
        :get-list-sort="getListSort"
        :parent-head-pk="String(headPk ?? '')"
        :parent-base-pk="String(basePk ?? '')"
        @head-set="headSet"
        @base-set="baseSet"
        @get-diff="getDiff"
        @get-list-sort="changeListSort"
        @page-select="pageSelect"
      />

      <ViewDiff
        v-if="viewPageSort === 'diff'"
        :head-pk="headPk as number"
        :base-pk="basePk as number"
        :git-diff="gitDiff"
        @get-diff="getDiff"
        @get-back="getBack"
      />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
