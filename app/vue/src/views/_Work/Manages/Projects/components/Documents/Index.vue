<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work'
import { type DocsFilter, useDocs } from '@/store/pinia/docs'
import type { AFile, Link, PatchDocs } from '@/store/types/docs'
import DocsList from './components/DocsList.vue'
import DocsView from './components/DocsView.vue'
import DocsForm from './components/DocsForm.vue'
import AddNewDoc from '@/views/_Work/Manages/Projects/components/Documents/components/AddNewDoc.vue'

const emit = defineEmits(['aside-visible'])

const typeNumber = ref<1 | 2>(1)
const refDocsForm = ref()

const types = ref<any[]>([
  { value: 1, label: '일반문서' },
  { value: 2, label: '소송기록' },
])

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
const fetchAllIssueProjectList = (
  com: '' | number = '',
  sort: '1' | '2' | '3' = '2',
  p_isnull: '' | '1' = '1',
  status: '1' | '9' = '1',
) => workStore.fetchAllIssueProjectList(com, sort, p_isnull, status)

const docStore = useDocs()
const docs = computed(() => docStore.docs)
const docsList = computed(() => docStore.docsList)
const categoryList = computed(() => docStore.categoryList)
const getCategories = computed(() => docStore.getCategories)

const fetchDocTypeList = () => docStore.fetchDocTypeList()
const fetchLink = (pk: number) => docStore.fetchLink(pk)
const fetchFile = (pk: number) => docStore.fetchFile(pk)
const fetchDocs = (pk: number) => docStore.fetchDocs(pk)
const fetchDocsList = (payload: DocsFilter) => docStore.fetchDocsList(payload)
const fetchCategoryList = (type: number) => docStore.fetchCategoryList(type)

const createDocs = (payload: { form: FormData }) => docStore.createDocs(payload)
const updateDocs = (payload: { pk: number; form: FormData }) => docStore.updateDocs(payload)
const patchDocs = (payload: PatchDocs & { filter: DocsFilter }) => docStore.patchDocs(payload)
const patchLink = (payload: Link) => docStore.patchLink(payload)
const patchFile = (payload: AFile) => docStore.patchFile(payload)

const categories = computed(() =>
  issueProject.value?.sort !== '3' ? getCategories.value : codeCategoryList.value,
)

const getDocsList = (target: unknown) => {
  console.log(target)
  if (target === 1 || target === 2) {
    docsFilter.value.doc_type = target
    fetchCategoryList(target)
    fetchDocsList(docsFilter.value)
    if (route.name === '(문서) - 추가') refDocsForm.value.setDocType(target)
  }
}

const pageSelect = (page: number) => {
  docsFilter.value.page = page
  fetchDocsList(docsFilter.value)
}

const dataSetup = async (pk: number, docsId?: string | string[]) => {
  if (route.params.projId) {
    const projId = route.params.projId as string
    await workStore.fetchIssueProject(projId)
  }
  docsFilter.value.issue_project = issueProject.value?.pk
  await fetchAllIssueProjectList(pk, '2', '')
  await fetchDocTypeList()
  await fetchCodeCategoryList()
  await fetchCategoryList(typeNumber.value)
  await fetchDocsList(docsFilter.value)
  if (docsId) await fetchDocs(Number(docsId))
}

onBeforeMount(async () => {
  emit('aside-visible', true)
  await dataSetup(1, route.params?.docsId)
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>문서</h5>
    </CCol>

    <AddNewDoc :proj-status="issueProject?.status" />
  </CRow>

  <CRow class="mb-3">
    <CCol v-if="issueProject?.sort !== '3'">
      <v-tabs v-model="typeNumber" density="compact" @update:model-value="getDocsList">
        <v-tab
          v-for="type in types"
          :value="type.value"
          :key="type.value"
          variant="tonal"
          :active="typeNumber === type.value"
        >
          {{ type.label }}
        </v-tab>
      </v-tabs>
    </CCol>
  </CRow>

  <DocsForm
    ref="refDocsForm"
    v-if="route.name === '(문서) - 추가'"
    :project-sort="issueProject?.sort"
    :type-number="typeNumber"
    :categories="categories"
  />

  <DocsView v-if="route.name === '(문서) - 보기'" />

  <DocsList v-else :docs-list="docsList" @page-select="pageSelect" />
</template>
