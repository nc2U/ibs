<script lang="ts" setup>
import { computed, inject, onBeforeMount } from 'vue'
import { useWork } from '@/store/pinia/work.ts'
import Revisions from './components/Revisions.vue'

const project = inject('iProject')
const workStore = useWork()
const commitList = computed(() => workStore.commitList)

const fetchCommitList = (payload: {
  project?: string
  repo?: number
  issues?: number[]
  page?: number
}) => workStore.fetchCommitList(payload)

const pageSelect = (page: number) => fetchCommitList({ project: project?.pk, page })

onBeforeMount(() => {
  fetchCommitList({ project: project?.pk })
})
</script>

<template>
  <Revisions :commit-list="commitList" @page-select="pageSelect" />
</template>
