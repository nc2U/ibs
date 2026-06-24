<script lang="ts" setup>
import { computed, type ComputedRef, inject, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import type { IssueProject, ProjectFilter } from '@/store/types/work_project.ts'
import SearchList from './SearchList.vue'
import ProjectCard from './ProjectCard.vue'
import ProjectTable from './ProjectTable.vue'
import NoData from '@/components/NoData/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const workManager = inject<ComputedRef<boolean>>('workManager')

const workStore = useWork()
const projectList = computed<IssueProject[]>(() => workStore.issueProjects)
const allIssueProjects = computed<IssueProject[]>(() => workStore.AllIssueProjects)
const allProjects = computed(() => workStore.getAllProjects)

const viewMode = ref<'board' | 'list'>(
  (localStorage.getItem('project-view-mode') as 'board' | 'list') || 'board',
)
const onChangeViewMode = (mode: 'board' | 'list') => {
  viewMode.value = mode
  localStorage.setItem('project-view-mode', mode)
}

const filterSubmit = (payload: ProjectFilter) => workStore.fetchIssueProjectList(payload)

const route = useRoute()

// 권한 필터링 로직 추가
const hasVisible = (project: IssueProject): boolean => {
  if (project.visible) return true
  if (project.sub_projects && project.sub_projects.length > 0)
    for (let sub of project.sub_projects) {
      if (hasVisible(sub)) return true
    }
  return false
}

// 반응형 설정 (breakpoint 로직 유지)
const breakpoint = ref('xl')

const updateBreakpoint = () => {
  const width = window.innerWidth
  if (width < 768) breakpoint.value = 'sm'
  else if (width < 992) breakpoint.value = 'md'
  else if (width < 1200) breakpoint.value = 'lg'
  else breakpoint.value = 'xl'
}

onMounted(() => {
  updateBreakpoint()
  window.addEventListener('resize', updateBreakpoint)
})
onBeforeUnmount(() => window.removeEventListener('resize', updateBreakpoint))

// 반응형 컬럼 설정 계산
const colProps = computed(() => {
  switch (breakpoint.value) {
    case 'sm': return { xs: 12 }
    case 'md': return { sm: 6 }
    case 'lg': return { sm: 4 }
    default: return { sm: 3 }
  }
})
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>프로젝트</h5>
        </CCol>

        <CCol v-if="workManager" class="text-right form-text">
          <span v-show="route.name !== '프로젝트 - 추가'" class="mr-2">
            <v-icon icon="mdi-plus-circle" color="success" size="15" />
            <router-link :to="{ name: '프로젝트 - 추가' }" class="ml-1">새 프로젝트</router-link>
          </span>
        </CCol>
      </CRow>

      <SearchList
        :all-projects="allProjects"
        @filter-submit="filterSubmit"
        @change-view-mode="onChangeViewMode"
      />

      <NoData v-if="!projectList.length" />

      <div v-else-if="viewMode === 'list'" class="mb-4">
        <ProjectTable :projects="allIssueProjects" />
      </div>

      <CRow v-else>
        <template v-for="proj in projectList" :key="proj.pk">
          <CCol v-if="hasVisible(proj)" v-bind="colProps">
            <ProjectCard :project="proj" />
          </CCol>
        </template>
      </CRow>

      <CRow>
        <CCol class="text-right form-text">
          <span class="mr-2">
            <v-icon icon="mdi-account-tag" color="success" size="15" class="mr-1" />
            <span class="mt-2">내 프로젝트</span>
          </span>

          <span>
            <v-icon icon="mdi-bookmark" color="info" size="15" class="mr-1" />
            <span class="mt-2">내 북마크</span>
          </span>
        </CCol>
      </CRow>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
