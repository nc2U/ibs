<script lang="ts" setup>
import { ref, computed, onBeforeMount, nextTick } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin2'
import { numFormat } from '@/utils/baseMixins'
import { useProject } from '@/store/pinia/project'
import { useSite, type OwnerFilter } from '@/store/pinia/project_site'
import { write_project_site } from '@/utils/pageAuth'
import type { Project, Relation, SiteOwner } from '@/store/types/project'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import ListController from '@/views/projects/SiteOwner/components/ListController.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import AddSiteOwner from '@/views/projects/SiteOwner/components/AddSiteOwner.vue'
import SiteOwnerList from '@/views/projects/SiteOwner/components/SiteOwnerList.vue'

const route = useRoute()
const router = useRouter()
const listControl = ref()

// URL에서 highlight_id 파라미터 읽기
const highlightId = computed(() => {
  const id = route.query.highlight_id
  return id ? parseInt(id as string, 10) : null
})

// URL에서 project 파라미터 읽기
const urlProjectId = computed(() => {
  const id = route.query.project
  return id ? parseInt(id as string, 10) : null
})

const dataFilter = ref<OwnerFilter>({
  project: null,
  limit: '',
  page: 1,
  sort: '',
  is_use_consent: '',
  search: '',
})

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)
const isReturned = computed(() => (projStore.project as Project)?.is_returned_area)

const siteStore = useSite()
const getOwnersTotal = computed(() => siteStore.getOwnersTotal?.owned_area)

// Store 함수들
const findSiteOwnerPage = (highlightId: number, filters: OwnerFilter) =>
  siteStore.findSiteOwnerPage(highlightId, filters)
const fetchSiteOwnerList = (payload: OwnerFilter) => siteStore.fetchSiteOwnerList(payload)

const excelUrl = computed(() => {
  const url = `/excel/sites-by-owner/?project=${project.value}`
  const filter = dataFilter.value
  let queryStr = filter.sort ? `&own_sort=${filter.sort}` : ''
  queryStr = filter.search ? `${queryStr}&search=${filter.search}` : queryStr
  return `${url}${queryStr}`
})

const listFiltering = (payload: OwnerFilter) => {
  // 필터링 시 query string 정리
  clearQueryString()
  payload.project = project.value as number
  dataFilter.value = payload
  if (project.value) siteStore.fetchSiteOwnerList(payload)
}

const pageSelect = (page: number) => {
  // 페이지 변경 시 query string 정리
  clearQueryString()
  dataFilter.value.project = project.value as number
  dataFilter.value.page = page
  if (project.value) siteStore.fetchSiteOwnerList(dataFilter.value)
}

// 하이라이트 기능
const scrollToHighlight = async () => {
  if (highlightId.value) {
    await nextTick()
    const element = document.querySelector(`[data-site-owner-id="${highlightId.value}"]`)
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
          sort: dataFilter.value.sort || '',
          is_use_consent: dataFilter.value.is_use_consent || '',
          search: dataFilter.value.search || '',
        }
        await siteStore.fetchSiteOwnerList({ project: projectId, page: targetPage })
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

type inputData = SiteOwner & {
  limit: number
  page: number
  sort: string
  use_consent: '' | '0' | '1'
  search: string
}

const onCreate = (payload: inputData) => siteStore.createSiteOwner(payload)

const onUpdate = (payload: inputData) => siteStore.updateSiteOwner(payload)

const relationPatch = (payload: Relation) => {
  const { page, sort, is_use_consent, search } = dataFilter.value
  if (project.value) {
    const data = { project: project.value, page, sort, is_use_consent, search, ...payload }
    siteStore.patchRelation(data)
  }
}

const multiSubmit = (payload: SiteOwner) => {
  const { limit, page, sort, is_use_consent, search } = dataFilter.value
  const submitData = { ...payload, limit, page, sort, is_use_consent, search } as inputData
  if (payload.pk) onUpdate(submitData)
  else onCreate(submitData)
}

const onDelete = (payload: { pk: number; project: number }) => {
  const { pk, project } = payload
  siteStore.deleteSiteOwner(pk, project)
}

const dataSetup = (pk: number) => siteStore.fetchSiteOwnerList({ project: pk })

const dataReset = () => {
  siteStore.siteOwnerList = []
  siteStore.siteOwnerCount = 0
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

// 다른 라우트로 이동 시 query string 정리
onBeforeRouteLeave(() => {
  clearQueryString()
})

const loading = ref(true)
onBeforeMount(async () => {
  // URL에서 프로젝트 ID가 지정되어 있으면 해당 프로젝트 사용
  let projectId = urlProjectId.value || project.value || projStore.initProjId
  if (urlProjectId.value && urlProjectId.value !== project.value) {
    console.log(`Using project ${urlProjectId.value} from URL parameter`)
    projectId = urlProjectId.value
  }

  siteStore.fetchAllSites(projectId)

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
          @list-filtering="listFiltering"
        />
        <AddSiteOwner
          v-if="write_project_site"
          :project="project as number"
          @multi-submit="multiSubmit"
        />
        <TableTitleRow title="부지 소유자 목록" excel :url="excelUrl" :disabled="!project">
          <span v-if="project" class="text-success" style="padding-top: 7px">
            소유자 면적 :
            {{ numFormat(getOwnersTotal as number, 2) }}m<sup>2</sup> ({{
              numFormat((getOwnersTotal as number) * 0.3025, 2)
            }}평) 등록
          </span>
        </TableTitleRow>
        <SiteOwnerList
          :is-returned="isReturned"
          :limit="dataFilter.limit || 10"
          :highlight-id="highlightId || undefined"
          :current-page="dataFilter.page"
          @page-select="pageSelect"
          @relation-patch="relationPatch"
          @multi-submit="multiSubmit"
          @on-delete="onDelete"
        />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
