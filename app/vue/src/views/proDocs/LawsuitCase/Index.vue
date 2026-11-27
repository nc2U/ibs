<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/proDocs/_menu/headermixin1.ts'
import { useProject } from '@/store/pinia/project.ts'
import { type RouteLocationNormalizedLoaded as LoadedRoute, useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { type SuitCaseFilter as cFilter, useDocs } from '@/store/pinia/docs.ts'
import type { SuitCase } from '@/store/types/docs.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProDocsAuthGuard from '@/components/AuthGuard/ProDocsAuthGuard.vue'
import NoAuth from '@/views/_Accounts/NoAuth.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ListController from '@/components/LawSuitCase/ListController.vue'
import CaseDetail from '@/components/LawSuitCase/CaseDetail.vue'
import CaseList from '@/components/LawSuitCase/CaseList.vue'
import CaseForm from '@/components/LawSuitCase/CaseForm.vue'

const { can, PERM } = usePerms()

const fController = ref<{ resetForm: (isFilter?: boolean) => void } | null>(null)
const mainViewName = ref('소송 사건 관리')
const loading = ref(true)

const createDefaultCaseFilter = (
  companyPk: number | '' = '',
  projectPk: number | '' = '',
): cFilter => ({
  company: companyPk,
  project: projectPk,
  is_real_dev: 'true',
  court: '',
  related_case: '',
  sort: '',
  level: '',
  in_progress: '',
  search: '',
  page: 1,
  limit: '',
})

const caseFilter = ref<cFilter>(createDefaultCaseFilter())

const projStore = useProject()
const project = computed(() => projStore.project?.pk)
const projName = computed(() => projStore.project?.name)
const company = computed(() => projStore.project?.company)
const canDocsRead = computed(() => can(PERM.DOCS_READ))

const docStore = useDocs()
const suitcase = computed(() => docStore.suitcase)
const suitcaseList = computed(() => docStore.suitcaseList)
const getSuitCase = computed(() => docStore.getSuitCase)

const excelFilter = computed(() => {
  const { is_real_dev, sort, level, court, related_case, in_progress, search } = caseFilter.value
  const params = new URLSearchParams({
    company: String(company.value ?? ''),
    project: String(project.value ?? ''),
    is_real_dev: String(is_real_dev || 'true'),
    sort: sort ?? '',
    level: level ?? '',
    court: court ?? '',
    related_case: String(related_case ?? ''),
    in_progress: String(in_progress ?? ''),
    search: search ?? '',
  })
  return params.toString()
})
const excelUrl = computed(() => `/excel/suitcases/?${excelFilter.value}`)

const listFiltering = (payload: cFilter) => {
  caseFilter.value = {
    ...payload,
    company: company.value ?? '',
    project: project.value ?? '',
    is_real_dev: 'true',
    limit: payload.limit || 10,
    page: payload.page || 1,
  }
  if (project.value && canDocsRead.value) {
    docStore.fetchSuitCaseList({ ...caseFilter.value })
  }
}

const pageSelect = (page: number) => {
  caseFilter.value.page = page
  if (project.value && canDocsRead.value) {
    docStore.fetchSuitCaseList({ ...caseFilter.value })
  }
}

const casesRenewal = (page: number) => pageSelect(page)

const linkHit = async (pk: number) => {
  await docStore.hitLink(pk)
}
const fileHit = async (pk: number) => {
  await docStore.hitFile(pk)
}

const [route, router] = [useRoute() as LoadedRoute & { name: string }, useRouter()]

const onSubmit = async (payload: SuitCase & { is_real_dev?: boolean }) => {
  if (!project.value) return
  if (payload.pk) {
    const ok = await docStore.updateSuitCase(payload)
    if (!ok) return
    await router.replace({
      name: `${mainViewName.value} - 보기`,
      params: { caseId: payload.pk },
    })
  } else {
    payload.issue_project = projStore.project?.issue_project ?? null
    payload.is_real_dev = true
    const created = await docStore.createSuitCase(payload)
    if (!created) return
    caseFilter.value.page = 1
    await router.replace({ name: `${mainViewName.value}` })
  }
}

const onDelete = async (pk: number) => {
  const ok = await docStore.deleteSuitCase(pk)
  if (!ok) return
  await router.replace({ name: `${mainViewName.value}` })
}

const agencyFilter = (court: string) => {
  caseFilter.value.page = 1
  caseFilter.value.court = court
  if (project.value && canDocsRead.value) {
    docStore.fetchSuitCaseList({ ...caseFilter.value })
  }
}

const agencySearch = (agent: string) => {
  caseFilter.value.page = 1
  caseFilter.value.search = agent
  if (project.value && canDocsRead.value) {
    docStore.fetchSuitCaseList({ ...caseFilter.value })
  }
}

const relatedFilter = (related: number) => {
  caseFilter.value.page = 1
  caseFilter.value.related_case = related
  if (project.value && canDocsRead.value) {
    docStore.fetchSuitCaseList({ ...caseFilter.value })
  }
}

const dataSetup = async (pk: number, caseId?: string | string[]) => {
  if (!canDocsRead.value) return
  caseFilter.value.company = company.value ?? ''
  caseFilter.value.project = pk
  const tasks: Promise<unknown>[] = [
    docStore.fetchAllSuitCaseList({
      company: company.value ?? '',
      is_real_dev: 'true',
      project: pk,
    }),
    docStore.fetchSuitCaseList({ ...caseFilter.value }),
  ]
  if (caseId) tasks.push(docStore.fetchSuitCase(Number(caseId)))
  await Promise.all(tasks)
}

const dataReset = async (resetRoute = true) => {
  docStore.removeSuitcase()
  docStore.removeSuitcaseList()
  docStore.suitcaseCount = 0
  caseFilter.value = createDefaultCaseFilter(company.value ?? '', project.value ?? '')
  fController.value?.resetForm(false)
  if (resetRoute && route.name !== mainViewName.value) {
    await router.replace({ name: `${mainViewName.value}`, query: route.query })
  }
}

watch(
  project,
  async (newPk, oldPk) => {
    const switched = oldPk !== undefined && newPk !== oldPk
    loading.value = true
    try {
      if (switched) await dataReset(true)
      if (newPk && canDocsRead.value) {
        await dataSetup(newPk, route.params?.caseId)
      } else if (!newPk) {
        await dataReset(false)
      }
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

watch(
  () => route.params.caseId,
  async newId => {
    if (newId && project.value && canDocsRead.value) {
      await docStore.fetchSuitCase(Number(newId))
    } else if (!newId) {
      docStore.removeSuitcase()
    }
  },
)
</script>

<template>
  <ProDocsAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <NoAuth v-if="project && !canDocsRead" />
      <CCardBody v-else class="pb-5">
        <div v-if="route.name === `${mainViewName}`" class="pt-3">
          <ListController
            ref="fController"
            :project="project"
            :case-filter="caseFilter"
            @list-filter="listFiltering"
          />

          <TableTitleRow
            title="소송 사건 관리 목록"
            excel
            :url="excelUrl"
            filename="PR소송_사건내역.xlsx"
            :disabled="!project"
          />

          <CaseList
            :company="company || undefined"
            :limit="caseFilter.limit || 10"
            :page="caseFilter.page || 1"
            :case-list="suitcaseList"
            :view-route="mainViewName"
            @page-select="pageSelect"
            @agency-filter="agencyFilter"
            @agency-search="agencySearch"
            @related-filter="relatedFilter"
          />
        </div>

        <div v-else-if="route.name.includes('보기')">
          <CaseDetail
            v-if="suitcase"
            :suitcase="suitcase"
            :view-route="mainViewName"
            :curr-page="caseFilter.page ?? 1"
            @link-hit="linkHit"
            @file-hit="fileHit"
            @cases-renewal="casesRenewal"
            @post-delete="onDelete"
          />
        </div>

        <div v-else-if="route.name.includes('작성')">
          <CaseForm
            v-if="can(PERM.DOCS_CREATE)"
            :sort-name="projName"
            :get-suit-case="getSuitCase"
            :view-route="mainViewName"
            @on-submit="onSubmit"
          />
          <CAlert v-else color="danger" class="m-3">이 페이지에 접근할 권한이 없습니다.</CAlert>
        </div>

        <div v-else-if="route.name.includes('수정')">
          <CaseForm
            v-if="can(PERM.DOCS_UPDATE)"
            :sort-name="projName"
            :get-suit-case="getSuitCase"
            :suitcase="suitcase ?? undefined"
            :view-route="mainViewName"
            @on-submit="onSubmit"
          />
          <CAlert v-else color="danger" class="m-3">이 페이지에 접근할 권한이 없습니다.</CAlert>
        </div>
      </CCardBody>
    </ContentBody>
  </ProDocsAuthGuard>
</template>
