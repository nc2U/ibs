<script lang="ts" setup>
import { computed, inject, onBeforeMount, ref } from 'vue'
import { useWork } from '@/store/pinia/work.ts'
import type { Commit, IssueProject } from '@/store/types/work.ts'
import Revisions from './components/Revisions.vue'
import ViewDiff from '@/views/_Work/Manages/Projects/components/Repository/components/ViewDiff.vue'

const project = inject<IssueProject | null>('iProject')

const commitFilter = ref({
  project: project?.pk,
  repo: undefined,
  page: 1,
  limit: 25,
})

const workStore = useWork()
const commitList = computed(() => workStore.commitList)

const fetchCommitList = (payload: {
  project?: number
  repo?: number
  issues?: number[]
  page?: number
  limit?: number
}) => workStore.fetchCommitList(payload)

const viewPageSort = ref<'revisions' | 'diff'>('revisions')

const diffs = ref<{ headCommit: Commit | null; baseCommit: Commit | null }>({
  headCommit: null,
  baseCommit: null,
})

const headSet = (pk: number) =>
  (diffs.value.headCommit = commitList.value.filter(c => c.pk === pk)[0])
const baseSet = (pk: number) =>
  (diffs.value.baseCommit = commitList.value.filter(c => c.pk === pk)[0])

const getDiff = (payload: { headCommit: number; baseCommit: number }) => {
  diffs.value.headCommit = commitList.value.filter(c => c.pk === payload.headCommit)[0]
  diffs.value.baseCommit = commitList.value.filter(c => c.pk === payload.baseCommit)[0]
  viewPageSort.value = 'diff'
  console.log(diffs)
}

const pageSelect = (page: number) => {
  commitFilter.value.page = page
  fetchCommitList(commitFilter.value)
}

onBeforeMount(() => {
  fetchCommitList(commitFilter.value)
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
    :head-commit="diffs.headCommit"
    :base-commit="diffs.baseCommit"
    @get-back="() => (viewPageSort = 'revisions')"
  />

  {{ diffs }}
</template>
