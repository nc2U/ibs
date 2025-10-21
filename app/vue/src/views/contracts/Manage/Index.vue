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

const [route, router] = [useRoute(), useRouter()]

// URL에서 from_page 파라미터 읽기
const fromPage = computed(() =>
  route.query.from_page ? parseInt(route.query.from_page as string, 10) : null,
)

const contStore = useContract()
const contract = computed(() => contStore.contract as Contract | null)
const contractor = computed(() => contStore.contractor as Contractor | null)

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)
const unitSet = computed(() => (projStore.project as Project)?.is_unit_set)
const isUnion = computed(() => !(projStore.project as Project)?.is_direct_manage)

const fetchContract = (cont: number) => contStore.fetchContract(cont)
const fetchContractor = (contor: number, proj?: number) => contStore.fetchContractor(contor, proj)
const fetchContractorList = (projId: number, search = '') =>
  contStore.fetchContractorList(projId, search)

const fetchContAddressList = (contor: number) => contStore.fetchContAddressList(contor)

watch(route, val => {
  const { contractor } = val.query
  if (!!contractor) getContract(contractor as string)
  else {
    contStore.removeContractor()
  }
})

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

const searchContractor = (search: string) => {
  if (search !== '' && project.value) {
    fetchContractorList(project.value, search)
  } else contStore.contractorList = []
}

const dataSetup = (pk: number) => {}

const dataReset = () => {}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  dataSetup(project.value || projStore.initProjId)
  if (route.query.contractor) {
    await getContract(route.query.contractor as string)
    await fetchContAddressList(parseInt(route.query.contractor as string))
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
      <ContractManage
        :project="project ?? undefined"
        :contract="contract ?? undefined"
        :contractor="contractor ?? undefined"
        :unit-set="unitSet"
        :is-union="isUnion"
        :from-page="fromPage"
        @search-contractor="searchContractor"
      />

      <template #footer>
        <div style="display: none"></div>
      </template>
    </ContentBody>
  </ContractAuthGuard>
</template>
