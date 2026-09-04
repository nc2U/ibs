<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useWork } from '@/store/pinia/work_project.ts'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import type { AFile, Docs, Link, SuitCase } from '@/store/types/docs.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import { type DocsFilter, type SuitCaseFilter, useDocs } from '@/store/pinia/docs'
import Loading from '@/components/Loading/Index.vue'
import DocsList from '@/views/_Work/Manages/Documents/components/DocsList.vue'
import DocsDetail from '@/views/_Work/Manages/Documents/components/DocsDetail.vue'
import DocsForm from '@/views/_Work/Manages/Documents/components/DocsForm.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import DocsListAside from '@/views/_Work/Manages/Documents/components/atomics/DocsListAside.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import CaseList from '@/components/LawSuitCase/CaseList.vue'
import CaseDetail from '@/components/LawSuitCase/CaseDetail.vue'
import CaseForm from '@/components/LawSuitCase/CaseForm.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const typeNumber = ref<1 | 2>(1)
const refDocsForm = ref()
const RefDelDocs = ref()

const types = ref([
  { value: 1, label: '일반문서' },
  { value: 2, label: '소송기록' },
])

const isSuitCase = computed(() => String(route.name ?? '').startsWith('(문서 사건)'))
const mainViewName = ref('(문서 사건)')

const { can, PERM } = usePerms()
const canDocsRead = computed(() => can(PERM.DOCS_READ))
const canDocsCreate = computed(() => can(PERM.DOCS_CREATE) && currentProject.value?.status === '1')
const canDocsUpdate = computed(() => can(PERM.DOCS_UPDATE))
const canDocsDelete = computed(() => can(PERM.DOCS_DELETE))

const viewForm = ref(false)

const route = useRoute()
const router = useRouter()

const workStore = useWork()
const currentProject = computed<IssueProject | null>(() => workStore.currentProject)

const docStore = useDocs()
const docs = computed<Docs | null>(() => docStore.docs)
const docsList = computed<Docs[]>(() => docStore.docsList)
const categoryList = computed(() => docStore.categoryList)
const getCategories = computed(() => docStore.getCategories)
const getSuitCase = computed(() => docStore.getSuitCase)

const suitcase = computed(() => docStore.suitcase)
const suitcaseList = computed(() => docStore.suitcaseList)

const docsFilter = ref<DocsFilter>({
  doc_type: 1,
  category: '',
  issue_project: '',
  ordering: '-is_pinned,-created',
  search: '',
  page: 1,
  limit: '',
})

const caseFilter = ref<SuitCaseFilter>({
  company: '',
  issue_project: '',
  sort: '',
  level: '',
  court: '',
  related_case: '',
  in_progress: '',
  search: '',
  page: 1,
  limit: 10,
})

const fetchDocs = (pk: number) => docStore.fetchDocs(pk)
const fetchDocsList = (payload: DocsFilter) => docStore.fetchDocsList(payload)
const fetchCategoryList = (type: number) => docStore.fetchCategoryList(type)
const deleteDocs = (pk: number, proj?: number) => docStore.deleteDocs(pk, { project: proj })

const fetchSuitCase = (pk: number) => docStore.fetchSuitCase(pk)
const fetchSuitCaseList = (payload: SuitCaseFilter) => docStore.fetchSuitCaseList(payload)
const fetchAllSuitCaseList = (payload: SuitCaseFilter) => docStore.fetchAllSuitCaseList(payload)
const createSuitCase = (payload: SuitCase) => docStore.createSuitCase(payload)
const updateSuitCase = (payload: SuitCase) => docStore.updateSuitCase(payload)
const deleteSuitCase = (pk: number) => docStore.deleteSuitCase(pk)
const fetchLink = (pk: number) => docStore.fetchLink(pk)
const fetchFile = (pk: number) => docStore.fetchFile(pk)
const patchLink = (pk: number, payload: Link) => docStore.patchLink(pk, payload)
const patchFile = (pk: number, payload: any) => docStore.patchFile(pk, payload)

const linkHit = async (pk: number) => {
  const link = (await fetchLink(pk)) as Link
  link.hit = (link.hit as number) + 1
  await patchLink(pk, link)
}

const fileHit = async (pk: number) => {
  const file = (await fetchFile(pk)) as AFile
  const hit = (file.hit as number) + 1
  await patchFile(pk, { hit })
}

const casesRenewal = (page: number) => {
  caseFilter.value.page = page
  fetchSuitCaseList(caseFilter.value)
}

const excelFilter = computed(() => {
  const { issue_project, sort, level, court, in_progress, search } = caseFilter.value
  return `issue_project=${issue_project ?? ''}&sort=${sort ?? ''}&level=${level ?? ''}&court=${court ?? ''}&in_progress=${in_progress ?? ''}&search=${search ?? ''}`
})
const excelUrl = computed(
  () => `/excel/suitcases/?company=${currentProject.value?.company ?? ''}&${excelFilter.value}`,
)

const getDocsList = (target: unknown) => {
  if (target === 1 || target === 2) {
    if (route.name !== '(문서)') {
      router.push({ name: '(문서)', params: { projId: projId.value } })
    }
    docsFilter.value.page = 1
    docsFilter.value.doc_type = target as number
    fetchCategoryList(target as 1 | 2)
    fetchDocsList(docsFilter.value)
    if (viewForm.value) refDocsForm.value.setDocType(target as number)
  }
}

const goToSuitCase = () => {
  caseFilter.value.company = currentProject.value?.company ?? ''
  caseFilter.value.issue_project = currentProject.value?.pk ?? docsFilter.value.issue_project ?? ''
  fetchSuitCaseList(caseFilter.value)
  if (route.name !== '(문서 사건)' && !String(route.name ?? '').startsWith('(문서 사건) -')) {
    router.push({ name: '(문서 사건)', params: { projId: projId.value } })
  }
}

const goToDocs = () => {
  router.push({ name: '(문서)', params: { projId: projId.value } })
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

const casePageSelect = (page: number) => {
  caseFilter.value.page = page
  fetchSuitCaseList(caseFilter.value)
}

const agencyFilter = (court: string) => {
  caseFilter.value.page = 1
  caseFilter.value.court = court
  fetchSuitCaseList(caseFilter.value)
}

const agencySearch = (agent: string) => {
  caseFilter.value.page = 1
  caseFilter.value.search = agent
  fetchSuitCaseList(caseFilter.value)
}

const relatedFilter = (related: number) => {
  caseFilter.value.page = 1
  caseFilter.value.related_case = related
  fetchSuitCaseList(caseFilter.value)
}

const caseReset = () => {
  caseFilter.value = {
    company: currentProject.value?.company ?? '',
    issue_project: currentProject.value?.pk ?? docsFilter.value.issue_project ?? '',
    sort: '',
    level: '',
    court: '',
    related_case: '',
    in_progress: '',
    search: '',
    page: 1,
    limit: 10,
  }
  fetchSuitCaseList(caseFilter.value)
}

const onCaseSubmit = async (payload: SuitCase) => {
  if (payload.pk) {
    await updateSuitCase(payload)
    await router.replace({
      name: `${mainViewName.value} - 보기`,
      params: { projId: projId.value, caseId: payload.pk },
    })
  } else {
    if (!payload.issue_project) {
      payload.issue_project =
        (currentProject.value?.pk as number) ||
        (docsFilter.value.issue_project as number) ||
        null
    }
    await createSuitCase(payload)
    await router.replace({ name: mainViewName.value, params: { projId: projId.value } })
  }
}

const onCaseDelete = async (pk: number) => {
  await deleteSuitCase(pk)
  await router.replace({ name: mainViewName.value, params: { projId: projId.value } })
}

const heatedPage = ref<number[]>([])

const docsHit = async (pk: number) => {
  if (!heatedPage.value.includes(pk)) {
    heatedPage.value.push(pk)
    await docStore.hitDocs(pk)
  }
}

const projId = computed(() => route.params.projId)

watch(
  () => projId.value,
  async nVal => {
    if (nVal) {
      await dataSetup(nVal as string, docId.value)
    }
  },
)

const docId = computed(() => route.params.docId)

watch(
  () => docId.value,
  nVal => {
    if (nVal) dataSetup(projId.value as string, nVal)
  },
)

const docsDelConfirm = async () => {
  RefDelDocs.value.close()
  const docId = docs.value?.pk
  if (docId && projId) await deleteDocs(docId, Number(projId.value))

  await router.replace({ name: '(문서)', params: { projId: projId.value } })
}

const loading = ref<boolean>(true)

const dataSetup = async (projId: string, docId?: string | string[]) => {
  loading.value = true
  try {
    if (projId && (!currentProject.value || currentProject.value.slug !== projId)) {
      await workStore.fetchIssueProject(projId as string)
    }

    if (currentProject.value?.type === '3') {
      typeNumber.value = 2 // 소송 워크스페이스인 경우 기본 소송기록
    } else {
      typeNumber.value = 1
    }

    const currentProjPk = currentProject.value?.pk ?? ''
    docsFilter.value.doc_type = typeNumber.value
    docsFilter.value.issue_project = currentProjPk

    caseFilter.value.company = currentProject.value?.company ?? ''
    caseFilter.value.issue_project = currentProjPk

    const tasks: Promise<any>[] = [
      fetchAllSuitCaseList({ issue_project: currentProjPk }),
    ]

    if (isSuitCase.value) {
      if (route.params.caseId) {
        tasks.push(fetchSuitCase(Number(route.params.caseId)))
      } else {
        tasks.push(fetchSuitCaseList(caseFilter.value))
      }
    } else {
      tasks.push(fetchCategoryList(typeNumber.value))
      tasks.push(fetchDocsList(docsFilter.value))
      if (docId) tasks.push(fetchDocs(Number(docId)))
    }

    await Promise.all(tasks)
  } catch (err) {
    console.error('Failed to load project documents data:', err)
  } finally {
    loading.value = false
  }
}

onBeforeMount(async () => {
  if (route.query.viewForm) viewForm.value = true
  await dataSetup(projId.value as string, docId.value)
})

watch(
  () => route.name,
  async newName => {
    const nameStr = String(newName ?? '')
    if (nameStr === '(문서)') {
      await dataSetup(projId.value as string, docId.value)
    } else if (nameStr.startsWith('(문서 사건)')) {
      if (route.params.caseId) {
        await fetchSuitCase(Number(route.params.caseId))
      } else {
        docStore.removeSuitcase()
        caseFilter.value.issue_project = currentProject.value?.pk ?? ''
        await fetchSuitCaseList(caseFilter.value)
      }
    }
  },
)
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody">
    <template v-slot:default>
      <span v-if="route.name !== '(문서)' && route.name !== '(문서 사건)'">
        <router-link :to="{ name: isSuitCase ? '(문서 사건)' : '(문서)', params: { projId } }">
          {{ isSuitCase ? '소송 사건' : '문서' }}
        </router-link>
        »
      </span>

      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon
              :icon="isSuitCase ? 'mdi-scale-balance' : 'mdi-text-box-search-outline'"
              :color="isSuitCase ? 'primary' : 'green-darken-1'"
              class="mr-2"
            />
            {{ isSuitCase ? '소송 사건' : '문서' }}
          </h5>
        </CCol>

        <CCol v-if="!isSuitCase && route.name === '(문서)'" class="text-right">
          <!-- 문서/소송사건 전환 버튼 -->
          <v-btn
            size="small"
            variant="tonal"
            color="deep-purple-lighten-1"
            prepend-icon="mdi-scale-balance"
            class="mr-2"
            @click="goToSuitCase"
          >
            소송 사건
          </v-btn>

          <span v-if="canDocsCreate" class="mr-2 form-text">
            <TextButton name="새 문서" @click="viewForm = !viewForm" :active="false" />
          </span>
        </CCol>

        <CCol v-else-if="isSuitCase && route.name === '(문서 사건)'" class="text-right">
          <!-- 문서 목록 복귀 버튼 -->
          <v-btn
            size="small"
            variant="tonal"
            color="indigo-lighten-1"
            prepend-icon="mdi-text-box-search-outline"
            class="mr-2"
            @click="goToDocs"
          >
            문서 목록
          </v-btn>

          <span v-if="canDocsCreate" class="mr-2 form-text">
            <TextButton
              name="새 사건"
              @click="router.push({ name: `${mainViewName} - 작성`, params: { projId } })"
              :active="false"
            />
          </span>
        </CCol>

        <CCol v-else-if="isSuitCase" class="text-right">
          <!-- 소송 사건 상세/작성/수정 시 상단 버튼 -->
          <v-btn
            size="small"
            variant="tonal"
            color="indigo-lighten-1"
            prepend-icon="mdi-text-box-search-outline"
            class="mr-2"
            @click="goToDocs"
          >
            문서 목록
          </v-btn>
        </CCol>

        <CCol v-else class="text-right">
          <!-- 일반문서 보기 화면에서의 편집/삭제 -->
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

      <template v-if="canDocsRead">
        <!-- 소송 사건 화면 -->
        <template v-if="isSuitCase">
          <!-- 사건 목록 -->
          <div v-if="route.name === mainViewName" class="pt-4">
            <TableTitleRow
              title="소송 사건 목록"
              excel
              :url="excelUrl"
              filename="소송사건.xlsx"
              :disabled="!suitcaseList.length"
            />

            <CaseList
              :company="currentProject?.company || undefined"
              :limit="caseFilter.limit || 10"
              :page="caseFilter.page || 1"
              :case-list="suitcaseList"
              :view-route="mainViewName"
              @page-select="casePageSelect"
              @agency-filter="agencyFilter"
              @agency-search="agencySearch"
              @related-filter="relatedFilter"
            />
          </div>

          <!-- 사건 상세 보기 -->
          <div v-else-if="String(route.name ?? '').includes('보기')">
            <CaseDetail
              v-if="suitcase"
              :curr-page="caseFilter.page ?? 1"
              :suitcase="suitcase as SuitCase"
              :view-route="mainViewName"
              @link-hit="linkHit"
              @file-hit="fileHit"
              @cases-renewal="casesRenewal"
              @post-delete="onCaseDelete"
            />
          </div>

          <!-- 사건 신규 등록 -->
          <div v-else-if="String(route.name ?? '').includes('작성')">
            <CaseForm
              :sort-name="currentProject?.name ?? '[워크스페이스]'"
              :get-suit-case="getSuitCase"
              :view-route="mainViewName"
              @on-submit="onCaseSubmit"
            />
          </div>

          <!-- 사건 수정 -->
          <div v-else-if="String(route.name ?? '').includes('수정')">
            <CaseForm
              :sort-name="currentProject?.name ?? '[워크스페이스]'"
              :get-suit-case="getSuitCase"
              :suitcase="suitcase"
              :view-route="mainViewName"
              @on-submit="onCaseSubmit"
            />
          </div>
        </template>

        <!-- 일반 문서 (1) & 소송 기록 (2) 화면 -->
        <template v-else>
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
            ref="refDocsForm"
            v-if="viewForm"
            :project-pk="currentProject?.pk"
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
        v-if="route.name !== '(문서) - 보기' && !String(route.name ?? '').includes('보기')"
        :type-number="isSuitCase ? 3 : typeNumber"
        :category-list="categoryList"
        :suit-case-options="getSuitCase"
        :filter="docsFilter"
        :case-filter="caseFilter"
        @select-cate="selectCate"
        @search="fetchDocsList(docsFilter)"
        @update:filter="docsFilter = $event"
        @update:caseFilter="caseFilter = $event"
        @case-search="fetchSuitCaseList(caseFilter)"
        @case-reset="caseReset"
      />
    </template>
  </ContentBody>
</template>
