<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin5'
import { write_project } from '@/utils/pageAuth'
import { useProject } from '@/store/pinia/project'
import { useProjectData } from '@/store/pinia/project_data'
import type { BuildingUnit, Project } from '@/store/types/project'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import BuildingAddForm from '@/views/projects/Building/components/BuildingAddForm.vue'
import BuildingFormList from '@/views/projects/Building/components/BuildingFormList.vue'

const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)

const pDataStore = useProjectData()
const fetchBuildingList = (projId: number) => pDataStore.fetchBuildingList(projId)
const createBuilding = (payload: BuildingUnit) => pDataStore.createBuilding(payload)
const updateBuilding = (payload: BuildingUnit) => pDataStore.updateBuilding(payload)
const deleteBuilding = (pk: number, projId: number) => pDataStore.deleteBuilding(pk, projId)

const onCreateBuilding = (payload: BuildingUnit) =>
  createBuilding({ ...{ project: project.value }, ...payload })

const onUpdateBuilding = (payload: BuildingUnit) =>
  updateBuilding({ ...{ project: project.value }, ...payload })

const onDeleteBuilding = (pk: number) => {
  if (project.value) deleteBuilding(pk, project.value as number)
}

const projSelect = (target: number | null) => {
  pDataStore.buildingList = []
  if (!!target) fetchBuildingList(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  await fetchBuildingList(project.value || projStore.initProjId)
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
        <BuildingAddForm v-if="write_project" :disabled="!project" @on-submit="onCreateBuilding" />
        <BuildingFormList @on-update="onUpdateBuilding" @on-delete="onDeleteBuilding" />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
