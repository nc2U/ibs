<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch, nextTick } from 'vue'
import { navMenu, pageTitle } from '@/views/contracts/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { useRoute, useRouter, onBeforeRouteUpdate, onBeforeRouteLeave } from 'vue-router'
import { write_contract } from '@/utils/pageAuth'
import type { BuyerForm, Contractor, Succession } from '@/store/types/contract'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContractAuthGuard from '@/components/AuthGuard/ContractAuthGuard.vue'
import ContNavigation from '@/views/contracts/Manage/components/ContNavigation.vue'
import ContractorAlert from '@/views/contracts/Manage/components/ContractorAlert.vue'
import ContController from './components/ContController.vue'
import SuccessionButton from './components/SuccessionButton.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import SuccessionList from './components/SuccessionList.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import SuccessionForm from '@/views/contracts/Succession/components/SuccessionForm.vue'

const page = ref(1)

const successionFormModal = ref()
const successionAlertModal = ref()

const projStore = useProject()
const project = computed(() => (projStore.project as any)?.pk)

const highlightId = computed(() => {
  const id = route.query.highlight_id
  return id ? parseInt(id as string, 10) : null
})

// URL에서 project 파라미터 읽기
const urlProjectId = computed(() => {
  const id = route.query.project
  return id ? parseInt(id as string, 10) : null
})

const downloadUrl = computed(() => `/excel/successions/?project=${project.value}`)

const contStore = useContract()
const contractor = computed<Contractor | null>(() => contStore.contractor)
const contOn = computed(() => contractor.value && contractor.value.status < '3')
const succession = computed<Succession | null>(() => contStore.succession)
const isSuccession = computed(() => !!succession.value && !succession.value.is_approval)

const fetchContract = (cont: number) => contStore.fetchContract(cont)
const fetchContractor = (contor: number) => contStore.fetchContractor(contor)
const fetchContractorList = (projId: number, search?: string) =>
  contStore.fetchContractorList(projId, search)

const fetchSuccession = (pk: number) => contStore.fetchSuccession(pk)
const fetchSuccessionList = (projId: number, page?: number) =>
  contStore.fetchSuccessionList(projId, page)

const findSuccessionPage = (highlightId: number, projectId: number) =>
  contStore.findSuccessionPage(highlightId, projectId)

const createSuccession = (payload: Succession & BuyerForm & { project: number; page: number }) =>
  contStore.createSuccession(payload)

const patchSuccession = (payload: Succession & BuyerForm & { project: number; page: number }) =>
  contStore.patchSuccession(payload)

const route = useRoute()
watch(
  () => route.params.contractorId,
  contractorId => {
    if (contractorId) fetchContractor(Number(contractorId))
    else {
      contStore.contract = null
      contStore.contractor = null
    }
  },
)

watch(contractor, val => {
  if (val?.contract) fetchContract(val.contract)
  if (val?.succession) fetchSuccession(val.succession?.pk as number)
  else {
    contStore.contract = null
    contStore.succession = null
  }
})

const router = useRouter()

const searchContractor = (search: string) => {
  if (search !== '' && project.value) {
    fetchContractorList(project.value, search)
  } else contStore.contractorList = []
}

const pageSelect = (p: number) => {
  // 하이라이팅 기능이 활성화된 경우 highlight_id 보존
  if (highlightId.value) {
    router
      .replace({
        name: route.name,
        params: route.params,
        query: { highlight_id: route.query.highlight_id },
      })
      .catch(() => {})
  } else {
    // 일반적인 경우는 query string 정리
    clearQueryString()
  }

  page.value = p
  if (project.value) fetchSuccessionList(project.value, p)
}

const scrollToHighlight = async () => {
  if (highlightId.value) {
    await nextTick()
    const element = document.querySelector(`[data-succession-id="${highlightId.value}"]`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }
}

const loadHighlightPage = async (projectId: number) => {
  if (highlightId.value && projectId) {
    try {
      const targetPage = await findSuccessionPage(highlightId.value, projectId)

      // 해당 페이지로 이동
      page.value = targetPage
      await fetchSuccessionList(projectId, targetPage)
    } catch (error) {
      console.error('Error finding succession highlight page:', error)
      // 오류 발생시 기본 첫 페이지 로드
      await fetchSuccessionList(projectId, 1)
    }
  }
}

const callFormModal = () => {
  if (write_contract.value) successionFormModal.value.callModal()
  else successionAlertModal.value.callModal()
}

const doneAlert = () =>
  successionAlertModal.value.callModal(
    '',
    '승계 완료된 건 입니다. 신규 승계 건을 등록하려면 해당 계약자를 선택하십시요.',
  )

const onSubmit = (payload: { s_data: Succession; b_data: BuyerForm }) => {
  const { s_data, b_data } = payload
  const dbData = { ...s_data, ...b_data }

  if (!isSuccession.value && !s_data.pk) {
    createSuccession({ ...dbData, project: project.value as number, page: 1 })
    router.push({ name: '권리 의무 승계 보기', params: { contractorId: s_data.seller.pk } })
  } else
    patchSuccession({
      ...dbData,
      project: project.value as number,
      page: page.value,
    })
  successionFormModal.value.close()
}

const dataSetup = async (pk: number) => {
  // 하이라이트 항목이 있으면 해당 페이지로 이동 후 스크롤
  if (highlightId.value) {
    await loadHighlightPage(pk)
  } else {
    await fetchSuccessionList(pk)
  }

  await scrollToHighlight()
}

const dataReset = () => {
  contStore.contract = null
  contStore.contractor = null
  contStore.contractorList = []
  contStore.successionList = []
}

const projSelect = async (target: number | null, skipClearQuery = false) => {
  // 프로젝트 변경 시 query string 정리 (URL 파라미터로부터 자동 전환하는 경우는 제외)
  if (!skipClearQuery) {
    // 수동 프로젝트 변경 시에는 하이라이트 관련 쿼리 파라미터 모두 제거
    clearQueryString(false)
  }

  dataReset()
  if (!!target) {
    await projStore.fetchProject(target)

    if (!skipClearQuery) {
      // 수동 선택 시에는 하이라이트 없이 일반 목록만 로드
      await fetchSuccessionList(target)
    } else {
      // 슬랙 링크 등 자동 전환 시에만 하이라이트 기능 사용
      await dataSetup(target)
    }
  }
}

// Query string 정리 함수 (하이라이팅 기능 중에는 highlight_id 보존)
const clearQueryString = (preserveHighlight = false) => {
  if (
    route.query.page ||
    route.query.highlight_id ||
    route.query.contractor ||
    route.query.project
  ) {
    const queryToKeep =
      preserveHighlight && route.query.highlight_id
        ? { highlight_id: route.query.highlight_id }
        : {}

    router
      .replace({
        name: route.name,
        params: route.params,
        query: queryToKeep,
      })
      .catch(() => {
        // NavigationDuplicated 에러 무시
      })
  }
}

// Route 처리
onBeforeRouteUpdate(async to => {
  // URL에서 프로젝트 ID 파라미터 확인
  const toProjectId = to.query.project ? parseInt(to.query.project as string, 10) : null

  if (toProjectId && toProjectId !== project.value?.pk) {
    await projSelect(toProjectId, true)
  } else {
    // URL에 highlight_id가 있으면 하이라이트 기능이 필요한 경우이므로 dataSetup 실행
    if (to.query.highlight_id) {
      await dataSetup(project.value?.pk || projStore.initProjId)
    }
  }
})

// 다른 라우트로 이동 시 query string 정리
onBeforeRouteLeave(to => {
  // contracts 내부 이동이 아닌 경우에만 쿼리 정리
  if (!to.path.startsWith('/contracts')) {
    clearQueryString()
  }
})

const loading = ref(true)
onBeforeMount(async () => {
  // URL에서 프로젝트 ID가 지정되어 있으면 해당 프로젝트로 전환
  let projectId = project.value?.pk || projStore.initProjId

  if (urlProjectId.value && urlProjectId.value !== projectId) {
    // 프로젝트 전환 (query string 정리 건너뛰기)
    await projSelect(urlProjectId.value, true)
  } else {
    // contractor 파라미터가 있으면 contractor 설정
    if (route.params.contractorId) await fetchContractor(Number(route.params.contractorId))
    else contStore.contractor = null

    // URL에 프로젝트 파라미터가 없거나 같은 경우 일반 데이터 설정
    await dataSetup(projectId)
  }

  loading.value = false
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
        <ContController :project="project || undefined" @search-contractor="searchContractor" />
        <ContractorAlert v-if="contractor" :contractor="contractor" />

        <SuccessionButton
          v-if="contractor"
          :is-succession="isSuccession"
          @call-form="callFormModal"
        />
        <TableTitleRow title="승계 진행 건 목록" excel :url="downloadUrl" filename="승계_진행건_목록" :disabled="!project" />
        <SuccessionList
          :highlight-id="highlightId ?? undefined"
          :current-page="page"
          @page-select="pageSelect"
          @call-form="callFormModal"
          @done-alert="doneAlert"
        />
      </CCardBody>
    </ContentBody>

    <FormModal ref="successionFormModal" size="lg">
      <template #header>권리 의무 승계 수정 등록</template>
      <template #default>
        <SuccessionForm
          :succession="succession ?? undefined"
          :is-succession="isSuccession"
          @on-submit="onSubmit"
          @close="successionFormModal.close()"
        />
      </template>
    </FormModal>

    <AlertModal ref="successionAlertModal" />
  </ContractAuthGuard>
</template>
