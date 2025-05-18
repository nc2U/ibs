<script lang="ts" setup>
import { computed, inject, onBeforeMount, ref } from 'vue'
import { useWork } from '@/store/pinia/work.ts'
import type { Commit, IssueProject, Repository } from '@/store/types/work.ts'
import Revisions from './components/Revisions.vue'
import ViewDiff from './components/ViewDiff.vue'

const project = inject<IssueProject | null>('iProject')

const cFilter = ref({
  project: project?.pk,
  repo: undefined,
  page: 1,
  limit: 25,
})

const workStore = useWork()
const repo = computed<Repository | null>(() => workStore.repository)
const repoList = computed(() => workStore.repositoryList)
const commitList = computed(() => workStore.commitList)
const githubApiUrl = computed<any>(() => (workStore.githubRepoApi as any)?.url || '')
const githubDiffApi = computed<any>(() => workStore.githubDiffApi)

const fetchDiff = (url: string, token: string) => workStore.fetchDiff(url, token)
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

const getDiff = () => {
  fetchDiff(
    `${githubApiUrl.value}/compare/${diffs.value.baseCommit?.commit_hash}...${diffs.value.headCommit?.commit_hash}`,
    `${repo.value?.github_token}`,
  )
  viewPageSort.value = 'diff'
}

const getBack = () => {
  viewPageSort.value = 'revisions'
  workStore.removeDiffApi()
}

const pageSelect = (page: number) => {
  cFilter.value.page = page
  fetchCommitList(cFilter.value)
}

onBeforeMount(async () => {
  await fetchRepoList(1, 'true')
  await fetchCommitList(cFilter.value)
  if (repoList.value.length) await fetchRepo(repoList.value[0].pk as number)
})
</script>

<template>
  <Revisions
    v-if="viewPageSort === 'revisions'"
    :page="cFilter.page"
    :commit-list="commitList"
    :get-list-sort="getListSort"
    @head-set="headSet"
    @base-set="baseSet"
    @get-diff="getDiff"
    @get-list-sort="changeListSort"
    @page-select="pageSelect"
  />

  <ViewDiff
    v-else
    :head-commit="diffs.headCommit as Commit"
    :base-commit="diffs.baseCommit as Commit"
    :github-api-url="githubApiUrl"
    :github-diff-api="githubDiffApi"
    @get-back="getBack"
  />
</template>
