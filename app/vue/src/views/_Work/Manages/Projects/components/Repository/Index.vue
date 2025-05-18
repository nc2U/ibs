<script lang="ts" setup>
import { computed, inject, onBeforeMount, ref } from 'vue'
import { useWork } from '@/store/pinia/work.ts'
import type { IssueProject } from '@/store/types/work.ts'
import Revisions from './components/Revisions.vue'
import ViewDiff from '@/views/_Work/Manages/Projects/components/Repository/components/ViewDiff.vue'

const project = inject<IssueProject | null>('iProject')

const workStore = useWork()
const commitList = computed(() => workStore.commitList)

const commitFilter = ref({
  project: project?.pk,
  repo: undefined,
  page: 1,
  limit: 25,
})

const fetchCommitList = (payload: {
  project?: number
  repo?: number
  issues?: number[]
  page?: number
  limit?: number
}) => workStore.fetchCommitList(payload)

const viewPageSort = ref<'revisions' | 'diff'>('revisions')
const diffs = ref<{ refCommit: number; comCommit: number }>({
  refCommit: 2,
  comCommit: 1,
})

const getDiff = (payload: any) => {
  diffs.value.refCommit = payload.refCommit
  diffs.value.comCommit = payload.comCommit
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
    @get-diff="getDiff"
    @page-select="pageSelect"
  />

  <ViewDiff
    v-else
    :ref-commit="diffs.refCommit"
    :com-commit="diffs.comCommit"
    @get-back="() => (viewPageSort = 'revisions')"
  />
</template>
