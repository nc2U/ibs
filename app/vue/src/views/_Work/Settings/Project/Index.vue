<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { navMenu, pageTitle } from '@/views/_Work/_menu/headermixin2'
import { ALL_PROJECT_COLUMNS, DEFAULT_PROJECT_COLUMNS } from './constants'
import { useWork } from '@/store/pinia/work_project.ts'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useTableColumns } from '@/composables/useTableColumns'
import type { IssueProject, ProjectFilter } from '@/store/types/work_project.ts'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ColumnSelector from '@/components/ColumnSelector/Index.vue'
import QuerySection from '@/views/_Work/Manages/Projects/components/QuerySection.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import ProjectTable from './components/ProjectTable.vue'
import Loading from '@/components/Loading/Index.vue'
import NoData from '@/components/NoData/Index.vue'

const cBody = ref()
const sideNavCall = () => cBody.value.toggle()

const { can, PERM } = usePerms()
const canProjectCreate = computed(() => can(PERM.PROJECT_CREATE))

const route = useRoute()
const workStore = useWork()

const projectResultsFlat = computed<IssueProject[]>(() => workStore.projectResultsFlat)
const allReadableProjects = computed(() => workStore.getAllReadableProjects)

// Columns Selector Start
const { selectedColumns } = useTableColumns(
  'settings-project-table-columns',
  ALL_PROJECT_COLUMNS,
  DEFAULT_PROJECT_COLUMNS,
)
// Columns Selector End!

// 검색양식 관련 계산 및 메서드
const filterSubmit = (payload: ProjectFilter) => {
  workStore.fetchIssueProjectList(payload)
}

const loading = ref(true)
onBeforeMount(async () => {
  try {
    await workStore.fetchIssueProjectList({ status: '1' })
  } catch (err) {
    console.error('Failed to load issue project list:', err)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :pageTitle="pageTitle" :navMenu="navMenu" @side-nav-call="sideNavCall" />
  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="true">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon
              icon="mdi-office-building-cog-outline"
              color="blue-grey-lighten-1"
              size="small"
              class="mr-2"
            />
            워크스페이스 관리
          </h5>
        </CCol>

        <CCol v-if="canProjectCreate" class="text-right form-text">
          <span v-show="route.name !== '워크스페이스 - 추가'" class="mr-2">
            <TextButton name="새 워크스페이스" :to="{ name: '워크스페이스 - 추가' }" />
          </span>
        </CCol>
      </CRow>

      <QuerySection
        ref="querySectionRef"
        :all-readable-projects="allReadableProjects"
        show-locked-option
        @filter-submit="filterSubmit"
      >
        <template #option>
          <CRow class="p-2">
            <CCol>
              <ColumnSelector v-model="selectedColumns" :all-columns="ALL_PROJECT_COLUMNS" />
            </CCol>
          </CRow>
        </template>
      </QuerySection>

      <NoData v-if="!projectResultsFlat.length" />

      <ProjectTable v-else :issue-projects-flat="projectResultsFlat" :columns="selectedColumns" />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
