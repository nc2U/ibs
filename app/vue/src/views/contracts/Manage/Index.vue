<script lang="ts" setup>
import { ref, computed, watch, onBeforeMount } from 'vue'
import { pageTitle, navMenu } from '@/views/contracts/_menu/headermixin'
import type { Project } from '@/store/types/project'
import { type UnitFilter, useContract } from '@/store/pinia/contract'
import type { Contract, Contractor, ContractorAddress } from '@/store/types/contract'
import { useRoute, useRouter } from 'vue-router'
import { useProject } from '@/store/pinia/project'
import { usePayment } from '@/store/pinia/payment'
import { useProCash } from '@/store/pinia/proCash'
import { useProjectData } from '@/store/pinia/project_data'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContractAuthGuard from '@/components/AuthGuard/ContractAuthGuard.vue'
import ContractManage from './components/ContractManage.vue'

const contForm = ref()

const [route, router] = [useRoute(), useRouter()]

// URL에서 from_page 파라미터 읽기
const fromPage = computed(() =>
  route.query.from_page ? parseInt(route.query.from_page as string, 10) : null,
)

const contStore = useContract()
const contract = computed<Contract | null>(() => contStore.contract)
const contractor = computed<Contractor | null>(() => contStore.contractor)

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)
const unitSet = computed(() => (projStore.project as Project)?.is_unit_set)
const isUnion = computed(() => !(projStore.project as Project)?.is_direct_manage)

const fetchContract = (cont: number) => contStore.fetchContract(cont)

const fetchContractor = (contor: number, proj?: number) => contStore.fetchContractor(contor, proj)

const fetchContractorList = (projId: number, search = '') =>
  contStore.fetchContractorList(projId, search)

const fetchContAddressList = (contor: number) => contStore.fetchContAddressList(contor)

const fetchOrderGroupList = (projId: number) => contStore.fetchOrderGroupList(projId)

const fetchKeyUnitList = (payload: UnitFilter) => contStore.fetchKeyUnitList(payload)

const fetchHouseUnitList = (payload: UnitFilter) => contStore.fetchHouseUnitList(payload)

const projDataStore = useProjectData()
const fetchTypeList = (projId: number) => projDataStore.fetchTypeList(projId)

const proCashStore = useProCash()
const fetchAllProBankAccList = (projId: number) => proCashStore.fetchAllProBankAccList(projId)

const paymentStore = usePayment()
const fetchPayOrderList = (projId: number) => paymentStore.fetchPayOrderList(projId)

watch(route, val => {
  const { contractor } = val.query
  if (!!contractor) getContract(contractor as string)
  else {
    contStore.removeContractor()
    contForm.value.formDataReset()
  }
})

const resumeForm = (contor: string) => getContract(contor)

watch(contractor, val => {
  if (!!val) {
    if (val.contract && !!contract.value && contract.value.pk !== val.contract)
      fetchContract(val.contract)
    fetchContAddressList(val.pk)
  }
})

watch(contract, newVal => {
  if (newVal && project.value) {
    fetchKeyUnitList({
      project: project.value,
      unit_type: newVal.unit_type,
      contract: newVal.pk,
    })
    if (newVal.key_unit?.houseunit) {
      fetchHouseUnitList({
        project: project.value,
        unit_type: newVal.unit_type,
        contract: newVal.pk,
      })
    } else {
      fetchHouseUnitList({
        project: project.value,
        unit_type: newVal.unit_type,
      })
    }
  }
})

const getContract = async (contor: string) => {
  await fetchContractor(parseInt(contor), project.value)
  await fetchContract(contractor.value?.contract as number)
  await fetchContAddressList(parseInt(contor))
}

const typeSelect = (payload: {
  unit_type?: number
  contract?: number
  available?: 'true' | ''
}) => {
  if (project.value) {
    fetchKeyUnitList({ project: project.value, ...payload })
    fetchHouseUnitList({ project: project.value, ...payload })
  }
}

const onSubmit = (payload: Contract & { status: '1' | '2' }) => {
  const { pk, ...getData } = payload as { [key: string]: any }

  const form = new FormData()

  for (const key in getData) form.set(key, getData[key] ?? '')

  // from_page 정보 추가 (수정인 경우에만)
  if (pk && fromPage.value) {
    form.set('from_page', fromPage.value.toString())
  }

  if (!pk) {
    contStore.createContractSet(form)
    if (payload.status === '1') {
      router.replace({ name: '계약 내역 조회', query: { status: '1' } })
    } else router.replace({ name: '계약 내역 조회' })
  } else contStore.updateContractSet(pk, form)
}

const searchContractor = (search: string) => {
  if (search !== '' && project.value) {
    fetchContractorList(project.value, search)
  } else contStore.contractorList = []
}

const dataSetup = (pk: number) => {
  fetchTypeList(pk)
  fetchPayOrderList(pk)
  fetchOrderGroupList(pk)
  fetchAllProBankAccList(pk)
  fetchKeyUnitList({ project: pk })
  fetchHouseUnitList({ project: pk })
}

const dataReset = () => {
  contStore.removeContract()
  contStore.removeContractor()
  contStore.orderGroupList = []
  contStore.keyUnitList = []
  contStore.houseUnitList = []
  projDataStore.unitTypeList = []
  paymentStore.payOrderList = []
  proCashStore.proBankAccountList = []
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) {
    contForm.value.formDataReset()
    dataSetup(target)
  }
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
        ref="contForm"
        :project="project ?? undefined"
        :contract="contract ?? undefined"
        :contractor="contractor ?? undefined"
        :unit-set="unitSet"
        :is-union="isUnion"
        :from-page="fromPage"
        @type-select="typeSelect"
        @on-submit="onSubmit"
        @resume-form="resumeForm"
        @search-contractor="searchContractor"
      />

      <template #footer>
        <div style="display: none"></div>
      </template>
    </ContentBody>
  </ContractAuthGuard>
</template>
