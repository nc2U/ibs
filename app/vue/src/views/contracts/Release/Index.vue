<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/contracts/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { type Contractor, type ContractRelease } from '@/store/types/contract'
import { useRoute, useRouter } from 'vue-router'
import { write_contract } from '@/utils/pageAuth'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ReleasetButton from '@/views/contracts/Release/components/ReleasetButton.vue'
import ContNavigation from '@/views/contracts/Register/components/ContNavigation.vue'
import ContractorAlert from '@/views/contracts/Register/components/ContractorAlert.vue'
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
const project = computed(() => projStore.project?.pk)

const downloadUrl = computed(() => `/excel/releases/?project=${project.value}`)

const contStore = useContract()
const contractor = computed(() => contStore.contractor)
const contRelease = computed(() => contStore.contRelease)
const contOn = computed(() => contractor.value && contractor.value.status < '3')

const fetchContractor = (contor: number) => contStore.fetchContractor(contor)

const fetchContractorList = (projId: number, search?: string) =>
  contStore.fetchContractorList(projId, search)
const fetchContRelease = (pk: number) => contStore.fetchContRelease(pk)
const fetchContReleaseList = (projId: number, page?: number) =>
  contStore.fetchContReleaseList(projId, page)

const createRelease = (payload: ContractRelease) => contStore.createRelease(payload)
const updateRelease = (payload: ContractRelease & { page: number }) =>
  contStore.updateRelease(payload)

const route = useRoute()
const router = useRouter()

watch(route, val => {
  if (val.query.contractor) {
    fetchContractor(Number(val.query.contractor))
  } else contStore.contractor = null
})

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
    name: '계약 해지 관리',
    query: { contractor },
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
  router.replace({ name: '계약 해지 관리' })
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  await dataSetup(project.value || projStore.initProjId)
  if (route.query.contractor) await fetchContractor(Number(route.query.contractor))
  else {
    contStore.contract = null
    contStore.contractor = null
  }
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
      <ContNavigation :cont-on="!!contOn" />
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
        :disabled="!project"
      />
      <ReleaseList @page-select="pageSelect" @call-form="callForm" @on-submit="onSubmit" />
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
</template>
