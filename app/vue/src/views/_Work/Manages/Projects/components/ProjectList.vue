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

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const workStore = useWork()
const informStore = useInform()
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
      return { xs: 12 }
    case 'md':
      return { sm: 6 }
    case 'lg':
      return { sm: 4 }
    default:
      return { sm: 3 }
  }
})

// 검색양식 관련 계산 및 메서드
const activeQueryId = ref<number | null>(null)
const querySectionRef = ref()

const myQueries = computed(() =>
  informStore.queries.filter(q => !q.is_public && q.target_type === 'project'),
)
const publicQueries = computed(() =>
  informStore.queries.filter(q => q.is_public && q.target_type === 'project'),
)

const onQueryClick = (query: any) => {
  activeQueryId.value = query.pk
  if (querySectionRef.value) {
    querySectionRef.value.applyQuery(query)
  }
}

const onDeleteQuery = async (query: any, event: Event) => {
  event.stopPropagation() // 클릭 이벤트 전파 방지
  if (confirm(`'${query.name}' 검색 양식을 삭제하시겠습니까?`)) {
    await informStore.deleteQuery(query.pk)
    await informStore.fetchQueries({ targetType: 'project' })
  }
}

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
            <ProjectCard :project="proj" />
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
      <div class="mb-4">
        <div class="mb-4">
          <h5 class="text-subtitle-1 mb-2 strong">내 검색 양식</h5>
          <v-list density="compact" nav class="pa-0 bg-transparent">
            <v-list-item
              v-for="q in myQueries"
              :key="q.pk"
              link
              @click="onQueryClick(q)"
              :active="activeQueryId === q.pk"
              active-color="indigo"
              class="rounded-lg mb-1 px-2 query-item pr-3"
            >
              <template v-slot:prepend>
                <v-icon icon="mdi-filter-variant" size="small" class="mr-1" color="indigo" />
              </template>
              <v-list-item-title style="font-size: 1em">{{ q.name }}</v-list-item-title>
              <template v-slot:append>
                <v-btn
                  icon="mdi-close-circle"
                  size="small"
                  variant="text"
                  color="grey"
                  class="delete-btn"
                  @click="onDeleteQuery(q, $event)"
                />
              </template>
            </v-list-item>
            <div
              v-if="!myQueries.length"
              class="text-caption text-grey pl-2 py-1"
              style="font-size: 0.9rem"
            >
              저장된 개인 검색 양식이 없습니다.
            </div>
          </v-list>
        </div>

        <v-divider class="my-3" />

        <div class="mb-4">
          <h5 class="text-subtitle-1 mb-2 strong">공용 검색양식</h5>
          <v-list density="compact" nav class="pa-0 bg-transparent">
            <v-list-item
              v-for="q in publicQueries"
              :key="q.pk"
              link
              @click="onQueryClick(q)"
              :active="activeQueryId === q.pk"
              active-color="teal"
              class="rounded-lg mb-1 px-2"
            >
              <template v-slot:prepend>
                <v-icon icon="mdi-filter-variant" size="small" class="mr-2" color="teal" />
              </template>
              <v-list-item-title style="font-size: 1em">{{ q.name }}</v-list-item-title>
            </v-list-item>
            <div
              v-if="!publicQueries.length"
              class="text-caption text-grey pl-2 py-1"
              style="font-size: 0.9rem"
            >
              저장된 공용 검색 양식이 없습니다.
            </div>
          </v-list>
        </div>
      </div>
    </template>
  </ContentBody>
</template>

<style lang="scss" scoped>
.query-item {
  .delete-btn {
    opacity: 0;
    transition: opacity 0.2s;
  }
  &:hover {
    .delete-btn {
      opacity: 1;
    }
  }
}
</style>
