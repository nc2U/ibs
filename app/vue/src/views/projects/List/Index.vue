<script lang="ts" setup>
import { ref, computed, onBeforeMount, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/projects/_menu/headermixin1'
import { useWork } from '@/store/pinia/work'
import { useProject } from '@/store/pinia/project'
import { type Project } from '@/store/types/project'
import type { IssueProject } from '@/store/types/work'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
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
const toSubmit = (payload: Project) => {
  if (payload.pk) toUpdate(payload)
  else toCreate(payload)
}

const workStore = useWork()
const getAllProjects = computed(() => workStore.getAllProjects)
const fetchAllIssueProjectList = (is_dev: '' | '1', p_isnull = '1') =>
  workStore.fetchAllIssueProjectList(is_dev, p_isnull)
const createIssueProject = (payload: IssueProject) => workStore.createIssueProject(payload)

onBeforeMount(() => fetchAllIssueProjectList('1', ''))
</script>

<template>
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
      :get-projects="getAllProjects"
      @to-submit="toSubmit"
      @reset-form="resetForm"
      @issue-pr-submit="createIssueProject"
    />

    <IndexForm
      v-if="compName === 'UpdateForm'"
      :project="project as Project"
      :get-projects="getAllProjects"
      @to-submit="toSubmit"
      @reset-form="resetForm"
      @issue-pr-submit="createIssueProject"
    />

    <template #footer>
      <div style="display: none"></div>
    </template>
  </ContentBody>
</template>
