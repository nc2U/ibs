<script lang="ts" setup>
import { computed, onBeforeMount } from 'vue'
import { useWork } from '@/store/pinia/work'
import { useRoute } from 'vue-router'
import DocsList from './components/DocsList.vue'
import DocsView from './components/DocsView.vue'
import DocsForm from './components/DocsForm.vue'

const emit = defineEmits(['aside-visible'])

const route = useRoute()

const workStore = useWork()
const issueProject = computed(() => workStore.issueProject)

onBeforeMount(() => emit('aside-visible', true))
</script>

<template>
  <DocsList v-if="route.name === '(문서)'" :proj-status="issueProject?.status" :docs-list="[]" />

  <DocsView v-if="route.name === '(문서) - 보기'" />

  <DocsForm v-if="route.name === '(문서) - 추가' || route.name === '(문서) - 편집'" />
</template>
