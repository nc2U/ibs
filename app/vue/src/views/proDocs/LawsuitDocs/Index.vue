<script setup lang="ts">
import { computed, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/proDocs/_menu/headermixin1'
import { useAccount } from '@/store/pinia/account'
import { useProject } from '@/store/pinia/project'
import {
  onBeforeRouteUpdate,
  type RouteLocationNormalizedLoaded as Loaded,
  useRoute,
  useRouter,
} from 'vue-router'
import type { User } from '@/store/types/accounts.ts'
import type { Project } from '@/store/types/project.ts'
import { type DocsFilter, type SuitCaseFilter, useDocs } from '@/store/pinia/docs'
import type { AFile, Attatches, Docs, Link, PatchDocs, SuitCase } from '@/store/types/docs'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ListController from '@/components/Documents/ListController.vue'
import CategoryTabs from '@/components/Documents/CategoryTabs.vue'
import DocsList from '@/components/Documents/DocsList.vue'
import DocsView from '@/components/Documents/DocsView.vue'
import DocsForm from '@/components/Documents/DocsForm.vue'

const fController = ref()
const typeNumber = ref(2)
const mainViewName = ref('PR 소송 문서')
const docsFilter = ref<DocsFilter>({
  project: '',
  doc_type: typeNumber.value,
  category: '',
  lawsuit: '',
  ordering: '-created',
  search: '',
  page: 1,
  limit: '',
})

const heatedPage = ref<number[]>([])

const listFiltering = (payload: DocsFilter) => {
  payload.limit = payload.limit || 10
  docsFilter.value.project = payload.project
  docsFilter.value.limit = payload.limit
  docsFilter.value.ordering = payload.ordering
  docsFilter.value.lawsuit = payload.lawsuit
  docsFilter.value.search = payload.search
  if (project.value) fetchDocsList({ ...docsFilter.value })
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

const projStore = useProject()
const projObj = computed(() => projStore.project as Project | null)
const project = computed(() => projObj.value?.pk)
const projName = computed(() => projObj.value?.name)
const company = computed(() => projObj.value?.company)

const accStore = useAccount()
const writeAuth = computed(() => accStore.writeProDocs)

const createDocScrape = (payload: { docs: number; user: number }) =>
  accStore.createDocScrape(payload)

const docStore = useDocs()
const docs = computed(() => docStore.docs)
const docsList = computed(() => docStore.docsList)
const categoryList = computed(() => docStore.categoryList)
const getSuitCase = computed(() => docStore.getSuitCase)

const fetchDocTypeList = () => docStore.fetchDocTypeList()
const fetchLink = (pk: number) => docStore.fetchLink(pk)
const fetchFile = (pk: number) => docStore.fetchFile(pk)
const fetchDocs = (pk: number) => docStore.fetchDocs(pk)
const fetchDocsList = (payload: DocsFilter) => docStore.fetchDocsList(payload)
const fetchCategoryList = (type: number) => docStore.fetchCategoryList(type)
const fetchAllSuitCaseList = (payload: SuitCaseFilter) => docStore.fetchAllSuitCaseList(payload)
const createSuitCase = (payload: SuitCase) => docStore.createSuitCase(payload)

const createDocs = (payload: { form: FormData; isProject: boolean }) => docStore.createDocs(payload)
const updateDocs = (payload: { pk: number; form: FormData; isProject: boolean }) =>
  docStore.updateDocs(payload)
const patchDocs = (payload: PatchDocs & { filter: DocsFilter }) => docStore.patchDocs(payload)
const patchLink = (pk: number, payload: Link) => docStore.patchLink(pk, payload)
const patchFile = (pk: number, payload: any) => docStore.patchFile(pk, payload)

const [route, router] = [useRoute() as Loaded & { name: string }, useRouter()]

watch(route, val => {
  if (val.params.docsId) fetchDocs(Number(val.params.docsId))
  else docStore.removeDocs() //docs = null
})

const docsRenewal = (page: number) => {
  docsFilter.value.page = page
  fetchDocsList(docsFilter.value)
}

const docsScrape = (docs: number) => {
  const user = (accStore.userInfo as User)?.pk as number
  createDocScrape({ docs, user }) // 스크랩 추가
}

const onSubmit = async (payload: Docs & Attatches) => {
  if (project.value) {
    const { pk, ...rest } = payload
    const getData: Record<string, any> = { ...rest }

    getData.issue_project = projObj.value?.issue_project as number

    const form = new FormData()

    for (const key in getData) {
      if (key === 'links' || key === 'files') {
        ;(getData[key] as any[]).forEach(val => form.append(key, JSON.stringify(val)))
      } else if (key === 'newFiles') {
        getData[key]?.forEach(val => {
          form.append('new_files', val.file as Blob)
          form.append('new_descs', val.description as string)
        })
      } else if (key === 'cngFiles') {
        getData[key]?.forEach(val => {
          form.append('cngPks', val.pk as any)
          form.append('cngFiles', val.file as Blob)
        })
      } else if (key === 'newLinks') getData[key].forEach(val => form.append(key, val as string))
      else {
        // 기타 단일 값 처리
        const formValue = getData[key] === null ? '' : getData[key]
        form.append(key, formValue as string)
      }
    }

    if (pk) {
      await updateDocs({ pk, form, ...{ isProject: true } })
      await router.replace({ name: `${mainViewName.value} - 보기`, params: { docsId: pk } })
    } else {
      await createDocs({ form, ...{ isProject: true } })
      await router.replace({ name: `${mainViewName.value}` })
      fController.value.resetForm(false)
    }
  }
}

const createLawSuit = (payload: SuitCase) => {
  if (!payload.issue_project) payload.issue_project = projObj.value?.issue_project as number
  createSuitCase(payload)
}

const docsHit = async (pk: number) => {
  if (!heatedPage.value.includes(pk)) {
    heatedPage.value.push(pk)
    await fetchDocs(pk)
    const hit = ((docs.value as Docs)?.hit ?? 0) + 1
    await patchDocs({ pk, hit, filter: docsFilter.value })
  }
}
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

const dataSetup = (pk: number, docsId?: string | string[]) => {
  docsFilter.value.project = pk
  fetchDocTypeList()
  fetchCategoryList(typeNumber.value)
  fetchDocsList(docsFilter.value)
  if (docsId) fetchDocs(Number(docsId))
  fetchAllSuitCaseList({
    project: pk,
    is_real_dev: 'true',
  }) // Todo 프로젝트마다 변경 로직 구현
}

const dataReset = () => {
  docStore.removeDocs()
  docStore.docsList = []
  docStore.docsCount = 0
  router.replace({ name: `${mainViewName.value}` })
}

const projSelect = (target: number | null) => {
  if (fController.value) fController.value.resetForm(false)
  dataReset()
  if (!!target) dataSetup(target)
  else docStore.removeDocsList()
}

onBeforeRouteUpdate(to => dataSetup(project.value ?? projStore.initProjId, to.params?.docsId))

const loading = ref(true)
onBeforeMount(async () => {
  await dataSetup(project.value ?? projStore.initProjId, route.params?.docsId)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentHeader
    :page-title="pageTitle"
    :nav-menu="navMenu"
    selector="ProjectSelect"
    @proj-select="projSelect"
  />

  <ContentBody>
    <CCardBody class="pb-5">
      <div v-if="route.name === `${mainViewName}`" class="pt-3">
        <ListController
          ref="fController"
          :get-suit-case="getSuitCase"
          :docs-filter="docsFilter"
          @list-filter="listFiltering"
        />

        <CategoryTabs
          :category="docsFilter.category as number"
          :category-list="categoryList"
          @select-cate="selectCate"
        />

        <DocsList
          :project="project as number"
          :limit="docsFilter.limit || 10"
          :page="docsFilter.page || 1"
          :docs-list="docsList"
          :view-route="mainViewName"
          :is-lawsuit="true"
          :write-auth="writeAuth"
          @page-select="pageSelect"
        />
      </div>

      <div v-else-if="route.name.includes('보기')">
        <DocsView
          :type-num="typeNumber"
          :heated-page="heatedPage"
          :re-order="docsFilter.ordering !== '-created'"
          :category="docsFilter.category as number"
          :docs="docs as Docs"
          :view-route="mainViewName"
          :curr-page="docsFilter.page ?? 1"
          :write-auth="writeAuth"
          :docs-filter="docsFilter"
          @docs-hit="docsHit"
          @link-hit="linkHit"
          @file-hit="fileHit"
          @docs-scrape="docsScrape"
          @docs-renewal="docsRenewal"
        />
      </div>

      <div v-else-if="route.name.includes('작성')">
        <DocsForm
          :sort-name="projName"
          :type-num="typeNumber"
          :get-suit-case="getSuitCase"
          :category-list="categoryList"
          :view-route="mainViewName"
          :write-auth="writeAuth"
          @on-submit="onSubmit"
          @create-lawsuit="createLawSuit"
        />
      </div>

      <div v-else-if="route.name.includes('수정')">
        <DocsForm
          :sort-name="projName"
          :type-num="typeNumber"
          :get-suit-case="getSuitCase"
          :category-list="categoryList"
          :docs="docs as Docs"
          :view-route="mainViewName"
          :write-auth="writeAuth"
          @on-submit="onSubmit"
          @create-lawsuit="createLawSuit"
        />
      </div>
    </CCardBody>
  </ContentBody>
</template>
