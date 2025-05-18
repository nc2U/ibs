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
</template>
