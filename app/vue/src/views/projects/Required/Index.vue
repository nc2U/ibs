<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/projects/_menu/headermixin6'
import { usePerms } from '@/composables/usePerms'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import type { Project } from '@/store/types/project'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import RequiredAddForm from '@/views/projects/Required/components/RequiredAddForm.vue'
import RequiredFormList from '@/views/projects/Required/components/RequiredFormList.vue'

const { can, PERM } = usePerms()
const canProjectUpdate = computed(() => can(PERM.PROJECT_UPDATE))

const projStore = useProject()
const contStore = useContract()
const project = computed(() => (projStore.project as Project)?.pk)

const loading = ref(true)

const dataSetup = async (projId: number) => {
  if (!projId) return
  loading.value = true
  try {
    await Promise.all([contStore.fetchDocumentTypeList(), contStore.fetchRequiredDocsList(projId)])
  } finally {
    loading.value = false
  }
}

watch(
  () => project.value,
  newVal => {
    contStore.requiredDocsList = []
    if (newVal) dataSetup(newVal)
  },
)

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
        <RequiredAddForm v-if="canProjectUpdate" :disabled="!project" />
        <RequiredFormList />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
