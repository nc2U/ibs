<script lang="ts" setup>
import { computed, onBeforeMount, provide, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/projects/_menu/headermixin3'
import { write_project } from '@/utils/pageAuth'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { useProLedger } from '@/store/pinia/proLedger.ts'
import { useProjectData } from '@/store/pinia/project_data'
import type { Project, ProOutBudget } from '@/store/types/project'
import type { ProAccountFilter } from '@/store/types/proLedger.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import BudgetAddForm from '@/views/projects/OutBudget/components/BudgetAddForm.vue'
import BudgetFormList from '@/views/projects/OutBudget/components/BudgetFormList.vue'

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const pLedgerStore = useProLedger()
const allProAccount = computed(() => pLedgerStore.proAccounts)
const fetchProjectAccounts = (payload: ProAccountFilter) =>
  pLedgerStore.fetchProjectAccounts(payload)

const contStore = useContract()
const getOrderGroups = computed(() => contStore.getOrderGroups)

const pDataStore = useProjectData()
const getTypes = computed(() => pDataStore.getTypes)

provide('accountList', allProAccount)
provide('orderGroups', getOrderGroups)
provide('unitTypes', getTypes)

const fetchOutBudgetList = (pj: number) => projStore.fetchOutBudgetList(pj)
const createOutBudget = (payload: ProOutBudget) => projStore.createOutBudget(payload)
const updateOutBudget = (payload: ProOutBudget) => projStore.updateOutBudget(payload)
const deleteOutBudget = (pk: number, project: number) => projStore.deleteOutBudget(pk, project)

const fetchOrderGroupList = (proj: number) => contStore.fetchOrderGroupList(proj)

const fetchTypeList = (proj: number) => pDataStore.fetchTypeList(proj)

const onSubmit = (payload: ProOutBudget) => {
  if (project.value) createOutBudget({ ...{ project: project.value }, ...payload })
}

const onUpdateBudget = (payload: ProOutBudget) => {
  if (project.value) updateOutBudget({ ...{ project: project.value }, ...payload })
}

const onDeleteBudget = (pk: number) => {
  if (project.value) deleteOutBudget(pk, project.value)
}

const dataSetup = (pk: number) => {
  fetchOrderGroupList(pk)
  fetchTypeList(pk)
  fetchOutBudgetList(pk)
}

const dataReset = () => {
  contStore.orderGroupList = []
  pDataStore.unitTypeList = []
  projStore.proOutBudgetList = []
}

const projSelect = (target: number | null) => {
  dataReset()
  if (!!target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  await fetchProjectAccounts({
    direction: 'withdraw',
    is_category_only: false,
    is_active: true,
    category: 'expense',
  })
  dataSetup(project.value || projStore.initProjId)
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      @proj-select="projSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <BudgetAddForm v-if="write_project" :disabled="!project" @on-submit="onSubmit" />
        <BudgetFormList @on-update="onUpdateBudget" @on-delete="onDeleteBudget" />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
