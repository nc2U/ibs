<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/projects/_menu/headermixin1'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useProject } from '@/store/pinia/project'
import { type Project } from '@/store/types/project'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ProjectAuthGuard from '@/components/AuthGuard/ProjectAuthGuard.vue'
import IndexForm from '@/views/projects/List/components/IndexForm.vue'
import IndexDetail from '@/views/projects/List/components/IndexDetail.vue'

const compName = ref('IndexDetail')

const projStore = useProject()
const project = computed(() => projStore.project)

const createProject = (payload: Project) => projStore.createProject(payload)
const updateProject = (payload: Project) => projStore.updateProject(payload)

const createForm = () => (compName.value = 'CreateForm')
const updateForm = () => (compName.value = 'UpdateForm')
const resetForm = () => (compName.value = 'IndexDetail')

const toCreate = (payload: Project) => createProject(payload)
const toUpdate = (payload: Project) => updateProject(payload)
const toSubmit = async (payload: Project) => {
  if (payload.pk) await toUpdate(payload)
  else await toCreate(payload)
  compName.value = 'IndexDetail'
}

const workStore = useWork()
const getAllProjPks = computed(() => workStore.getAllProjPks)
const getProjects = (sort: '1' | '2' | '3') => workStore.fetchAllIssueProjectList('', sort, '')

const issueStore = useIssue()

const loading = ref(true)
onBeforeMount(async () => {
  await workStore.fetchAllIssueProjectList('', '2', '')
  await workStore.fetchRoleList()
  await issueStore.fetchTrackerList()
  await issueStore.fetchActivityList()
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

      <IndexForm
        v-if="compName === 'CreateForm'"
        :get-projects="getAllProjPks"
        @to-submit="toSubmit"
        @reset-form="resetForm"
        @get-project="getProjects"
      />

      <IndexForm
        v-if="compName === 'UpdateForm'"
        :project="project as Project"
        :get-projects="getAllProjPks"
        @to-submit="toSubmit"
        @reset-form="resetForm"
        @get-project="getProjects"
      />

      <template #footer>
        <div style="display: none"></div>
      </template>
    </ContentBody>
  </ProjectAuthGuard>
</template>
