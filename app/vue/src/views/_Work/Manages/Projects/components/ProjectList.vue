<script lang="ts" setup>
import { computed, onBeforeMount, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { useWork } from '@/store/pinia/work_project.ts'
import { useInform } from '@/store/pinia/work_inform.ts'
import type { IssueProject, ProjectFilter } from '@/store/types/work_project.ts'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import QuerySection from './QuerySection.vue'
import ProjectCard from './ProjectCard.vue'
import ProjectTable from './ProjectTable.vue'
import NoData from '@/components/NoData/Index.vue'
import SavedQueryAside from '@/views/_Work/components/asides/SavedQueryAside.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const workStore = useWork()
const { can, PERM } = usePerms() // 사용자 권한 데이터
const issueProjectsTree = computed<IssueProject[]>(() => workStore.issueProjectsTree)
const issueProjectsFlat = computed<IssueProject[]>(() => workStore.issueProjectsFlat)
const allProjects = computed(() => workStore.getAllProjects)
const rollList = computed(() => workStore.roleList)

const viewMode = ref<'board' | 'list'>(
  (localStorage.getItem('project-view-mode') as 'board' | 'list') || 'board',
)
const onChangeViewMode = (mode: 'board' | 'list') => {
  viewMode.value = mode
  localStorage.setItem('project-view-mode', mode)
}

const filterSubmit = (payload: ProjectFilter) => {
  if (activeQueryId.value) {
    // 사용자가 임의의 다른 필터 제출 시 하이라이트 지우기 (단, payload가 쿼리에 의한 것이 아닐 때)
    // 여기서는 간단히 두겠습니다.
  }
  workStore.fetchIssueProjectList(payload)
}

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

// 반응형 컬럼 설정 계산
const colProps = computed(() => {
  switch (breakpoint.value) {
    case 'sm':
      return { xs: 12 } // 768px 미만
    case 'md':
      return { md: 6 } // 768px 이상, 992px 미만 (기존 sm: 6 수정)
    case 'lg':
      return { lg: 4 } // 992px 이상, 1200px 미만 (기존 sm: 4 수정)
    default:
      return { xl: 3 } // 1200px 이상 (기존 sm: 3 수정)
  }
})

// 검색양식 관련 계산 및 메서드
const activeQueryId = ref<number | null>(null)
const querySectionRef = ref()

const onQueryClick = (query: any) => {
  activeQueryId.value = query.pk
  if (querySectionRef.value) {
    querySectionRef.value.applyQuery(query)
  }
}

const onResetQuery = () => {
  activeQueryId.value = null
  if (querySectionRef.value) {
    querySectionRef.value.resetFilter()
  }
}

// onDeleteQuery 제거됨

onMounted(() => {
  updateBreakpoint()
  window.addEventListener('resize', updateBreakpoint)
})
onBeforeUnmount(() => window.removeEventListener('resize', updateBreakpoint))

onBeforeMount(() => {
  workStore.fetchAllProjectList('', '', 'all')
  workStore.fetchIssueProjectList({ status: '1' })
  workStore.fetchBookmarks()
})
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5><v-icon icon="mdi-domain" color="primary" size="small" class="mr-2" />프로젝트</h5>
        </CCol>

        <CCol v-if="can(PERM.PROJECT_CREATE)" class="text-right form-text">
          <span v-show="route.name !== '프로젝트 - 추가'" class="mr-2">
            <TextButton name="새 프로젝트" :to="{ name: '프로젝트 - 추가' }" />
          </span>
        </CCol>
      </CRow>

      <QuerySection
        ref="querySectionRef"
        :all-projects="allProjects"
        @filter-submit="filterSubmit"
        @change-view-mode="onChangeViewMode"
      />

      <NoData v-if="!issueProjectsTree.length" />

      <div v-else-if="viewMode === 'list'" class="mb-4">
        <ProjectTable :issue-projects-flat="issueProjectsFlat" />
      </div>

      <CRow v-else>
        <template v-for="proj in issueProjectsTree" :key="proj.pk">
          <CCol v-if="hasVisible(proj)" v-bind="colProps">
            <CCard class="my-2 my-lg-3">
              <CCardBody class="pb-1">
                <ProjectCard :project="proj" />
              </CCardBody>
            </CCard>
          </CCol>
        </template>
      </CRow>

      <CRow class="mt-3">
        <CCol class="text-right form-text">
          <span class="mr-3">
            <v-icon icon="mdi-account-tag" color="success" size="small" class="mr-2" />
            내 프로젝트
          </span>

          <span class="mr-2">
            <v-icon icon="mdi-bookmark" color="info" size="small" class="mr-2" />
            내 북마크
          </span>
        </CCol>
      </CRow>
      <CRow class="text-right text">
        <div class="my-5"></div>
        <CCol class="mt-4 p-3 bg-more-light text-muted">
          <v-icon icon="mdi-information" color="light-blue-lighten-2" size="small" class="mr-2" />
          프로젝트를 생성 하려면
          <strong>
            {{
              rollList
                .filter(r => r.permissions.includes(1))
                .map(r => r.name)
                .join(', ')
            }}
          </strong>
          역할이 필요합니다.<br />
          해당 역할을 배정 받거나 해당 멤버에게 생성을 요청하시기 바랍니다.
        </CCol>
      </CRow>
    </template>
    <template v-slot:aside>
      <SavedQueryAside
        target-type="project"
        :active-query-id="activeQueryId ?? undefined"
        :canProjectPubQuery="can(PERM.PROJECT_PUB_QUERY)"
        @on-query-click="onQueryClick"
        @on-reset-query="onResetQuery"
      />
    </template>
  </ContentBody>
</template>
