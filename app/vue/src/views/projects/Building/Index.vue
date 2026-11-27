<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin5'
import { useProject } from '@/store/pinia/project'
import { useProjectData } from '@/store/pinia/project_data'
import { usePerms } from '@/composables/usePerms.ts'
import type { BuildingUnit, Project } from '@/store/types/project'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import BuildingAddForm from '@/views/projects/Building/components/BuildingAddForm.vue'
import BuildingFormList from '@/views/projects/Building/components/BuildingFormList.vue'

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projStore = useProject()
const project = computed(() => (projStore.project as Project | null)?.pk)

const pDataStore = useProjectData()
const fetchBuildingList = (projId: number) => pDataStore.fetchBuildingList(projId)
const createBuilding = (payload: BuildingUnit) => pDataStore.createBuilding(payload)
const updateBuilding = (payload: BuildingUnit) => pDataStore.updateBuilding(payload)
const deleteBuilding = (pk: number, projId: number) => pDataStore.deleteBuilding(pk, projId)

const onCreateBuilding = (payload: { name: string }) => {
  if (project.value) {
    createBuilding({ project: project.value, name: payload.name } as BuildingUnit)
  }
}

const onUpdateBuilding = (payload: { pk?: number; name: string }) => {
  if (project.value && payload.pk) {
    updateBuilding({ project: project.value, pk: payload.pk, name: payload.name } as BuildingUnit)
  }
}

const onDeleteBuilding = (pk: number) => {
  if (project.value) {
    deleteBuilding(pk, project.value)
  }
}

watch(
  () => project.value,
  newProjId => {
    if (newProjId) fetchBuildingList(newProjId)
    else pDataStore.buildingList = []
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  if (project.value) await fetchBuildingList(project.value)
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <CCardBody class="pb-5">
        <BuildingAddForm
          v-if="canProjectUpdate"
          :disabled="!project"
          @on-submit="onCreateBuilding"
        />
        <BuildingFormList @on-update="onUpdateBuilding" @on-delete="onDeleteBuilding" />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
