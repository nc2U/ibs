<script lang="ts" setup>
import { computed, onBeforeMount, provide, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/projects/_menu/headermixin3'
import { useProject } from '@/store/pinia/project'
import { useProLedger } from '@/store/pinia/proLedger'
import { usePerms } from '@/composables/usePerms'
import type { Project, ProOutBudget } from '@/store/types/project'
import type { ProAccountFilter } from '@/store/types/proLedger'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import BudgetAddForm from '@/views/projects/OutBudget/components/BudgetAddForm.vue'
import BudgetFormList from '@/views/projects/OutBudget/components/BudgetFormList.vue'

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const pLedgerStore = useProLedger()
const allProAccount = computed(() => pLedgerStore.proAccounts)
const fetchProjectAccounts = (payload: ProAccountFilter) =>
  pLedgerStore.fetchProjectAccounts(payload)

provide('accountList', allProAccount)

const fetchOutBudgetList = (pj: number) => projStore.fetchOutBudgetList(pj)
const createOutBudget = (payload: ProOutBudget) => projStore.createOutBudget(payload)
const updateOutBudget = (payload: ProOutBudget) => projStore.updateOutBudget(payload)
const deleteOutBudget = (pk: number, project: number) => projStore.deleteOutBudget(pk, project)

const onSubmit = (payload: Omit<ProOutBudget, 'pk' | 'project'>) => {
  if (project.value) createOutBudget({ project: project.value, ...payload })
}

const onUpdateBudget = (payload: ProOutBudget) => {
  if (project.value) updateOutBudget({ project: project.value, ...payload })
}

const onDeleteBudget = (pk: number) => {
  if (project.value) deleteOutBudget(pk, project.value)
}

const dataSetup = async (pk: number) => {
  await fetchOutBudgetList(pk)
}

const dataReset = () => {
  projStore.proOutBudgetList = []
}

watch(
  () => project.value,
  newProjId => {
    dataReset()
    if (newProjId) dataSetup(newProjId)
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  await fetchProjectAccounts({
    direction: 'withdraw',
    is_category_only: false,
    is_active: true,
    category: 'expense',
  })
  if (project.value) await dataSetup(project.value)
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <CCardBody class="pb-5">
        <BudgetAddForm v-if="canProjectUpdate" :disabled="!project" @on-submit="onSubmit" />
        <BudgetFormList @on-update="onUpdateBudget" @on-delete="onDeleteBudget" />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
