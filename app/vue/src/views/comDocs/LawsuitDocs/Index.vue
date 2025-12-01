<script setup lang="ts">
import { computed, onBeforeMount, ref, watch } from 'vue'
import Cookies from 'js-cookie'
import { navMenu, pageTitle } from '@/views/comDocs/_menu/headermixin'
import {
  onBeforeRouteUpdate,
  onBeforeRouteLeave,
  type RouteLocationNormalizedLoaded as LoadedRoute,
  useRoute,
  useRouter,
} from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useAccount } from '@/store/pinia/account'
import { useCompany } from '@/store/pinia/company'
import type { User } from '@/store/types/accounts.ts'
import type { Company } from '@/store/types/settings.ts'
import { type DocsFilter, type SuitCaseFilter, useDocs } from '@/store/pinia/docs'
import type { AFile, Attatches, Docs, Link, PatchDocs, SuitCase } from '@/store/types/docs'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ComDocsAuthGuard from '@/components/AuthGuard/ComDocsAuthGuard.vue'
import ListController from '@/components/Documents/ListController.vue'
import CategoryTabs from '@/components/Documents/CategoryTabs.vue'
import DocsList from '@/components/Documents/DocsList.vue'
import DocsView from '@/components/Documents/DocsView.vue'
import DocsForm from '@/components/Documents/DocsForm.vue'
import Loading from '@/components/Loading/Index.vue'

const fController = ref()
const refDocsForm = ref()
const typeNumber = ref(2)
const mainViewName = ref('본사 소송 문서')

// URL에서 company 파라미터 읽기
const urlCompanyId = computed(() => {
  const id = route.query.company
  return id ? parseInt(id as string, 10) : null
})
const docsFilter = ref<DocsFilter>({
  company: '',
  issue_project: '',
  is_real_dev: 'false',
  doc_type: typeNumber.value,
  category: '',
  lawsuit: '',
  ordering: '-created',
  search: '',
  page: 1,
  limit: '',
})

const heatedPage = ref<number[]>([])

const formTitle = ref<string>('[본사]')
const listFiltering = (payload: DocsFilter) => {
  payload.limit = payload.limit || 10
  if (!payload.issue_project) {
    docsFilter.value.company = company.value as number
    docsFilter.value.issue_project = (comStore.company as Company)?.com_issue_project ?? ''
    docsFilter.value.is_real_dev = 'false'
    formTitle.value = '[본사]'
  } else {
    docsFilter.value.issue_project = payload.issue_project
    docsFilter.value.is_real_dev = ''
    formTitle.value = getAllProjPks.value.filter(p => p.value == payload.issue_project)[0].label
  }

  fetchAllSuitCaseList({ issue_project: docsFilter.value.issue_project })
  docsFilter.value.lawsuit = payload.lawsuit
  docsFilter.value.ordering = payload.ordering
  docsFilter.value.search = payload.search
  docsFilter.value.limit = payload.limit
  fetchDocsList({ ...docsFilter.value })
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

const comStore = useCompany()
const company = computed(() => (comStore.company as Company)?.pk)
const comIProject = computed(() => (comStore.company as Company)?.com_issue_project ?? '')

const workStore = useWork()
const getAllProjPks = computed(() => workStore.getAllProjPks)

const accStore = useAccount()
const writeAuth = computed(() => accStore.writeComDocs)

const createDocScrape = (payload: { docs: number; user: number }) =>
  accStore.createDocScrape(payload)

const docStore = useDocs()
const docs = computed<Docs | null>(() => docStore.docs)
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

const createDocs = (payload: { form: FormData }) => docStore.createDocs(payload)
const updateDocs = (payload: { pk: number; form: FormData }) => docStore.updateDocs(payload)
const patchDocs = (payload: PatchDocs & { filter: DocsFilter }) => docStore.patchDocs(payload)
const patchLink = (pk: number, payload: Link) => docStore.patchLink(pk, payload)
const patchFile = (pk: number, payload: any) => docStore.patchFile(pk, payload)

const [route, router] = [
  useRoute() as LoadedRoute & {
    name: string
  },
  useRouter(),
]

watch(route, val => {
  if (val.params.docsId) fetchDocs(Number(val.params.docsId))
  else docStore.removeDocs()
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
  if (company.value) {
    const { pk, ...rest } = payload
    const getData: Record<string, any> = { ...rest }

    if (!payload.issue_project)
      getData.issue_project =
        (comIProject.value as number) ?? docsFilter.value.issue_project ?? null

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
      await updateDocs({ pk, form })
      await router.replace({ name: `${mainViewName.value} - 보기`, params: { docsId: pk } })
    } else {
      await createDocs({ form })
      await router.replace({ name: `${mainViewName.value}` })
    }
  }
}

const createLawSuit = (payload: SuitCase) => {
  if (!payload.issue_project)
    payload.issue_project = docsFilter.value.issue_project
      ? (docsFilter.value.issue_project as number)
      : (comIProject.value as number)
  createSuitCase(payload)
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
  await patchLink(pk, link)
}
const fileHit = async (pk: number) => {
  const file = (await fetchFile(pk)) as AFile
  const hit = (file.hit as number) + 1
  await patchFile(pk, { hit })
}

watch(route, val => {
  if (val.params.docsId) fetchDocs(Number(val.params.docsId))
  else docStore.removeDocs()
})

watch(comIProject, val => {
  if (val)
    fetchAllSuitCaseList({
      company: company.value as number,
      issue_project: val,
    })
})

// ContentHeader 강제 리렌더링용
const headerKey = ref(0)

// company 변경을 감지하여 자동으로 데이터 다시 로드
const isInitializing = ref(true)
watch(
  company,
  async (newCompany, oldCompany) => {
    // 초기화 중이거나 URL에서 회사 변경 중인 경우 무시
    if (isInitializing.value) return

    if (newCompany && newCompany !== oldCompany && oldCompany !== undefined) {
      await fetchAllSuitCaseList({
        company: newCompany,
        issue_project: comIProject.value,
      })
      await dataSetup(newCompany, route.params?.docsId)
    }
  },
  { immediate: false },
)

const dataSetup = async (pk: number, docsId?: string | string[]) => {
  docsFilter.value.company = pk

  // workStore.fetchAllIssueProjectList가 회사를 변경하므로 현재 회사 저장
  const targetCompany = pk

  await workStore.fetchAllIssueProjectList(pk, '2', '')

  // workStore 함수가 회사를 변경했다면 다시 원래 회사로 복원
  if (company.value !== targetCompany) {
    Cookies.set('curr-company', `${targetCompany}`)
    await comStore.fetchCompany(targetCompany)
  }

  await fetchDocTypeList()
  await fetchCategoryList(typeNumber.value)
  await fetchDocsList(docsFilter.value)
  if (docsId) await fetchDocs(Number(docsId))
}
const dataReset = () => {
  docsFilter.value.issue_project = ''
  docsFilter.value.is_real_dev = 'false'
  // 문서 리스트만 리셋하고 현재 문서는 유지
  docStore.removeDocsList()
  docStore.docsCount = 0
}

// Query string 정리 함수
const clearQueryString = () => {
  if (Object.keys(route.query).length > 0) {
    router
      .replace({
        name: route.name,
        params: route.params,
        // query를 빈 객체로 설정하여 모든 query string 제거
        query: {},
      })
      .catch(() => {
        // 같은 경로로의 이동에서 발생하는 NavigationDuplicated 에러 무시
      })
  }
}

const comSelect = async (target: number | null, skipClearQuery = false) => {
  // 회사 변경 시 query string 정리 (URL 파라미터로부터 자동 전환하는 경우는 제외)
  if (!skipClearQuery) clearQueryString()

  if (fController.value) fController.value.resetForm(false)

  if (target) {
    // 쿠키 설정 (ContentHeader와 동일한 방식)
    Cookies.set('curr-company', `${target}`)

    // 회사 변경
    await comStore.fetchCompany(target)

    // 슬랙 링크 진입 시 보기 화면에서 목록으로 이동하지 않음
    const isSlackEntry = skipClearQuery && route.name?.includes('보기')
    if (!isSlackEntry && route.name?.includes('보기')) {
      await router.replace({ name: '본사 소송 문서' })
    }

    // 초기화 중이거나 watch가 비활성화된 경우 직접 데이터 로딩
    if (isInitializing.value) {
      await fetchAllSuitCaseList({
        company: target,
        issue_project: comIProject.value,
      })
      await dataSetup(target, route.params?.docsId)
      // ContentHeader 강제 리렌더링으로 CompanySelect 업데이트
      headerKey.value++
    }
  } else {
    dataReset()
    docStore.removeDocsList()
  }
}

onBeforeRouteUpdate(async to => {
  // URL에서 회사 ID 파라미터 확인
  const toCompanyId = to.query.company ? parseInt(to.query.company as string, 10) : null

  if (toCompanyId && toCompanyId !== company.value) await comSelect(toCompanyId, true)
  else await dataSetup(company.value ?? comStore.initComId, to.params?.docsId)
})

const loading = ref(true)
onBeforeMount(async () => {
  // URL에서 회사 ID가 지정되어 있으면 해당 회사로 전환
  let companyId = company.value ?? comStore.initComId

  if (urlCompanyId.value) {
    // 회사 전환 (query string 정리 건너뛰기) 및 문서 로드
    await comSelect(urlCompanyId.value, true)
    // comSelect에서 데이터까지 로딩하므로 추가 작업 불필요
  } else {
    // URL에 회사 파라미터가 없는 경우에만 일반 데이터 설정
    await fetchAllSuitCaseList({
      company: companyId,
      issue_project: comIProject.value,
    })
    await dataSetup(companyId, route.params?.docsId)
  }

  // 초기화 완료 후 watch 활성화
  isInitializing.value = false
  loading.value = false
})

// 다른 라우트로 이동 시 query string 정리
onBeforeRouteLeave(() => {
  clearQueryString()
})
</script>

<template>
  <ComDocsAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :key="headerKey"
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
            :company="company ?? undefined"
            :projects="getAllProjPks"
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
            :sort-name="formTitle"
            ref="refDocsForm"
            :type-num="typeNumber"
            :category-list="categoryList"
            :get-suit-case="getSuitCase"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @on-submit="onSubmit"
            @create-lawsuit="createLawSuit"
          />
        </div>

        <div v-else-if="route.name.includes('수정')">
          <DocsForm
            :sort-name="formTitle"
            ref="refDocsForm"
            :type-num="typeNumber"
            :category-list="categoryList"
            :get-suit-case="getSuitCase"
            :docs="docs as Docs"
            :view-route="mainViewName"
            :write-auth="writeAuth"
            @on-submit="onSubmit"
            @create-lawsuit="createLawSuit"
          />
        </div>
      </CCardBody>
    </ContentBody>
  </ComDocsAuthGuard>
</template>
