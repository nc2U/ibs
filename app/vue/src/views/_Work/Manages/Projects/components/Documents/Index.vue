<script lang="ts" setup>
import { computed, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work'
import { useDocs } from '@/store/pinia/docs'
import DocsList from './components/DocsList.vue'
import DocsView from './components/DocsView.vue'
import DocsForm from './components/DocsForm.vue'

const emit = defineEmits(['aside-visible'])

const route = useRoute()

const workStore = useWork()
const issueProject = computed(() => workStore.issueProject)
const codeCategoryList = computed(() => workStore.codeCategoryList)
const fetchCodeCategoryList = () => workStore.fetchCodeCategoryList()

const docsStore = useDocs()
const getCategories = computed(() => docsStore.getCategories)
const fetchCategoryList = (docType: number) => docsStore.fetchCategoryList(docType)

const categories = computed(() =>
  issueProject.value?.is_real_dev ? getCategories.value : codeCategoryList.value,
)

onBeforeMount(() => {
  emit('aside-visible', true)
  fetchCodeCategoryList()
  fetchCategoryList(1)
})
</script>

<template>
  <DocsForm v-if="route.name === '(문서) - 추가'" :categories="categories" />

  <DocsView v-if="route.name === '(문서) - 보기'" />

  <DocsList v-else :proj-status="issueProject?.status" :docs-list="[]" />
</template>
