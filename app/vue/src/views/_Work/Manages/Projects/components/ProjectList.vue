<script lang="ts" setup>
import {
  computed,
  type ComputedRef,
  inject,
  onBeforeMount,
  onBeforeUnmount,
  onMounted,
  type PropType,
  ref,
} from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work.ts'
import type { IssueProject, ProjectFilter } from '@/store/types/work'
import SearchList from './SearchList.vue'
import ProjectCard from './ProjectCard.vue'
import NoData from '@/views/_Work/components/NoData.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const emit = defineEmits(['aside-visible'])

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const workManager = inject<ComputedRef<boolean>>('workManager')

const workStore = useWork()
const projectList = computed<IssueProject[]>(() => workStore.issueProjects)
const allProjects = computed(() => workStore.AllIssueProjects)

const filterSubmit = (payload: ProjectFilter) => workStore.fetchIssueProjectList(payload)

const route = useRoute()

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
onBeforeMount(() => emit('aside-visible', true))
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <!--      <Overview v-if="routeName === '(개요)'" @aside-visible="asideVisible" />-->

      <!--      <Activity-->
      <!--        v-if="routeName === '(작업내역)'"-->
      <!--        :to-date="toDate"-->
      <!--        :activity-filter="activityFilter"-->
      <!--        @to-back="toMove"-->
      <!--        @to-next="toMove"-->
      <!--        @aside-visible="asideVisible"-->
      <!--      />-->

      <!--      <Roadmap v-if="routeName.includes('(로드맵)')" @aside-visible="asideVisible" />-->
      <!--      <Issues v-if="routeName.includes('(업무)')" @aside-visible="asideVisible" />-->
      <!--      <SpentTime v-if="routeName.includes('(소요시간)')" @aside-visible="asideVisible" />-->
      <!--      <Gantt v-if="routeName.includes('(간트차트)')" @aside-visible="asideVisible" />-->
      <!--      <Calendar v-if="routeName.includes('(달력)')" @aside-visible="asideVisible" />-->
      <!--      <News v-if="routeName.includes('(공지)')" @aside-visible="asideVisible" />-->
      <!--      <Documents v-if="routeName.includes('(문서)')" @aside-visible="asideVisible" />-->
      <!--      <Wiki v-if="routeName.includes('(위키)')" @aside-visible="asideVisible" />-->
      <!--      <Forums v-if="routeName.includes('(게시판)')" @aside-visible="asideVisible" />-->
      <!--      <Files v-if="routeName.includes('(파일)')" @aside-visible="asideVisible" />-->
      <!--      <Repository v-if="routeName.includes('(저장소)')" @aside-visible="asideVisible" />-->
      <!--      <Settings v-if="routeName.includes('(설정)')" @aside-visible="asideVisible" />-->

      <CRow class="py-2">
        <CCol>
          <h5>프로젝트</h5>
        </CCol>

        <CCol v-if="workManager" class="text-right form-text">
          <span v-show="route.name !== '프로젝트 - 추가'" class="mr-2">
            <v-icon icon="mdi-plus-circle" color="success" size="sm" />
            <router-link :to="{ name: '프로젝트 - 추가' }" class="ml-1">새 프로젝트</router-link>
          </span>
          <span>
            <v-icon icon="mdi-cog" color="secondary" size="sm" />
            <router-link :to="{ name: '(프로젝트)' }" class="ml-1">관리</router-link>
          </span>
        </CCol>
      </CRow>

      <SearchList :all-projects="allProjects" @filter-submit="filterSubmit" />

      <NoData v-if="!projectList.length" />

      <CRow v-else>
        <CCol v-if="breakpoint === 'sm'">
          <template v-for="proj in projectList" :key="proj.pk">
            <ProjectCard :project="proj" />
          </template>
        </CCol>

        <template v-else-if="breakpoint === 'md'">
          <CCol sm="6">
            <template v-for="(proj, i) in projectList" :key="proj.pk">
              <ProjectCard v-if="(i + 1) % 2 == 1" :project="proj" />
            </template>
          </CCol>
          <CCol sm="6">
            <template v-for="(proj, i) in projectList" :key="proj.pk">
              <ProjectCard v-if="(i + 1) % 2 == 0" :project="proj" />
            </template>
          </CCol>
        </template>

        <template v-else-if="breakpoint === 'lg'">
          <CCol sm="4">
            <template v-for="(proj, i) in projectList" :key="proj.pk">
              <ProjectCard v-if="(i + 1) % 3 == 1" :project="proj" />
            </template>
          </CCol>
          <CCol sm="4">
            <template v-for="(proj, i) in projectList" :key="proj.pk">
              <ProjectCard v-if="(i + 1) % 3 == 2" :project="proj" />
            </template>
          </CCol>
          <CCol sm="4">
            <template v-for="(proj, i) in projectList" :key="proj.pk">
              <ProjectCard v-if="(i + 1) % 3 == 0" :project="proj" />
            </template>
          </CCol>
        </template>

        <template v-else>
          <CCol sm="3">
            <template v-for="(proj, i) in projectList" :key="proj.pk">
              <ProjectCard v-if="(i + 1) % 4 == 1" :project="proj" />
            </template>
          </CCol>
          <CCol sm="3">
            <template v-for="(proj, i) in projectList" :key="proj.pk">
              <ProjectCard v-if="(i + 1) % 4 == 2" :project="proj" />
            </template>
          </CCol>
          <CCol sm="3">
            <template v-for="(proj, i) in projectList" :key="proj.pk">
              <ProjectCard v-if="(i + 1) % 4 == 3" :project="proj" />
            </template>
          </CCol>
          <CCol sm="3">
            <template v-for="(proj, i) in projectList" :key="proj.pk">
              <ProjectCard v-if="(i + 1) % 4 == 0" :project="proj" />
            </template>
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
