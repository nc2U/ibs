<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useRoute } from 'vue-router'
import type { IssueProject } from '@/store/types/work_project.ts'
import { type DocsFilter, type SuitCaseFilter, useDocs } from '@/store/pinia/docs'
import type { Docs, PatchDocs } from '@/store/types/docs'
import Loading from '@/components/Loading/Index.vue'
import AddNewDoc from './components/AddNewDoc.vue'
import DocsList from './components/DocsList.vue'
import DocsView from './components/DocsView.vue'
import DocsForm from './components/DocsForm.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

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
const issueProject = computed<IssueProject | null>(() => workStore.issueProject)

const docStore = useDocs()
const docs = computed(() => docStore.docs)
const docsList = computed(() => docStore.docsList)
const categoryList = computed(() => docStore.categoryList)
const getCategories = computed(() => docStore.getCategories)
const getSuitCase = computed(() => docStore.getSuitCase)

const fetchDocTypeList = () => docStore.fetchDocTypeList()
const fetchDocs = (pk: number) => docStore.fetchDocs(pk)
const fetchDocsList = (payload: DocsFilter) => docStore.fetchDocsList(payload)
const fetchCategoryList = (type: number) => docStore.fetchCategoryList(type)
const fetchAllSuitCaseList = (payload: SuitCaseFilter) => docStore.fetchAllSuitCaseList(payload)
const patchDocs = (payload: PatchDocs & { filter: DocsFilter }) => docStore.patchDocs(payload)

const issueStore = useIssue()
const codeCategoryList = computed(() => issueStore.codeCategoryList)
const fetchCodeCategoryList = () => issueStore.fetchCodeCategoryList()

const categories = computed(() =>
  (issueProject.value as IssueProject)?.sort !== '3' ? getCategories.value : codeCategoryList.value,
)

const getDocsList = (target: unknown) => {
  if (target === 1 || target === 2) {
    docsFilter.value.page = 1
    docsFilter.value.doc_type = target
    fetchCategoryList(target)
    fetchDocsList(docsFilter.value)
    if (route.name === '(문서) - 추가') refDocsForm.value.setDocType(target)
  }
}

const selectCate = (cate: number) => {
  docsFilter.value.page = 1
  docsFilter.value.category = cate
  fetchDocsList(docsFilter.value)
}

const pageSelect = (page: number) => {
  docsFilter.value.page = page
  fetchDocsList(docsFilter.value)
}

const heatedPage = ref<number[]>([])

const docsHit = async (pk: number) => {
  if (!heatedPage.value.includes(pk)) {
    heatedPage.value.push(pk)
    await fetchDocs(pk)
    const hit = ((docs.value as Docs)?.hit ?? 0) + 1
    await patchDocs({ pk, hit, filter: docsFilter.value })
  }
}

const dataSetup = async (docId?: string | string[]) => {
  if (route.params.projId) {
    const projId = route.params.projId as string
    await workStore.fetchIssueProject(projId)
  }

  docsFilter.value.issue_project = (issueProject.value as IssueProject)?.pk
  await fetchDocTypeList()
  await fetchCodeCategoryList()
  await fetchCategoryList(typeNumber.value)
  await fetchDocsList(docsFilter.value)
  await fetchAllSuitCaseList({ issue_project: docsFilter.value.issue_project })
  if (docId) await fetchDocs(Number(docId))
}

watch(
  () => route.params?.docId,
  nVal => {
    if (nVal) dataSetup(nVal)
  },
)

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await dataSetup(route.params?.docId)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody">
    <template v-slot:default>
      <DocsView v-if="route.name === '(문서) - 보기'" :docs="docs as Docs" @docs-hit="docsHit" />

      <DocsForm
        v-else-if="route.name === '(문서) - 편집'"
        :issue-project="issueProject as IssueProject"
        :type-number="typeNumber"
        :categories="categories"
        :get-suit-case="getSuitCase"
        :docs="docs as Docs"
      />

      <template v-else>
        <DocsForm
          ref="refDocsForm"
          v-if="route.name === '(문서) - 추가'"
          :issue-project="issueProject as IssueProject"
          :type-number="typeNumber"
          :categories="categories"
          :get-suit-case="getSuitCase"
        />

        <CRow class="py-2">
          <CCol>
            <h5>문서</h5>
          </CCol>

          <AddNewDoc v-if="route.name !== '(문서) - 추가'" :proj-status="issueProject?.status" />
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

        <DocsList
          :category="docsFilter.category as number"
          :category-list="categoryList"
          :docs-list="docsList"
          @select-cate="selectCate"
          @page-select="pageSelect"
        />
      </template>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
