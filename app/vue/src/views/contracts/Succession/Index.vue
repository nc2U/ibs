<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/contracts/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { useRoute, useRouter } from 'vue-router'
import { write_contract } from '@/utils/pageAuth'
import type { BuyerForm, Contractor, Succession } from '@/store/types/contract'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContNavigation from '@/views/contracts/Register/components/ContNavigation.vue'
import ContractorAlert from '@/views/contracts/Register/components/ContractorAlert.vue'
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

const downloadUrl = computed(() => `/excel/successions/?project=${project.value}`)

const contStore = useContract()
const contractor = computed<Contractor | null>(() => contStore.contractor)
const succession = computed<Succession | null>(() => contStore.succession)
const isSuccession = computed(() => !!succession.value && !succession.value.is_approval)

const fetchContract = (cont: number) => contStore.fetchContract(cont)
const fetchContractor = (contor: number) => contStore.fetchContractor(contor)
const fetchContractorList = (projId: number, search?: string) =>
  contStore.fetchContractorList(projId, search)

const fetchSuccession = (pk: number) => contStore.fetchSuccession(pk)
const fetchSuccessionList = (projId: number, page?: number) =>
  contStore.fetchSuccessionList(projId, page)

const createSuccession = (payload: Succession & BuyerForm & { project: number; page: number }) =>
  contStore.createSuccession(payload)

const patchSuccession = (payload: Succession & BuyerForm & { project: number; page: number }) =>
  contStore.patchSuccession(payload)

const route = useRoute()
watch(route, val => {
  if (val.query.contractor) fetchContractor(Number(val.query.contractor))
  else {
    contStore.contract = null
    contStore.contractor = null
  }
})

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
  page.value = p
  if (project.value) fetchSuccessionList(project.value, p)
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
    router.push({ name: '권리 의무 승계', query: { contractor: s_data.seller.pk } })
  } else
    patchSuccession({
      ...dbData,
      project: project.value as number,
      page: page.value,
    })
  successionFormModal.value.close()
}

const dataSetup = (pk: number) => fetchSuccessionList(pk)

const dataReset = () => {
  contStore.contract = null
  contStore.contractor = null
  contStore.contractorList = []
  contStore.successionList = []
}

const projSelect = (target: number | null) => {
  router.replace({ name: '권리 의무 승계' })
  dataReset()
  if (!!target) dataSetup(target)
}

onBeforeMount(() => {
  if (route.query.contractor) fetchContractor(Number(route.query.contractor))
  else contStore.contractor = null
  dataSetup(project.value || projStore.initProjId)
})
</script>

<template>
  <ContentHeader
    :page-title="pageTitle"
    :nav-menu="navMenu"
    selector="ProjectSelect"
    @proj-select="projSelect"
  />

  <ContentBody>
    <CCardBody class="pb-5">
      <ContNavigation :cont-on="!!contractor?.status && contractor.status < '3'" />
      <ContController :project="project || undefined" @search-contractor="searchContractor" />

      <ContractorAlert v-if="contractor" :contractor="contractor" />

      <SuccessionButton
        v-if="contractor"
        :is-succession="isSuccession"
        @call-form="callFormModal"
      />
      <TableTitleRow title="승계 진행 건 목록" excel :url="downloadUrl" :disabled="!project" />
      <SuccessionList
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
</template>
