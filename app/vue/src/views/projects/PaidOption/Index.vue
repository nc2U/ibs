<script lang="ts" setup>
import { computed, onBeforeMount, provide, ref, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin6'
import { useProject } from '@/store/pinia/project'
import { useProjectData } from '@/store/pinia/project_data'
import { usePerms } from '@/composables/usePerms'
import type { OptionItem, Project } from '@/store/types/project'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import OptionAddForm from '@/views/projects/PaidOption/components/OptionAddForm.vue'
import OptionFormList from '@/views/projects/PaidOption/components/OptionFormList.vue'

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const pDataStore = useProjectData()
const getTypes = computed(() => pDataStore.getTypes)
provide('getTypes', getTypes)

const fetchTypeList = (projId: number, sort?: '1') => pDataStore.fetchTypeList(projId, sort)
const fetchOptionItemList = (proj: number) => pDataStore.fetchOptionItemList(proj)
const createOptionItem = (payload: OptionItem) => pDataStore.createOptionItem(payload)
const updateOptionItem = (payload: OptionItem) => pDataStore.updateOptionItem(payload)
const deleteOptionItem = (pk: number, proj: number) => pDataStore.deleteOptionItem(pk, proj)

const onSubmit = (payload: Omit<OptionItem, 'pk' | 'project'>) => {
  if (project.value) createOptionItem({ project: project.value, ...payload })
}

const onUpdateOption = (payload: OptionItem) => {
  if (project.value) updateOptionItem({ ...payload, project: project.value })
}

const onDeleteOption = (pk: number) => {
  if (project.value) deleteOptionItem(pk, project.value)
}

const dataSetup = async (pk: number) => {
  await fetchTypeList(pk, '1')
  await fetchOptionItemList(pk)
}

const dataReset = () => {
  pDataStore.unitTypeList = []
  pDataStore.optionItemList = []
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
        <OptionAddForm v-if="canProjectUpdate" :disabled="!project" @on-submit="onSubmit" />
        <OptionFormList @on-update="onUpdateOption" @on-delete="onDeleteOption" />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
