<script lang="ts" setup>
import { useWork } from '@/store/pinia/work.ts'
import Revisions from './components/Revisions.vue'
import { computed, onBeforeMount } from 'vue'

const workStore = useWork()
const commitList = computed(() => workStore.commitList)

const fetchCommitList = (repo?: number, issues?: number[]) =>
  workStore.fetchCommitList(repo, issues)

onBeforeMount(() => {
  fetchCommitList()
})
</script>

<template>
  <Revisions :commit-list="commitList" />
</template>
