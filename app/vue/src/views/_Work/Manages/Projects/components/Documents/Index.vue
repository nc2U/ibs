<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work'
import { type DocsFilter, useDocs } from '@/store/pinia/docs'
import DocsList from './components/DocsList.vue'
import DocsView from './components/DocsView.vue'
import DocsForm from './components/DocsForm.vue'

const emit = defineEmits(['aside-visible'])

const typeNumber = ref(1)

const docsFilter = ref<DocsFilter>({
  doc_type: typeNumber.value,
  category: '',
  issue_project: '',
  ordering: '-created',
  search: '',
  page: 1,
  limit: '',
})

const route = useRoute()

const workStore = useWork()
const issueProject = computed(() => workStore.issueProject)
const codeCategoryList = computed(() => workStore.codeCategoryList)
const fetchCodeCategoryList = () => workStore.fetchCodeCategoryList()

const docsStore = useDocs()
const getCategories = computed(() => docsStore.getCategories)
const fetchCategoryList = (type: number) => docsStore.fetchCategoryList(type)
const fetchDocsList = (payload: DocsFilter) => docsStore.fetchDocsList(payload)

const realProject = computed(() => !!issueProject.value?.is_real_dev)

const categories = computed(() =>
  realProject.value ? getCategories.value : codeCategoryList.value,
)

const cateChange = (type: number) => fetchCategoryList(type)

onBeforeMount(async () => {
  emit('aside-visible', true)
  await fetchCodeCategoryList()
  await fetchCategoryList(1)
  await fetchDocsList(docsFilter.value)
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
