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
import DocsList from '@/views/_Work/Manages/Documents/components/DocsList.vue'
import DocsDetail from '@/views/_Work/Manages/Documents/components/DocsDetail.vue'
import DocsForm from '@/views/_Work/Manages/Documents/components/DocsForm.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import DocsListAside from '@/views/_Work/Manages/Documents/components/atomics/DocsListAside.vue'

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
  ordering: '-is_pinned,-created',
  search: '',
  page: 1,
  limit: '',
})

const route = useRoute()
const router = useRouter()

const workStore = useWork()
const issueProject = computed<IssueProject | null>(() => workStore.issueProject)

const docStore = useDocs()
const docs = computed<Docs | null>(() => docStore.docs)
const docsList = computed<Docs[]>(() => docStore.docsList)
const categoryList = computed(() => docStore.categoryList)
const getCategories = computed(() => docStore.getCategories)
const getSuitCase = computed(() => docStore.getSuitCase)

const fetchDocs = (pk: number) => docStore.fetchDocs(pk)
const fetchDocsList = (payload: DocsFilter) => docStore.fetchDocsList(payload)
const fetchCategoryList = (type: number) => docStore.fetchCategoryList(type)
const fetchAllSuitCaseList = (payload: SuitCaseFilter) => docStore.fetchAllSuitCaseList(payload)
const deleteDocs = (pk: number, proj?: number) => docStore.deleteDocs(pk, { project: proj })

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

  if (issueProject.value?.type === '3') {
    typeNumber.value = 3
  } else if (typeNumber.value === 3) {
    typeNumber.value = 1
  }
  docsFilter.value.doc_type = typeNumber.value

  docsFilter.value.issue_project = (issueProject.value as IssueProject)?.pk
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
  if (route.query.viewForm) viewForm.value = true
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
            <v-icon icon="mdi-text-box-search-outline" color="green-darken-1" class="mr-2" />
            문서
          </h5>
        </CCol>

        <CCol v-if="route.name === '(문서)'" class="text-right">
          <span v-if="canDocsCreate" class="mr-2 form-text">
            <TextButton name="새 문서" @click="viewForm = !viewForm" :active="false" />
          </span>
        </CCol>

        <CCol v-else class="text-right">
          <span v-if="canDocsUpdate">
            <TextButton
              name="편집"
              icon="mdi-pencil"
              icon-color="amber"
              @click="viewForm = !viewForm"
            />
          </span>

          <span v-if="!viewForm && canDocsDelete">
            <TextButton
              name="삭제"
              icon="mdi-trash-can-outline"
              icon-color="grey"
              @click="RefDelDocs.callModal()"
            />
          </span>
        </CCol>
      </CRow>

      <template v-if="can(PERM.DOCS_READ)">
        <CRow v-if="route.name === '(문서)'" class="mb-3 header">
          <CCol>
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
          v-if="viewForm"
          :project-pk="issueProject?.pk"
          :type-number="typeNumber"
          :categories="getCategories"
          :get-suit-case="getSuitCase"
          :docs="route.name === '(문서)' ? undefined : (docs as Docs)"
          @close-form="viewForm = false"
        />

        <DocsList
          v-if="route.name === '(문서)'"
          :category="docsFilter.category as number"
          :category-list="categoryList"
          :docs-list="docsList"
          @select-cate="selectCate"
          @page-select="pageSelect"
        />

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
      <DocsListAside
        v-if="route.name !== '(문서) - 보기'"
        :type-number="typeNumber"
        :category-list="categoryList"
        :suit-case-options="getSuitCase"
        :filter="docsFilter"
        @select-cate="selectCate"
        @search="fetchDocsList(docsFilter)"
        @update:filter="docsFilter = $event"
      />
    </template>
  </ContentBody>
</template>
