<script lang="ts" setup>
import { computed, inject, onBeforeMount, ref } from 'vue'
import { useWork } from '@/store/pinia/work.ts'
import Revisions from './components/Revisions.vue'

const project = inject('iProject')
const workStore = useWork()
const commitList = computed(() => workStore.commitList)

const commitFilter = ref({
  project: project?.pk,
  repo: undefined,
  page: 1,
  limit: 25,
})

const fetchCommitList = (payload: {
  project?: string
  repo?: number
  issues?: number[]
  page?: number
  limit?: number
}) => workStore.fetchCommitList(payload)

const pageSelect = (page: number) => fetchCommitList({ project: project?.pk, page })

onBeforeMount(() => {
  fetchCommitList(commitFilter.value)
})
</script>

<template>
  <Revisions :commit-list="commitList" @page-select="pageSelect" />
</template>
