<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { navMenu, pageTitle } from '@/views/projects/_menu/headermixin1'
import { useProject } from '@/store/pinia/project'
import { type Project } from '@/store/types/project'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import IndexForm from '@/views/projects/List/components/IndexForm.vue'
import IndexDetail from '@/views/projects/List/components/IndexDetail.vue'

const compName = ref<'IndexDetail' | 'CreateForm' | 'UpdateForm'>('IndexDetail')

const projStore = useProject()
const project = computed(() => projStore.project)

const createForm = () => (compName.value = 'CreateForm')
const updateForm = () => (compName.value = 'UpdateForm')
const resetForm = () => (compName.value = 'IndexDetail')

const toSubmit = async (payload: Project) => {
  const ok = payload.pk
    ? await projStore.updateProject(payload)
    : await projStore.createProject(payload)
  if (ok) compName.value = 'IndexDetail'
}

watch(
  () => project.value,
  () => {
    compName.value = 'IndexDetail'
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  if (!projStore.project && projStore.currentProject) {
    await projStore.fetchProject(projStore.currentProject)
  }
  loading.value = false
})
</script>

<template>
  <ProjectAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <IndexDetail
        v-if="compName === 'IndexDetail'"
        :project="project as Project"
        @reset-form="resetForm"
        @create-form="createForm"
        @update-form="updateForm"
      />

      <IndexForm v-if="compName === 'CreateForm'" @to-submit="toSubmit" @reset-form="resetForm" />

      <IndexForm
        v-if="compName === 'UpdateForm'"
        :project="project as Project"
        @to-submit="toSubmit"
        @reset-form="resetForm"
      />
    </ContentBody>
  </ProjectAuthGuard>
</template>
