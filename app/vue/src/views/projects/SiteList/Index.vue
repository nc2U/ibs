<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, nextTick } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin2'
import { useProject } from '@/store/pinia/project'
import { useSite, type SiteFilter } from '@/store/pinia/project_site'
import type { Project, Site } from '@/store/types/project'
import { numFormat } from '@/utils/baseMixins'
import { write_project_site } from '@/utils/pageAuth'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import ListController from './components/ListController.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import AddSite from './components/AddSite.vue'
import SiteList from './components/SiteList.vue'

const route = useRoute()
const router = useRouter()
const listControl = ref()

const highlightId = computed(() => {
  const id = route.query.highlight_id
  return id ? parseInt(id as string, 10) : null
})

// URL에서 project 파라미터 읽기
const urlProjectId = computed(() => {
  const id = route.query.project
  return id ? parseInt(id as string, 10) : null
})

const dataFilter = ref<SiteFilter>({
  project: null,
  limit: '',
  page: 1,
  search: '',
})

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)
const isReturned = computed(() => (projStore.project as Project)?.is_returned_area)

const siteStore = useSite()
const getSitesTotal = computed(() => siteStore.getSitesTotal)
const totalArea = computed(() =>
  isReturned.value ? getSitesTotal.value?.returned : getSitesTotal.value?.official,
)

const rights = ref(false)
const excelUrl = computed(
  () =>
    `/excel/sites/?project=${project.value}&search=${dataFilter.value.search}&rights=${rights.value || ''}`,
)

const listFiltering = (payload: SiteFilter) => {
  // 필터링 시 query string 정리
  clearQueryString()
  payload.project = project.value as number
  dataFilter.value = payload
  if (project.value) siteStore.fetchSiteList(payload)
}

const pageSelect = (page: number) => {
  // 페이지 변경 시 query string 정리
  clearQueryString()
  dataFilter.value.page = page
  if (project.value) siteStore.fetchSiteList({ project: project.value, page })
  listControl.value.listFiltering(page)
}

const onCreate = (payload: { form: FormData; page?: number; search?: string }) =>
  siteStore.createSite(payload)

const onUpdate = (pk: number, payload: { form: FormData; page?: number; search?: string }) =>
  siteStore.updateSite(pk, payload)

const multiSubmit = (payload: Site) => {
  const { page, search } = dataFilter.value
  const { pk, ...data } = payload as { [key: string]: any }

  const form = new FormData()
  for (const key in data) {
    const value = data[key]

    // null, undefined, 빈 문자열은 제외 (숫자 필드 오류 방지 목적)
    if (value !== null && value !== undefined && value !== '') form.set(key, value)
  }

  const submitData = { form, page, search }

  if (pk) onUpdate(pk, submitData)
  else onCreate(submitData)
}

const onDelete = (payload: { pk: number; project: number }) => {
  const { pk, project } = payload
  siteStore.deleteSite(pk, project)
}

const dataSetup = (pk: number) => siteStore.fetchSiteList({ project: pk })

const dataReset = () => {
  siteStore.siteList = []
  siteStore.siteCount = 0
}

const projSelect = (target: number | null) => {
  // 프로젝트 변경 시 query string 정리
  clearQueryString()
  dataReset()
  if (!!target) dataSetup(target)
}

// Query string 정리 함수
const clearQueryString = () => {
  if (route.query.page || route.query.highlight_id) {
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

// 하이라이트 스크롤 함수
const scrollToHighlight = async () => {
  if (highlightId.value) {
    await nextTick()
    const element = document.querySelector(`[data-site-id="${highlightId.value}"]`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }
}

// 하이라이트 페이지 로드 함수
const loadHighlightPage = async (projectId: number) => {
  if (highlightId.value && projectId) {
    try {
      // URL의 page 파라미터가 있으면 해당 페이지로 이동
      const pageParam = route.query.page
      if (pageParam) {
        const targetPage = parseInt(pageParam as string, 10)
        dataFilter.value = {
          project: projectId,
          limit: dataFilter.value.limit || '',
          page: targetPage,
          search: dataFilter.value.search || '',
        }
        await siteStore.fetchSiteList({ project: projectId, page: targetPage })
      } else {
        // page 파라미터가 없으면 기본 첫 페이지
        await dataSetup(projectId)
      }
    } catch (error) {
      console.error('Error loading highlight page:', error)
      // 오류 발생시 기본 첫 페이지 로드
      await dataSetup(projectId)
    }
  }
}

// 다른 라우트로 이동 시 query string 정리
onBeforeRouteLeave(() => {
  clearQueryString()
})

const loading = ref(true)
onBeforeMount(async () => {
  // URL에서 프로젝트 ID가 지정되어 있으면 해당 프로젝트 사용
  let projectId = urlProjectId.value || project.value || projStore.initProjId
  if (urlProjectId.value && urlProjectId.value !== project.value) projectId = urlProjectId.value

  // 하이라이트 항목이 있으면 해당 페이지로 이동 후 스크롤
  if (highlightId.value) {
    await loadHighlightPage(projectId)
    await scrollToHighlight()
  } else {
    await dataSetup(projectId)
  }
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <ListController
          ref="listControl"
          :project="project as number"
          :is-returned="isReturned"
          @list-filtering="listFiltering"
        />
        <AddSite
          v-if="write_project_site"
          :project="project as number"
          @multi-submit="multiSubmit"
        />
        <TableTitleRow title="사업 부지 목록" excel :url="excelUrl" filename="사업_부지목록.xlsx" :disabled="!project">
          <span v-if="project" class="text-success" style="padding-top: 7px">
            총 면적 : {{ numFormat(totalArea as number, 2) }}m<sup>2</sup> ({{
              numFormat((totalArea as number) * 0.3025, 2)
            }}
            평) 등록
          </span>
          <span style="padding-top: 7px">
            <CFormCheck
              v-model="rights"
              id="include-rights"
              label="권리제한사항 포함"
              class="ml-3"
            />
          </span>
        </TableTitleRow>
        <SiteList
          :is-returned="isReturned"
          :limit="dataFilter.limit || 10"
          :highlight-id="highlightId || undefined"
          :current-page="dataFilter.page"
          @page-select="pageSelect"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
