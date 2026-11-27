<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router'
import { navMenu, pageTitle } from '@/views/contracts/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { usePerms } from '@/composables/usePerms'
import type { Project } from '@/store/types/project'
import type { Contractor, ContractRelease } from '@/store/types/contract'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContractAuthGuard from '@/components/AuthGuard/ContractAuthGuard.vue'
import ContNavigation from '@/views/contracts/Manage/components/ContNavigation.vue'
import ContractorAlert from '@/views/contracts/Manage/components/ContractorAlert.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ReleaseButton from './components/ReleaseButton.vue'
import ContController from './components/ContController.vue'
import ReleaseList from './components/ReleaseList.vue'
import ReleaseForm, { type ReleaseFormData } from './components/ReleaseForm.vue'

const { can, PERM } = usePerms()
const canContractRelease = computed(() => can(PERM.CONTRACT_RELEASE))

const route = useRoute()
const router = useRouter()
const projStore = useProject()
const contStore = useContract()

const page = ref(1)
const loading = ref(true)

const releaseFormModal = ref<InstanceType<typeof FormModal> | null>(null)
const releaseFormRef = ref<InstanceType<typeof ReleaseForm> | null>(null)
const releaseAlertModal = ref<InstanceType<typeof AlertModal> | null>(null)

// 쿼리/파라미터 안전 파싱 (NaN 방어)
const parseNumber = (val: unknown): number | null => {
  if (!val) return null
  const parsed = parseInt(String(val), 10)
  return Number.isNaN(parsed) ? null : parsed
}

const highlightId = computed(() => parseNumber(route.query.highlight_id))
const urlProjectId = computed(() => parseNumber(route.query.project))
const contractorId = computed(() => parseNumber(route.params.contractorId))
const project = computed<number | null>(() => (projStore.project as Project | null)?.pk ?? null)

const downloadUrl = computed(() =>
  project.value ? `/excel/releases/?project=${project.value}` : '',
)

const contractor = computed<Contractor | null>(() => contStore.contractor)
const contRelease = computed(() => contStore.contRelease)
const contOn = computed(() => !!contractor.value && contractor.value.status < '3')

const isNavigatingForm = ref(false)

// 라우트 contractorId 감시 (중복 fetch 방지)
watch(
  contractorId,
  async newId => {
    if (isNavigatingForm.value) return
    if (newId) {
      await contStore.fetchContractor(newId)
    } else {
      contStore.contractor = null
      contStore.contRelease = null
    }
  },
)

// 계약자 변경 시 해지 정보 동기화
watch(contractor, async val => {
  if (val?.contractorrelease) {
    await contStore.fetchContRelease(val.contractorrelease)
  } else {
    contStore.contRelease = null
  }
})

// 임시 쿼리만 선택적으로 정리 (project 등 영구 파라미터 보존)
const clearTransientQueries = () => {
  if (route.query.page || route.query.highlight_id) {
    const nextQuery = { ...route.query }
    delete nextQuery.page
    delete nextQuery.highlight_id
    router.replace({ query: nextQuery }).catch(() => {})
  }
}

const pageSelect = async (p: number) => {
  clearTransientQueries()
  page.value = p
  if (project.value) {
    await contStore.fetchContReleaseList(project.value, p)
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

const loadHighlightPage = async (highlightIdVal: number, targetProjectId: number) => {
  try {
    const pageNumber = await contStore.findContractorReleasePage(highlightIdVal, targetProjectId)
    if (pageNumber) {
      page.value = pageNumber
      await contStore.fetchContReleaseList(targetProjectId, pageNumber)
      await nextTick()
      scrollToHighlight(highlightIdVal)
    } else {
      await contStore.fetchContReleaseList(targetProjectId)
    }
  } catch (error) {
    console.error('해지 하이라이트 페이지 로드 오류:', error)
    await contStore.fetchContReleaseList(targetProjectId)
  }
}

// 중복 조회 방지 및 데이터 로드 완료 후 모달 즉시 호출
const callForm = async (targetContractorId: number) => {
  isNavigatingForm.value = true
  try {
    await router.replace({
      name: '계약 해지 보기',
      params: { contractorId: targetContractorId },
      query: route.query,
    })

    if (contStore.contractor?.pk !== targetContractorId) {
      await contStore.fetchContractor(targetContractorId)
    } else if (contStore.contractor?.contractorrelease) {
      await contStore.fetchContRelease(contStore.contractor.contractorrelease)
    } else {
      contStore.contRelease = null
    }

    if (canContractRelease.value) {
      releaseFormModal.value?.callModal()
    } else {
      releaseAlertModal.value?.callModal()
    }
  } catch (error) {
    console.error('해지 폼 호출 오류:', error)
  } finally {
    await nextTick()
    isNavigatingForm.value = false
  }
}

const dataSetup = async (pk: number) => {
  if (highlightId.value) {
    await loadHighlightPage(highlightId.value, pk)
  } else {
    await contStore.fetchContReleaseList(pk, page.value)
  }
}

const dataReset = () => {
  contStore.contractor = null
  contStore.contractorList = []
  contStore.contRelease = null
  contStore.contReleaseList = []
  contStore.contReleaseCount = 0
}

const projSelect = async (target: number | null, isAuto = false) => {
  if (!isAuto) clearTransientQueries()
  dataReset()

  if (target) {
    if (isAuto) await projStore.fetchProject(target)
    await dataSetup(target)
  }
}

const onSubmit = async (payload: ReleaseFormData) => {
  if (!project.value || !payload.contractor || !payload.request_date) return

  const releaseData: ContractRelease = {
    pk: payload.pk ?? 0,
    project: project.value,
    contractor: payload.contractor,
    request_date: payload.request_date,
    release_type: payload.release_type,
    status: payload.status,
    refund_amount: payload.refund_amount,
    refund_account_bank: payload.refund_account_bank,
    refund_account_number: payload.refund_account_number,
    refund_account_depositor: payload.refund_account_depositor,
    refund_completion_date: payload.refund_completion_date,
    completion_date: payload.completion_date,
    note: payload.note,
  }

  try {
    if (!payload.pk) {
      await contStore.createRelease(releaseData)
    } else {
      await contStore.updateRelease({ page: page.value, ...releaseData })
    }
    releaseFormModal.value?.close()
  } catch {
    // 에러 안내는 store의 errorHandle에서 처리하며 모달은 유지
  }
}

const onDelete = async (pk: number) => {
  if (!project.value) return
  try {
    await contStore.deleteRelease(pk, project.value, page.value)
    releaseFormModal.value?.close()
  } catch {
    // 에러 안내는 store의 errorHandle에서 처리
  }
}

// 라우트 갱신 감지 (watch(route) 대체)
onBeforeRouteUpdate(async to => {
  const toProjectId = parseNumber(to.query.project)

  if (toProjectId && toProjectId !== project.value) {
    await projSelect(toProjectId, true)
  } else if (to.query.highlight_id && project.value) {
    const toHighlightId = parseNumber(to.query.highlight_id)
    if (toHighlightId) {
      await loadHighlightPage(toHighlightId, project.value)
    }
  }
})

onBeforeMount(async () => {
  const targetProjectId = urlProjectId.value || project.value || projStore.currentProject

  if (targetProjectId) {
    if (project.value !== targetProjectId) {
      await projSelect(targetProjectId, true)
    } else {
      await dataSetup(targetProjectId)
    }

    if (contractorId.value) {
      await contStore.fetchContractor(contractorId.value)
    } else {
      contStore.contractor = null
      contStore.contract = null
    }
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
      @proj-select="projSelect($event, false)"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <ContNavigation :cont-on="!!contOn" :contractor="contractor?.pk" />
        <ContController :project="project ?? undefined" />
        <ContractorAlert v-if="contractor" :contractor="contractor" clear-route="계약 해지 관리" />

        <ReleaseButton
          v-if="canContractRelease && contractor"
          :contractor="contractor"
          :cont-release="contRelease ?? undefined"
          @call-form="callForm"
        />
        <TableTitleRow
          title="계약 해지 현황"
          color="grey"
          excel
          :url="downloadUrl"
          filename="계약_해지현황.xlsx"
          :disabled="!project"
        />
        <ReleaseList
          :highlight-id="highlightId"
          :current-page="page"
          @page-select="pageSelect"
          @call-form="callForm"
        />
      </CCardBody>
    </ContentBody>

    <FormModal ref="releaseFormModal" size="lg" @close="releaseFormRef?.resetForm()">
      <template #header>{{ contRelease ? '계약 해지 수정' : '계약 해지 등록' }}</template>
      <template #default>
        <ReleaseForm
          ref="releaseFormRef"
          :release="contRelease ?? undefined"
          :contractor="contractor"
          @on-submit="onSubmit"
          @on-delete="onDelete"
          @close="releaseFormModal?.close()"
        />
      </template>
    </FormModal>

    <AlertModal ref="releaseAlertModal" />
  </ContractAuthGuard>
</template>
