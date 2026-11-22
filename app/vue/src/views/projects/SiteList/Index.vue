<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { navMenu, pageTitle } from '@/views/projects/_menu/headermixin2'
import { useProject } from '@/store/pinia/project'
import { usePerms } from '@/composables/usePerms'
import { numFormat } from '@/utils/baseMixins'
import { type SiteFilter, useSite } from '@/store/pinia/project_site'
import type { Project, Site } from '@/store/types/project'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import ListController from './components/ListController.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import AddSite from './components/AddSite.vue'
import SiteList from './components/SiteList.vue'

const { can, PERM } = usePerms()
const canSiteRead = computed(() => can(PERM.SITE_READ))
const canSiteCreate = computed(() => can(PERM.SITE_CREATE))

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
const totalIncorporatedArea = computed(() => getSitesTotal.value?.incorporated ?? totalArea.value)

const rights = ref(false)
const excelUrl = computed(
  () =>
    `/excel/sites/?project=${project.value}&search=${dataFilter.value.search}&rights=${rights.value || ''}`,
)

const listFiltering = (payload: SiteFilter) => {
  clearQueryString()
  payload.project = project.value as number
  dataFilter.value = payload
  if (project.value) siteStore.fetchSiteList(payload)
}

const pageSelect = (page: number) => {
  clearQueryString()
  dataFilter.value.page = page
  if (project.value) {
    siteStore.fetchSiteList({
      ...dataFilter.value,
      project: project.value,
      page,
    })
  }
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
    if (value !== null && value !== undefined && value !== '') form.set(key, value)
    else if (key === 'incorporated_area') form.set(key, '')
  }

  const submitData = { form, page, search }

  if (pk) onUpdate(pk, submitData)
  else onCreate(submitData)
}

const onDelete = (payload: { pk: number; project: number }) => {
  const { pk, project: projId } = payload
  siteStore.deleteSite(pk, projId)
}

const dataSetup = (pk: number) => {
  dataFilter.value.project = pk
  siteStore.fetchSiteList(dataFilter.value)
}

const dataReset = () => {
  siteStore.siteList = []
  siteStore.siteCount = 0
}

const projSelect = (target: number | null) => {
  clearQueryString()
  dataReset()
  if (target) dataSetup(target)
}

// Query string 정리 함수
const clearQueryString = () => {
  if (route.query.page || route.query.highlight_id) {
    router
      .replace({
        name: route.name,
        params: route.params,
        query: {},
      })
      .catch(() => {
        // 동일 경로 이동 NavigationDuplicated 에러 무시
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
      const pageParam = route.query.page
      if (pageParam) {
        const targetPage = parseInt(pageParam as string, 10)
        dataFilter.value = {
          project: projectId,
          limit: dataFilter.value.limit || '',
          page: targetPage,
          search: dataFilter.value.search || '',
        }
        siteStore.fetchSiteList({ project: projectId, page: targetPage })
      } else {
        dataSetup(projectId)
      }
    } catch (error) {
      console.error('Error loading highlight page:', error)
      dataSetup(projectId)
    }
  }
}

watch(
  () => project.value,
  newVal => {
    clearQueryString()
    dataReset()
    if (newVal) dataSetup(newVal)
  },
)

onBeforeRouteLeave(() => {
  clearQueryString()
})

const loading = ref(true)
onBeforeMount(async () => {
  if (canSiteRead.value) {
    let projectId = urlProjectId.value || project.value || projStore.currentProject
    if (projectId) {
      if (urlProjectId.value && urlProjectId.value !== project.value) projectId = urlProjectId.value

      if (highlightId.value) {
        await loadHighlightPage(projectId)
        await scrollToHighlight()
      } else {
        dataSetup(projectId)
      }
    }
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
          :project="project ?? undefined"
          @list-filtering="listFiltering"
        />
        <AddSite v-if="canSiteCreate" :project="project ?? undefined" @multi-submit="multiSubmit" />
        <TableTitleRow
          title="사업 부지 목록"
          excel
          :url="excelUrl"
          filename="사업_부지목록.xlsx"
          :disabled="!project"
        >
          <span v-if="project" class="text-success" style="padding-top: 7px">
            전체 면적 : {{ numFormat(totalArea || 0, 2) }}m<sup>2</sup> ({{
              numFormat((totalArea || 0) * 0.3025, 2)
            }}
            평) /
            <strong class="text-primary">
              편입 면적 : {{ numFormat(totalIncorporatedArea || 0, 2) }}m<sup>2</sup> ({{
                numFormat((totalIncorporatedArea || 0) * 0.3025, 2)
              }}
              평)
            </strong>
          </span>
          <span style="padding-top: 7px">
            <CFormCheck
              id="include-rights"
              v-model="rights"
              label="권리제한사항 포함"
              class="ml-3"
            />
          </span>
        </TableTitleRow>
        <SiteList
          :is-returned="isReturned"
          :limit="Number(dataFilter.limit) || 10"
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
