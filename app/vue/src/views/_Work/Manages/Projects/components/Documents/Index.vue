<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useWork } from '@/store/pinia/work_project.ts'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import type { Docs } from '@/store/types/docs.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import { type DocsFilter, type SuitCaseFilter, useDocs } from '@/store/pinia/docs'
import Loading from '@/components/Loading/Index.vue'
import MultiSelect from '@/components/MultiSelect/index.vue'
import DocsList from './components/DocsList.vue'
import DocsDetail from './components/DocsDetail.vue'
import DocsForm from './components/DocsForm.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import TopButton from '../../../../components/atomics/TopButton.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const typeNumber = ref<1 | 2 | 3>(1)
const refDocsForm = ref()
const RefDelDocs = ref()

const types = ref<any[]>([
  { value: 1, label: '일반문서' },
  { value: 2, label: '소송기록' },
])

const { can, PERM } = usePerms()
const canDocsCreate = computed(() => can(PERM.DOCS_CREATE) && issueProject.value?.status !== '9')
const canDocsUpdate = computed(() => can(PERM.DOCS_UPDATE))
const canDocsDelete = computed(() => can(PERM.DOCS_DELETE))

const viewForm = ref(false)

const docsFilter = ref<DocsFilter>({
  doc_type: typeNumber.value,
  category: '',
  issue_project: '',
  lawsuit: '',
  ordering: '-created',
  search: '',
  page: 1,
  limit: '',
})

const route = useRoute()
const router = useRouter()

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
const deleteDocs = (pk: number, proj?: number) => docStore.deleteDocs(pk, { project: proj })

const categories = computed(() => getCategories.value)

const getDocsList = (target: unknown) => {
  if (target === 1 || target === 2) {
    docsFilter.value.page = 1
    docsFilter.value.doc_type = target as number
    fetchCategoryList(target as 1 | 2 | 3)
    fetchDocsList(docsFilter.value)
    if (viewForm.value) refDocsForm.value.setDocType(target as number)
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
    await docStore.hitDocs(pk)
  }
}

const docsDelConfirm = async () => {
  RefDelDocs.value.close()
  const docId = docs.value?.pk
  const projId = Number(route.params.projId)
  if (docId) await deleteDocs(docId, projId)

  await router.replace({ name: '(문서)' })
}

const dataSetup = async (docId?: string | string[]) => {
  if (route.params.projId) {
    const projId = route.params.projId as string
    await workStore.fetchIssueProject(projId)
  }

  if (issueProject.value?.sort === '3') {
    typeNumber.value = 3
  } else if (typeNumber.value === 3) {
    typeNumber.value = 1
  }
  docsFilter.value.doc_type = typeNumber.value

  docsFilter.value.issue_project = (issueProject.value as IssueProject)?.pk
  await fetchDocTypeList()
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
      <span v-if="route.name !== '(문서)'">
        <router-link :to="{ name: '(문서)' }">문서</router-link>
        »
      </span>

      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon icon="mdi-file-document-multiple-outline" color="info" class="mr-2" />
            {{ ($route?.name as string).replace(/^\((.*)\)$/, '$1') }}
          </h5>
        </CCol>

        <CCol v-if="route.name === '(문서)'" class="text-right">
          <span v-if="canDocsCreate" class="mr-2 form-text">
            <TopButton name="새 문서" @click="viewForm = !viewForm" :active="false" />
          </span>
        </CCol>

        <CCol v-else class="text-right">
          <span v-if="canDocsUpdate">
            <TopButton
              name="편집"
              icon="mdi-pencil"
              icon-color="amber"
              @click="viewForm = !viewForm"
            />
          </span>

          <span v-if="!viewForm && canDocsDelete">
            <TopButton
              name="삭제"
              icon="mdi-trash-can-outline"
              icon-color="grey"
              @click="RefDelDocs.callModal()"
            />
          </span>
        </CCol>
      </CRow>

      <DocsForm
        v-if="viewForm"
        :issue-project="issueProject as IssueProject"
        :type-number="typeNumber"
        :categories="categories"
        :get-suit-case="getSuitCase"
        @close-form="viewForm = false"
      />

      <template v-if="can(PERM.DOCS_READ)">
        <template v-if="route.name === '(문서)'">
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

        <DocsDetail
          v-else-if="route.name === '(문서) - 보기'"
          :docs="docs as Docs"
          @docs-hit="docsHit"
        />
      </template>
      <v-alert v-else color="warning" class="mt-4" variant="tonal">
        <v-icon icon="mdi-alert-circle" class="mr-2" />
        문서를 조회할 수 있는 권한이 없습니다.
      </v-alert>

      <ConfirmModal ref="RefDelDocs">
        <template #default>이 문서의 삭제를 계속 진행하시겠습니까?</template>
        <template #footer>
          <v-btn color="warning" size="small" @click="docsDelConfirm">삭제</v-btn>
        </template>
      </ConfirmModal>
    </template>

    <template v-slot:aside>
      <CRow class="mb-4 pr-2 mr-2">
        <CCol>
          <h6 class="asideTitle">문서 카테고리</h6>
          <v-divider class="mt-0" />
          <v-list density="compact" nav class="pa-0 aside-menu card-white">
            <v-list-item
              :active="docsFilter.category === '' || docsFilter.category === 0"
              @click="selectCate(0)"
              rounded="lg"
            >
              <template v-slot:prepend>
                <v-icon icon="mdi-folder-outline" size="small" />
              </template>
              <v-list-item-title>전체 문서</v-list-item-title>
            </v-list-item>

            <v-list-item
              v-for="cate in categoryList"
              :key="cate.pk as number"
              :active="docsFilter.category === cate.pk"
              @click="selectCate(cate.pk as number)"
              rounded="lg"
            >
              <template v-slot:prepend>
                <v-icon
                  icon="mdi-folder-text-outline"
                  size="small"
                  :color="cate.color ?? 'secondary'"
                />
              </template>
              <v-list-item-title>{{ cate.name }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </CCol>
      </CRow>

      <CRow>
        <CCol class="mt-4">
          <h6 class="asideTitle">{{ typeNumber === 1 ? '키워드' : '관련 사건' }}</h6>
          <v-divider class="mt-0" />
        </CCol>
      </CRow>

      <template v-if="typeNumber === 2">
        <CRow v-if="getSuitCase.length" class="mb-3 mr-2">
          <CCol>
            <MultiSelect
              mode="single"
              v-model="docsFilter.lawsuit"
              :options="getSuitCase"
              placeholder="관련 사건 목록"
            />
          </CCol>
        </CRow>
      </template>

      <CRow class="mb-3 mr-2">
        <CCol>
          <CFormInput
            v-model="docsFilter.search"
            placeholder="검색어"
            @keydown.enter="fetchDocsList(docsFilter)"
          />
        </CCol>
      </CRow>

      <CRow class="mr-2">
        <CCol class="text-right">
          <v-btn size="small" color="info" @click="fetchDocsList(docsFilter)">검색</v-btn>
        </CCol>
      </CRow>
    </template>
  </ContentBody>
</template>
