<script setup lang="ts">
import { ref, computed, onBeforeMount, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/comDocs/_menu/headermixin2'
import {
  onBeforeRouteUpdate,
  type RouteLocationNormalizedLoaded as LoadedRoute,
  useRoute,
  useRouter,
} from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import { type DocsFilter, type SuitCaseFilter, useDocs } from '@/store/pinia/docs'
import type { AFile, Attatches, Link, PatchDocs, Docs } from '@/store/types/docs'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ListController from '@/components/Documents/ListController.vue'
import CategoryTabs from '@/components/Documents/CategoryTabs.vue'
import DocsList from '@/components/Documents/DocsList.vue'
import DocsView from '@/components/Documents/DocsView.vue'
import DocsForm from '@/components/Documents/DocsForm.vue'
import { useProject } from '@/store/pinia/project'

const fController = ref()
const typeNumber = ref(2)
const mainViewName = ref('본사 소송 문서')
const docsFilter = ref<DocsFilter>({
  issue_project: '',
  doc_type: typeNumber.value,
  category: '',
  lawsuit: '',
  ordering: '-created',
  search: '',
  page: 1,
  limit: '',
})

const heatedPage = ref<number[]>([])

const newFiles = ref<File[]>([])
const cngFiles = ref<
  {
    pk: number
    file: File
  }[]
>([])

const listFiltering = (payload: DocsFilter) => {
  payload.limit = payload.limit || 10
  docsFilter.value.issue_project = payload.issue_project
  docsFilter.value.lawsuit = payload.lawsuit
  docsFilter.value.ordering = payload.ordering
  docsFilter.value.search = payload.search
  docsFilter.value.limit = payload.limit
  if (company.value) fetchDocsList({ ...docsFilter.value })
}

const selectCate = (cate: number) => {
  docsFilter.value.page = 1
  docsFilter.value.category = cate
  listFiltering(docsFilter.value)
}

const pageSelect = (page: number) => {
  docsFilter.value.page = page
  listFiltering(docsFilter.value)
}

// const comStore = useCompany()
// const company = computed(() => comStore.company?.pk)
const projStore = useProject()
const issue_project = computed(() => projStore.project?.issue_project)

const accStore = useAccount()
const writeAuth = computed(() => accStore.writeComDocs)

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

const createDocs = (payload: { form: FormData }) => docStore.createDocs(payload)
const updateDocs = (payload: { pk: number; form: FormData }) => docStore.updateDocs(payload)
const patchDocs = (payload: PatchDocs & { filter: DocsFilter }) => docStore.patchDocs(payload)
const patchLink = (payload: Link) => docStore.patchLink(payload)
const patchFile = (payload: AFile) => docStore.patchFile(payload)

const [route, router] = [
  useRoute() as LoadedRoute & {
    name: string
  },
  useRouter(),
]

watch(route, val => {
  if (val.params.docsId) fetchDocs(Number(val.params.docsId))
  else docStore.removeDocs() //docs = null
})

const docsRenewal = (page: number) => {
  docsFilter.value.page = page
  fetchDocsList(docsFilter.value)
}
const fileChange = (payload: { pk: number; file: File }) => cngFiles.value.push(payload)

const fileUpload = (file: File) => newFiles.value.push(file)

const docsScrape = (docs: number) => {
  const user = accStore.userInfo?.pk as number
  createDocScrape({ docs, user }) // 스크랩 추가
}

const onSubmit = async (payload: Docs & Attatches) => {
  if (issue_project.value) {
    const { pk, ...getData } = payload
    getData.issue_project = issue_project.value
    getData.newFiles = newFiles.value
    getData.cngFiles = cngFiles.value

    const form = new FormData()

    for (const key in getData) {
      if (key === 'links' || key === 'files') {
        getData[key]?.forEach(val => form.append(key, JSON.stringify(val)))
      } else if (key === 'newLinks' || key === 'newFiles' || key === 'cngFiles') {
        if (key === 'cngFiles') {
          getData[key]?.forEach(val => {
            form.append('cngPks', val.pk as any)
            form.append('cngFiles', val.file as Blob)
          })
        } else getData[key]?.forEach(val => form.append(key, val as string | Blob))
      } else {
        const formValue = getData[key] === null ? '' : getData[key]
        form.append(key, formValue as string)
      }
    }

    if (pk) {
      await updateDocs({ pk, form })
      await router.replace({
        name: `${mainViewName.value} - 보기`,
        params: { docsId: pk },
      })
    } else {
      await createDocs({ form })
      await router.replace({ name: `${mainViewName.value}` })
      fController.value.resetForm()
    }
    newFiles.value = []
    cngFiles.value = []
  }
}

const docsHit = async (pk: number) => {
  if (!heatedPage.value.includes(pk)) {
    heatedPage.value.push(pk)
    await fetchDocs(pk)
    const hit = (docs.value?.hit ?? 0) + 1
    await patchDocs({ pk, hit, filter: docsFilter.value })
  }
}
const linkHit = async (pk: number) => {
  const link = (await fetchLink(pk)) as Link
  link.hit = (link.hit as number) + 1
  await patchLink(link)
}
const fileHit = async (pk: number) => {
  const file = (await fetchFile(pk)) as AFile
  const hit = (file.hit as number) + 1
  await patchFile({ pk, hit })
}

const dataSetup = (pk: number, docsId?: string | string[]) => {
  fetchDocTypeList()
  docsFilter.value.company = pk
  fetchCategoryList(typeNumber.value)
  fetchAllSuitCaseList({ is_com: true })
  fetchDocsList(docsFilter.value)
  if (docsId) fetchDocs(Number(docsId))
}
const dataReset = () => {
  comStore.company = null
  docStore.docs = null
  docStore.docsList = []
  docStore.docsCount = 0
  docsFilter.value.company = ''
  router.replace({ name: `${mainViewName.value}` })
}

const comSelect = (target: number | null) => {
  dataReset()
  if (target) dataSetup(target)
}

onBeforeRouteUpdate(to => dataSetup(company.value || comStore.initComId, to.params?.docsId))

onBeforeMount(() => dataSetup(company.value || comStore.initComId, route.params?.docsId))
</script>

<template>
  <ContentHeader
    :page-title="pageTitle"
    :nav-menu="navMenu"
    selector="CompanySelect"
    @com-select="comSelect"
  />

  <ContentBody>
    <CCardBody class="pb-5">
      <div v-if="route.name === `${mainViewName}`" class="pt-3">
        <ListController
          ref="fController"
          :com-from="true"
          :get-suit-case="getSuitCase"
          :docs-filter="docsFilter"
          @list-filter="listFiltering"
        />

        <CategoryTabs
          :category="docsFilter.category || undefined"
          :category-list="categoryList"
          @select-cate="selectCate"
        />

        <DocsList
          :company="company || undefined"
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
          :category="docsFilter.category as undefined"
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
          :type-num="typeNumber"
          :category-list="categoryList"
          :get-suit-case="getSuitCase"
          :view-route="mainViewName"
          :write-auth="writeAuth"
          @file-upload="fileUpload"
          @on-submit="onSubmit"
        />
      </div>

      <div v-else-if="route.name.includes('수정')">
        <DocsForm
          :type-num="typeNumber"
          :category-list="categoryList"
          :get-suit-case="getSuitCase"
          :docs="docs as Docs"
          :view-route="mainViewName"
          :write-auth="writeAuth"
          @file-change="fileChange"
          @file-upload="fileUpload"
          @on-submit="onSubmit"
        />
      </div>
    </CCardBody>
  </ContentBody>
</template>
