<script lang="ts" setup>
import { useWork } from '@/store/pinia/work.ts'
import Revisions from './components/Revisions.vue'
import { computed, onBeforeMount } from 'vue'

const workStore = useWork()
const commitList = computed(() => workStore.commitList)

const fetchCommitList = (payload: { repo?: number; issues?: number[]; page?: number }) =>
  workStore.fetchCommitList(payload)

const pageSelect = (page: number) => fetchCommitList({ page })

onBeforeMount(() => {
  fetchCommitList({})
})
</script>

<template>
  <Revisions :commit-list="commitList" @page-select="pageSelect" />
</template>
