<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/contracts/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import type { Project } from '@/store/types/project.ts'
import { type Contractor, type ContractRelease } from '@/store/types/contract'
import { useRoute, useRouter } from 'vue-router'
import { write_contract } from '@/utils/pageAuth'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContractAuthGuard from '@/components/AuthGuard/ContractAuthGuard.vue'
import ReleasetButton from '@/views/contracts/Release/components/ReleasetButton.vue'
import ContNavigation from '@/views/contracts/Manage/components/ContNavigation.vue'
import ContractorAlert from '@/views/contracts/Manage/components/ContractorAlert.vue'
import ContController from '@/views/contracts/Release/components/ContController.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ReleaseList from '@/views/contracts/Release/components/ReleaseList.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ReleaseForm from '@/views/contracts/Release/components/ReleaseForm.vue'

const page = ref(1)

const releaseFormModal = ref()
const releaseAlertModal = ref()

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const highlightId = computed(() => {
  const id = route.query.highlight_id
  return id ? parseInt(id as string, 10) : null
})

const downloadUrl = computed(() => `/excel/releases/?project=${project.value}`)

const contStore = useContract()
const contractor = computed<Contractor | null>(() => contStore.contractor)
const contRelease = computed(() => contStore.contRelease)
const contOn = computed(() => contractor.value && contractor.value.status < '3')

const fetchContractor = (contor: number) => contStore.fetchContractor(contor)

const fetchContractorList = (projId: number, search?: string) =>
  contStore.fetchContractorList(projId, search)
const fetchContRelease = (pk: number) => contStore.fetchContRelease(pk)
const fetchContReleaseList = (projId: number, page?: number) =>
  contStore.fetchContReleaseList(projId, page)
const findContractorReleasePage = (id: number, projId: number) =>
  contStore.findContractorReleasePage(id, projId)

const createRelease = (payload: ContractRelease) => contStore.createRelease(payload)
const updateRelease = (payload: ContractRelease & { page: number }) =>
  contStore.updateRelease(payload)

const route = useRoute()
const router = useRouter()

watch(
  () => route.params.contractorId,
  contractorId => {
    if (contractorId) {
      fetchContractor(Number(contractorId))
    } else contStore.contractor = null
  },
)

watch(contractor, val => {
  if (val?.contractorrelease) fetchContRelease(val.contractorrelease)
  else contStore.contRelease = null
})

const searchContractor = (search: string) => {
  if (search !== '' && project.value) {
    fetchContractorList(project.value, search)
  } else contStore.contractorList = []
}

const pageSelect = (p: number) => {
  page.value = p
  if (project.value) fetchContReleaseList(project.value, p)
}

const onSubmit = (payload: ContractRelease) => {
  if (project.value) payload.project = project.value
  if (!payload.pk) createRelease({ ...payload })
  else updateRelease({ page: page.value, ...payload })
  releaseFormModal.value.close()
}

const callForm = (contractor: number) => {
  router.replace({
    name: '계약 해지 보기',
    params: {
      contractorId: contractor,
    },
    query: route.query,
  })

  setTimeout(() => {
    if (write_contract.value) releaseFormModal.value.callModal()
    else releaseAlertModal.value.callModal()
  }, 500)
}

const dataSetup = (pk: number) => fetchContReleaseList(pk)

const dataReset = () => {
  contStore.contractor = null
  contStore.contractorList = []
  contStore.contRelease = null
  contStore.contReleaseList = []
  contStore.contReleaseCount = 0
}

const projSelect = (target: number | null) => {
  // 프로젝트 변경 시에는 하이라이트 관련 쿼리 파라미터 모두 제거
  router.replace({
    name: '계약 해지 관리',
    query: {},
  })
  dataReset()
  if (!!target) dataSetup(target)
}

const loadHighlightPage = async (highlightId: number, targetProjectId: number) => {
  try {
    // URL에서 전달된 targetProjectId를 우선적으로 사용 (슬랙 링크 등에서 온 정확한 프로젝트 ID)
    const projectIdToUse = targetProjectId || project.value || 1
    const pageNumber = await findContractorReleasePage(highlightId, projectIdToUse)

    if (pageNumber) {
      page.value = pageNumber
      await fetchContReleaseList(projectIdToUse, pageNumber)
      await nextTick()
      scrollToHighlight(highlightId)
    } else {
      await dataSetup(projectIdToUse)
    }
  } catch (error) {
    console.error('Failed to load highlight page:', error)
    // 오류 발생 시 기본 데이터 로드
    const fallbackProjectId = targetProjectId || project.value || 1
    await dataSetup(fallbackProjectId)
  }
}

const scrollToHighlight = (id: number) => {
  setTimeout(() => {
    const element = document.querySelector(`[data-release-id="${id}"]`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, 100)
}

const loading = ref(true)
onBeforeMount(async () => {
  // URL에서 project 파라미터 읽기 (슬랙 링크 등에서 전달된 정확한 프로젝트)
  const urlProjectId = route.query.project ? parseInt(route.query.project as string, 10) : null
  const projectId = urlProjectId || project.value || projStore.initProjId || 1

  // 하이라이트 ID가 있는 경우 해당 페이지로 이동, 없으면 일반 데이터 로딩
  if (highlightId.value && projectId) {
    await loadHighlightPage(highlightId.value, projectId)
  } else {
    await dataSetup(projectId)
  }

  if (route.params.contractorId) await fetchContractor(Number(route.params.contractorId))
  else {
    contStore.contract = null
    contStore.contractor = null
  }

  loading.value = false
})

// URL이 변경될 때 하이라이트 처리
watch(route, async newRoute => {
  if (newRoute.params.contractorId) await fetchContractor(Number(newRoute.params.contractorId))
  else contStore.contractor = null

  // 하이라이트 ID 처리 (프로젝트 변경은 ProjectSelect에서 처리)
  if (newRoute.query.highlight_id && project.value) {
    const newHighlightId = parseInt(newRoute.query.highlight_id as string, 10)
    await loadHighlightPage(newHighlightId, project.value)
  }
})
</script>

<template>
  <ContractAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <ContNavigation :cont-on="!!contOn" :contractor="contractor?.pk" />
        <ContController
          :project="project || undefined"
          @search-contractor="searchContractor"
          @call-form="callForm"
        />
        <ContractorAlert v-if="contractor" :contractor="contractor" />

        <ReleasetButton
          v-if="contractor"
          :contractor="contractor"
          :cont-release="contRelease ?? undefined"
          @call-form="callForm"
        />
        <TableTitleRow
          title="계약 해지 현황"
          color="grey"
          excel
          :url="downloadUrl"
          filename="계약_해지현황"
          :disabled="!project"
        />
        <ReleaseList
          :highlight-id="highlightId"
          :current-page="page"
          @page-select="pageSelect"
          @call-form="callForm"
          @on-submit="onSubmit"
        />
      </CCardBody>
    </ContentBody>

    <FormModal ref="releaseFormModal" size="lg">
      <template #header>계약 해지 수정 등록</template>
      <template #default>
        <ReleaseForm
          :release="contRelease ?? undefined"
          :contractor="contractor as Contractor"
          @on-submit="onSubmit"
          @close="releaseFormModal.close()"
        />
      </template>
    </FormModal>

    <AlertModal ref="releaseAlertModal" />
  </ContractAuthGuard>
</template>
