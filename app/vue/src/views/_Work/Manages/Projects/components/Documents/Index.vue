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
const fetchCategoryList = (type: '' | '1' | '2') => docsStore.fetchCategoryList(type)

const realProject = computed(() => !!issueProject.value?.is_real_dev)

const categories = computed(() =>
  realProject.value ? getCategories.value : codeCategoryList.value,
)

const cateChange = (type: '1' | '2') => fetchCategoryList(type)

onBeforeMount(() => {
  emit('aside-visible', true)
  fetchCodeCategoryList()
  fetchCategoryList('1')
})
</script>

<template>
  <DocsForm
    v-if="route.name === '(문서) - 추가'"
    :real-project="realProject"
    :categories="categories"
    @get-categories="cateChange"
  />

  <DocsView v-if="route.name === '(문서) - 보기'" />

  <DocsList v-else :proj-status="issueProject?.status" :docs-list="[]" />
</template>
