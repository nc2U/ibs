<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/contracts/_menu/headermixin'
import type { Project } from '@/store/types/project'
import { useContract } from '@/store/pinia/contract'
import type { Contract, Contractor } from '@/store/types/contract'
import { useRoute, useRouter } from 'vue-router'
import { useProject } from '@/store/pinia/project'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContractAuthGuard from '@/components/AuthGuard/ContractAuthGuard.vue'
import ContractManage from './components/ContractManage.vue'
import ContNavigation from '@/views/contracts/Manage/components/ContNavigation.vue'
import ContController from '@/views/contracts/Manage/components/ContController.vue'
import ContractorAlert from '@/views/contracts/Manage/components/ContractorAlert.vue'

const [route, router] = [useRoute(), useRouter()]

// URL params에서 contractorId 읽기
const contractorId = computed(() =>
  route.params.contractorId ? parseInt(route.params.contractorId as string, 10) : null,
)

// URL에서 from_page 파라미터 읽기
const fromPage = computed(() =>
  route.query.from_page ? parseInt(route.query.from_page as string, 10) : null,
)
const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const contStore = useContract()
const contract = computed(() => contStore.contract as Contract | null)
const contractor = computed(() => contStore.contractor as Contractor | null)

const fetchContract = (cont: number) => contStore.fetchContract(cont)
const fetchContractor = (contor: number, proj?: number) => contStore.fetchContractor(contor, proj)
const fetchContractorList = (projId: number, search = '') =>
  contStore.fetchContractorList(projId, search)
const fetchRequiredDocsList = (projId: number) => contStore.fetchRequiredDocsList(projId)
const fetchContAddressList = (contor: number) => contStore.fetchContAddressList(contor)

watch(
  () => route.params.contractorId,
  contractorId => {
    if (contractorId) getContract(contractorId as string)
    else {
      contStore.removeContractor()
    }
  },
)

watch(contractor, val => {
  if (!!val) {
    if (val.contract && !!contract.value && contract.value.pk !== val.contract)
      fetchContract(val.contract)
    fetchContAddressList(val.pk)
  }
})

const getContract = async (contor: string) => {
  await fetchContractor(parseInt(contor), project.value)
  await fetchContract(contractor.value?.contract as number)
  await fetchContAddressList(parseInt(contor))
}

const searchContractor = async (search: string) => {
  if (search !== '' && project.value) {
    await fetchContractorList(project.value, search)
  } else contStore.contractorList = []
}

const dataSetup = (pk: number) => {
  fetchRequiredDocsList(pk)
}

const dataReset = () => {
  contStore.requiredDocsList = []
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  dataSetup(project.value || projStore.initProjId)
  if (contractorId.value) {
    await getContract(contractorId.value.toString())
    await fetchContAddressList(contractorId.value)
  } else {
    contStore.removeContract()
    contStore.removeContractor()
    contStore.contAddressList = []
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
        <ContNavigation :cont-on="!!contract" :contractor="contractor?.pk" />
        <ContController :project="project" @search-contractor="searchContractor" />
        <ContractorAlert v-if="contractor" :is-blank="!contract" :contractor="contractor" />

        <ContractManage
          :project="project ?? undefined"
          :contract="contract ?? undefined"
          :contractor="contractor ?? undefined"
          :from-page="fromPage"
        />
      </CCardBody>
    </ContentBody>
  </ContractAuthGuard>
</template>
