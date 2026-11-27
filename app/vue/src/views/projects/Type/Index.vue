<script lang="ts" setup>
import { computed, onBeforeMount, provide, ref, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin4'
import { useProject } from '@/store/pinia/project'
import { useProjectData } from '@/store/pinia/project_data'
import { usePerms } from '@/composables/usePerms'
import type { Project, UnitType } from '@/store/types/project'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import TypeAddForm from '@/views/projects/Type/components/TypeAddForm.vue'
import TypeFormList from '@/views/projects/Type/components/TypeFormList.vue'

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projStore = useProject()
const project = computed(() => (projStore.project as Project | null)?.pk)

const typeSort = [
  { value: '1', label: '공동주택' },
  { value: '2', label: '오피스텔' },
  { value: '3', label: '숙박시설' },
  { value: '4', label: '지식산업센터' },
  { value: '5', label: '근린생활시설' },
  { value: '6', label: '기타' },
] as const

provide('typeSort', typeSort)

const pDataStore = useProjectData()
const fetchTypeList = (projId: number) => pDataStore.fetchTypeList(projId)
const createType = (payload: UnitType) => pDataStore.createType(payload)
const updateType = (payload: UnitType) => pDataStore.updateType(payload)
const deleteType = (pk: number, projId: number) => pDataStore.deleteType(pk, projId)

const onSubmit = (payload: Omit<UnitType, 'pk' | 'project'>) => {
  if (project.value) {
    createType({ project: project.value, ...payload } as UnitType)
  }
}

const onUpdateType = (payload: UnitType) => {
  if (project.value) {
    updateType({ project: project.value, ...payload })
  }
}

const onDeleteType = (pk: number) => {
  if (project.value) deleteType(pk, project.value)
}

watch(
  () => project.value,
  newProjId => {
    pDataStore.unitTypeList = []
    if (newProjId) fetchTypeList(newProjId)
  },
)

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  if (project.value) await fetchTypeList(project.value)
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <CCardBody class="pb-5">
        <TypeAddForm v-if="canProjectUpdate" :disabled="!project" @on-submit="onSubmit" />
        <TypeFormList @on-update="onUpdateType" @on-delete="onDeleteType" />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
