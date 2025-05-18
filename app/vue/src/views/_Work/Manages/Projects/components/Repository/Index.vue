<script lang="ts" setup>
import { computed, inject, onBeforeMount, ref } from 'vue'
import { useWork } from '@/store/pinia/work.ts'
import type { Commit, IssueProject } from '@/store/types/work.ts'
import Revisions from './components/Revisions.vue'
import ViewDiff from './components/ViewDiff.vue'

const project = inject<IssueProject | null>('iProject')

const commitFilter = ref({
  project: project?.pk,
  repo: undefined,
  page: 1,
  limit: 25,
})

const workStore = useWork()
const repo = computed(() => workStore.repository)
const repoList = computed(() => workStore.repositoryList)
const commitList = computed(() => workStore.commitList)
const repoApi = computed(() => workStore.repoApi)

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

const viewPageSort = ref<'revisions' | 'diff'>('revisions')

const headPk = ref<number | null>(null)
const basePk = ref<number | null>(null)

const diffs = computed<{ headCommit: Commit | null; baseCommit: Commit | null }>(() => ({
  headCommit: commitList.value.filter(c => c.pk === 10218)[0] || null,
  baseCommit: commitList.value.filter(c => c.pk === basePk.value)[0] || null,
}))

const headSet = (pk: number) => (headPk.value = pk)
const baseSet = (pk: number) => (basePk.value = pk)

const getDiff = (payload: { headCommit: number; baseCommit: number }) => {
  // diffs.value.headCommit = commitList.value.filter(c => c.pk === payload.headCommit)[0]
  // diffs.value.baseCommit = commitList.value.filter(c => c.pk === payload.baseCommit)[0]
  viewPageSort.value = 'diff'
  console.log(diffs)
}

const pageSelect = (page: number) => {
  commitFilter.value.page = page
  fetchCommitList(commitFilter.value)
}

onBeforeMount(async () => {
  await fetchRepoList(1, 'true')
  await fetchCommitList(commitFilter.value)
  if (repoList.value.length) await fetchRepo(repoList.value[0].pk as number)
})
</script>

<template>
  <Revisions
    v-if="viewPageSort === 'revisions'"
    :commit-list="commitList"
    @head-set="headSet"
    @base-set="baseSet"
    @get-diff="getDiff"
    @page-select="pageSelect"
  />

  <ViewDiff
    v-else
    :head-commit="diffs.headCommit as Commit"
    :base-commit="diffs.baseCommit as Commit"
    @get-back="() => (viewPageSort = 'revisions')"
  />
</template>
