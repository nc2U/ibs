<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/projects/_menu/headermixin6'
import { useProject } from '@/store/pinia/project.ts'
import { useContract } from '@/store/pinia/contract.ts'
import type { Project } from '@/store/types/project.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import RequiredAddForm from '@/views/projects/Required/components/RequiredAddForm.vue'
import RequiredFormList from '@/views/projects/Required/components/RequiredFormList.vue'

const projStore = useProject()
const contStore = useContract()
const project = computed(() => (projStore.project as Project)?.pk)

const dataSetup = async (projId: number) => {
  if (!projId) return
  loading.value = true
  try {
    await Promise.all([contStore.fetchDocumentTypeList(), contStore.fetchRequiredDocsList(projId)])
  } finally {
    loading.value = false
  }
}

const projSelect = (target: number | null) => {
  if (target) dataSetup(target)
}

const loading = ref(true)
onBeforeMount(async () => {
  await dataSetup(project.value || projStore.initProjId)
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
        <RequiredAddForm />
        <RequiredFormList />
      </CCardBody>
    </ContentBody>
  </ProjectAuthGuard>
</template>
