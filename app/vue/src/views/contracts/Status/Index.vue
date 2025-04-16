<script lang="ts" setup>
import { ref, computed, onBeforeMount, provide } from 'vue'
import { pageTitle, navMenu } from '@/views/contracts/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useProjectData } from '@/store/pinia/project_data'
import { useContract } from '@/store/pinia/contract'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import Loading from '@/components/Loading/Index.vue'
import ContSummary from '@/views/contracts/Status/components/ContSummary.vue'
import TableTitleRow from '@/components/TableTitleRow.vue'
import ContractBoard from '@/views/contracts/Status/components/ContractBoard.vue'

const projStore = useProject()
const project = computed(() => projStore.project?.pk)

const pDataStore = useProjectData()
const isLoading = computed(() => pDataStore.isLoading)
const fetchTypeList = (projId: number) => pDataStore.fetchTypeList(projId)
const fetchBuildingList = (projId: number) => pDataStore.fetchBuildingList(projId)
const fetchHouseUnitList = (projId: number) => pDataStore.fetchHouseUnitList(projId)

const contStore = useContract()
const fetchContractList = (payload: { project: number }) => contStore.fetchContractList(payload)
const fetchSubsSummaryList = (projId: number) => contStore.fetchSubsSummaryList(projId)
const fetchContSummaryList = (projId: number) => contStore.fetchContSummaryList(projId)

const isContor = ref<boolean>(true)
const excelUrl = computed(() =>
  project.value ? `/excel/status/?project=${project.value}&iscontor=${isContor.value}` : '',
)

provide('isContor', isContor)

const dataSetup = (pk: number) => {
  fetchTypeList(pk)
  fetchBuildingList(pk)
  fetchHouseUnitList(pk)
  fetchSubsSummaryList(pk)
  fetchContractList({ project: pk })
  fetchContSummaryList(pk)
}

const dataReset = () => {
  pDataStore.unitTypeList = []
  pDataStore.buildingList = []
  pDataStore.houseUnitList = []
  contStore.subsSummaryList = []
  contStore.contSummaryList = []
  contStore.contractsCount = 0
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

onBeforeMount(() => dataSetup(project.value || projStore.initProjId))
</script>

<template>
  <Loading v-model:active="isLoading" />
  <ContentHeader
    :page-title="pageTitle"
    :nav-menu="navMenu"
    selector="ProjectSelect"
    @proj-select="projSelect"
  />

  <ContentBody>
    <CCardBody class="pb-5">
      <ContSummary />
      <TableTitleRow excel :url="excelUrl" :disabled="!project">
        <div class="p-2">
          <CFormSwitch
            id="flexCheckDefault"
            v-model="isContor"
            label="계약자명 표시"
            style="font-size: 0.825em"
            :disabled="!project"
          />
        </div>
      </TableTitleRow>
      <v-divider color="grey" class="my-0" />
      <ContractBoard />
    </CCardBody>
  </ContentBody>
</template>
