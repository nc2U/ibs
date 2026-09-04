<script lang="ts" setup>
import { computed, onBeforeMount, provide, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useWork } from '@/store/pinia/work_project.ts'
import { type DocsFilter, type SuitCaseFilter, useDocs } from '@/store/pinia/docs'
import { useCompany } from '@/store/pinia/company.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Company } from '@/store/types/settings'
import type { AFile, Docs, Link, SuitCase } from '@/store/types/docs'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import DocsList from './components/DocsList.vue'
import Loading from '@/components/Loading/Index.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import DocsForm from '@/views/_Work/Manages/Documents/components/DocsForm.vue'
import DocsListAside from '@/views/_Work/Manages/Documents/components/atomics/DocsListAside.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import CaseList from '@/components/LawSuitCase/CaseList.vue'
import CaseDetail from '@/components/LawSuitCase/CaseDetail.vue'
import CaseForm from '@/components/LawSuitCase/CaseForm.vue'

const cBody = ref()
const sideNavCAll = () => cBody.value.toggle()

const typeNumber = ref<1 | 2>(1)
const types = ref([
  { value: 1, label: '일반문서' },
  { value: 2, label: '소송기록' },
])

const isSuitCase = computed(() => String(route.name ?? '').startsWith('문서 사건'))
const mainViewName = ref('문서 사건')

const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const route = useRoute()
const router = useRouter()

const { can, PERM } = usePerms()
const canDocsRead = computed(() => can(PERM.DOCS_READ))
const canDocsCreate = computed(() => can(PERM.DOCS_CREATE))

const viewForm = ref(false)

const workStore = useWork()
const myProjects = computed(() => workStore.getMyProjects.filter(pjt => pjt.module?.document))

const docStore = useDocs()
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

provide('navMenu', navMenu)
provide('query', route?.query)

const fetchDocsList = (payload: DocsFilter) => docStore.fetchDocsList(payload)
const fetchCategoryList = (type: number) => docStore.fetchCategoryList(type)

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
  () => `/excel/suitcases/?company=${company.value?.pk ?? ''}&${excelFilter.value}`,
)

const getDocsList = (target: unknown) => {
  if (target === 1 || target === 2) {
    if (route.name !== '문서') {
      router.push({ name: '문서' })
    }
    docsFilter.value.page = 1
    docsFilter.value.doc_type = target as number
    fetchCategoryList(target as 1 | 2)
    fetchDocsList(docsFilter.value)
  }
}

const goToSuitCase = () => {
  caseFilter.value.company = company.value?.pk ?? ''
  caseFilter.value.issue_project = docsFilter.value.issue_project ?? ''
  fetchSuitCaseList(caseFilter.value)
  if (route.name !== '문서 사건' && !String(route.name ?? '').startsWith('문서 사건 -')) {
    router.push({ name: '문서 사건' })
  }
}

const goToDocs = () => {
  router.push({ name: '문서' })
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
    company: company.value?.pk ?? '',
    issue_project: docsFilter.value.issue_project ?? '',
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
      params: { caseId: payload.pk },
    })
  } else {
    if (!payload.issue_project) {
      payload.issue_project =
        (docsFilter.value.issue_project as number) ||
        (company.value?.com_issue_project as number) ||
        null
    }
    await createSuitCase(payload)
    await router.replace({ name: mainViewName.value })
  }
}

const onCaseDelete = async (pk: number) => {
  await deleteSuitCase(pk)
  await router.replace({ name: mainViewName.value })
}

const loading = ref<boolean>(true)
const initData = async () => {
  loading.value = true
  try {
    await workStore.fetchAllProjectList()
    await fetchAllSuitCaseList({ company: company.value?.pk ?? '' })
    if (isSuitCase.value) {
      caseFilter.value.company = company.value?.pk ?? ''
      caseFilter.value.issue_project = docsFilter.value.issue_project ?? ''
      await fetchSuitCaseList(caseFilter.value)
    } else {
      await fetchCategoryList(typeNumber.value as 1 | 2)
      await fetchDocsList(docsFilter.value)
    }
  } catch (err) {
    console.error('Failed to load documents data:', err)
  } finally {
    loading.value = false
  }
}

onBeforeMount(async () => {
  if (isSuitCase.value) {
    if (route.params.caseId) {
      await fetchSuitCase(Number(route.params.caseId))
    }
  }
  await initData()
})

watch(
  () => route.name,
  async newName => {
    const nameStr = String(newName ?? '')
    if (nameStr === '문서') {
      await initData()
    } else if (nameStr.startsWith('문서 사건')) {
      if (route.params.caseId) {
        await fetchSuitCase(Number(route.params.caseId))
      } else {
        docStore.removeSuitcase()
        await fetchSuitCaseList(caseFilter.value)
      }
    }
  },
)

watch(
  () => docsFilter.value.issue_project,
  newProject => {
    docsFilter.value.page = 1
    caseFilter.value.issue_project = newProject
    caseFilter.value.page = 1
    if (isSuitCase.value) {
      fetchSuitCaseList(caseFilter.value)
    } else {
      fetchDocsList(docsFilter.value)
    }
  },
)
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon
              :icon="isSuitCase ? 'mdi-scale-balance' : 'mdi-text-box-search-outline'"
              color="primary"
              class="mr-2"
            />
            {{ isSuitCase ? '소송 사건' : '문서' }}
          </h5>
        </CCol>

        <CCol class="text-right">
          <!-- 문서/소송사건 전환 및 대외 공문 발송 대장 바로가기 -->
          <v-btn
            v-if="isSuitCase"
            size="small"
            variant="tonal"
            color="indigo-lighten-1"
            prepend-icon="mdi-text-box-search-outline"
            class="mr-2"
            @click="goToDocs"
          >
            문서 목록
          </v-btn>
          <v-btn
            v-else
            size="small"
            variant="tonal"
            color="deep-purple-lighten-1"
            prepend-icon="mdi-scale-balance"
            class="mr-2"
            @click="goToSuitCase"
          >
            소송 사건
          </v-btn>

          <!-- 새 문서 또는 새 사건 등록 버튼 -->
          <span v-if="canDocsCreate && !isSuitCase" class="mr-2 form-text">
            <TextButton name="새 문서" @click="viewForm = !viewForm" :active="false" />
          </span>
          <span
            v-else-if="canDocsCreate && isSuitCase && route.name === '문서 사건'"
            class="mr-2 form-text"
          >
            <TextButton
              name="새 사건"
              @click="router.push({ name: `${mainViewName} - 작성` })"
              :active="false"
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
              :company="company?.pk || undefined"
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
              :sort-name="comName ?? '[본사]'"
              :get-suit-case="getSuitCase"
              :view-route="mainViewName"
              @on-submit="onCaseSubmit"
            />
          </div>

          <!-- 사건 수정 -->
          <div v-else-if="String(route.name ?? '').includes('수정')">
            <CaseForm
              :sort-name="comName ?? '[본사]'"
              :get-suit-case="getSuitCase"
              :suitcase="suitcase"
              :view-route="mainViewName"
              @on-submit="onCaseSubmit"
            />
          </div>
        </template>

        <!-- 일반 문서 (1) & 소송 기록 (2) 화면 -->
        <template v-else>
          <CRow class="mb-3 header">
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
            :type-number="typeNumber"
            :categories="getCategories"
            :get-suit-case="getSuitCase"
            :my-projects="myProjects"
            @close-form="viewForm = false"
          />

          <DocsList
            :category="docsFilter.category as number"
            :category-list="categoryList"
            :docs-list="docsList"
            @select-cate="selectCate"
            @page-select="pageSelect"
          />
        </template>
      </template>

      <v-alert v-else color="warning" class="mt-4" variant="tonal">
        <v-icon icon="mdi-alert-circle" class="mr-2" />
        문서를 조회할 수 있는 권한이 없습니다.
      </v-alert>
    </template>

    <template v-slot:aside>
      <DocsListAside
        :my-projects="myProjects"
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
