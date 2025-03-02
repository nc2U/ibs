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
  <DocsForm v-if="route.name === '(문서) - 추가'" />

  <DocsView v-if="route.name === '(문서) - 보기'" />

  <DocsList v-else :proj-status="issueProject?.status" :docs-list="[]" />
</template>
