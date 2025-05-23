<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useWork } from '@/store/pinia/work.ts'
import { useGithub } from '@/store/pinia/work_github.ts'
import type { Commit, IssueProject, Repository } from '@/store/types/work.ts'
import type { Branch, Tag } from '@/store/types/work_github.ts'
import Subversion from './components/Subversion.vue'
import Revisions from './components/Revisions.vue'
import ViewDiff from './components/ViewDiff.vue'

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
    cFilter.value.project = nVal?.pk as number
    fetchCommitList(cFilter.value)
  }
})
const repo = computed<Repository | null>(() => workStore.repository)
watch(repo, nVal => {
  if (nVal) cFilter.value.repo = nVal.pk as number
})
const repoList = computed(() => workStore.repositoryList)
const commitList = computed<Commit[]>(() => workStore.commitList)

const fetchRepo = (pk: number) => workStore.fetchRepo(pk)
const fetchRepoList = (project?: number, is_default?: string) =>
  workStore.fetchRepoList(project, is_default)
const fetchCommitList = (payload: {
  project?: number
  repo?: number
  issues?: number[]
  page?: number
  limit?: number
}) => workStore.fetchCommitList(payload)

// get github api
const ghStore = useGithub()
const branches = computed<Branch[]>(() => ghStore.branches)
const tags = computed<Tag[]>(() => ghStore.tags)
const trunk = computed<Branch | null>(() => ghStore.trunk)

const githubApiUrl = computed<any>(() => (ghStore.repoApi as any)?.url || '')
const diffApi = computed<any>(() => ghStore.diffApi)

const fetchDiffApi = (url: string, token: string) => ghStore.fetchDiffApi(url, token)
const fetchBranches = (url: string, token: string = '') => ghStore.fetchBranches(url, token)
const fetchTags = (url: string, token: string = '') => ghStore.fetchTags(url, token)

const getListSort = ref<'latest' | 'all'>('latest')
const changeListSort = (sort: 'latest' | 'all') => (getListSort.value = sort)

const viewPageSort = ref<'revisions' | 'diff'>('revisions')

const headPk = ref<number | null>(null)
const basePk = ref<number | null>(null)

const diffs = computed<{ headCommit: Commit | null; baseCommit: Commit | null }>(() => ({
  headCommit: commitList.value.filter(c => c.pk === headPk.value)[0] || null,
  baseCommit: commitList.value.filter(c => c.pk === basePk.value)[0] || null,
}))

const headSet = (pk: number) => (headPk.value = pk)
const baseSet = (pk: number) => (basePk.value = pk)

const getDiff = (reverse = false) => {
  const diff_hash = !reverse
    ? `${diffs.value.baseCommit?.commit_hash}...${diffs.value.headCommit?.commit_hash}`
    : `${diffs.value.headCommit?.commit_hash}...${diffs.value.baseCommit?.commit_hash}`

  fetchDiffApi(`${githubApiUrl.value}/compare/${diff_hash}`, `${repo.value?.github_token}`)
  viewPageSort.value = 'diff'
}

const getBack = () => {
  viewPageSort.value = 'revisions'
  ghStore.removeDiffApi()
}

const pageSelect = (page: number) => {
  cFilter.value.page = page
  fetchCommitList(cFilter.value)
}

onBeforeMount(async () => {
  cFilter.value.project = project.value?.pk as number
  await fetchRepoList(1, 'true')
  if (repoList.value.length) await fetchRepo(repoList.value[0].pk as number)
  if (repo.value) {
    cFilter.value.repo = repo.value?.pk as number
    await fetchCommitList(cFilter.value)
    const url = githubApiUrl.value
    const token = repo.value.github_token ?? ''
    await fetchBranches(url, token)
    await fetchTags(url, token)
  }
})
</script>

<template>
  <Subversion :branches="branches" :tags="tags" :trunk="trunk" />

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
    :head-commit="diffs.headCommit as Commit"
    :base-commit="diffs.baseCommit as Commit"
    :diff-api="diffApi"
    @get-diff="getDiff"
    @get-back="getBack"
  />
</template>
