<script setup lang="ts">
import { ref, computed, onBeforeMount, provide, inject, type ComputedRef, watch } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { dateFormat } from '@/utils/baseMixins'
import { useWork } from '@/store/pinia/work'
import { onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import type { Company } from '@/store/types/settings'
import type { ActLogEntryFilter, IssueProject } from '@/store/types/work'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ProjectList from '@/views/_Work/Manages/Projects/components/ProjectList.vue'
import ProjectForm from '@/views/_Work/Manages/Projects/components/ProjectForm.vue'
import Overview from '@/views/_Work/Manages/Projects/components/Overview/Index.vue'
import Activity from '@/views/_Work/Manages/Projects/components/Activity/Index.vue'
import Roadmap from '@/views/_Work/Manages/Projects/components/Roadmap/Index.vue'
import Issues from '@/views/_Work/Manages/Projects/components/Issues/Index.vue'
import SpentTime from '@/views/_Work/Manages/Projects/components/SpentTime/Index.vue'
import Gantt from '@/views/_Work/Manages/Projects/components/Gantt/Index.vue'
import Calendar from '@/views/_Work/Manages/Projects/components/Calendar/Index.vue'
import News from '@/views/_Work/Manages/Projects/components/News/Index.vue'
import Documents from '@/views/_Work/Manages/Projects/components/Documents/Index.vue'
import Wiki from '@/views/_Work/Manages/Projects/components/Wiki/Index.vue'
import Forums from '@/views/_Work/Manages/Projects/components/Forums/Index.vue'
import Files from '@/views/_Work/Manages/Projects/components/Files/Index.vue'
import Repository from '@/views/_Work/Manages/Projects/components/Repository/Index.vue'
import Settings from '@/views/_Work/Manages/Projects/components/Settings/Index.vue'
import AsideActivity from '@/views/_Work/Manages/Activity/components/aside/AsideActivity.vue'
import AsideIssue from '@/views/_Work/Manages/Issues/components/aside/AsideIssue.vue'

const cBody = ref()
const aside = ref(true)

const asideVisible = (visible: boolean) => (aside.value = visible)

const [route, router] = [useRoute(), useRouter()]

const routeName = computed(() => route.name as string)
const company = inject<ComputedRef<Company>>('company')
const comName = computed(() => company?.value?.name)
const headerTitle = computed(() =>
  routeName.value.includes('프로젝트') ? comName.value : issueProject.value?.name,
)

const navMenus = computed(() => (!issueProjects.value.length ? navMenu1 : navMenu2))

const projectNavMenus = computed(() => {
  let menus = [
    { no: 1, menu: '(개요)' },
    { no: 2, menu: '(작업내역)' },
  ]
  if (issueProject.value?.versions?.length)
    menus = [...new Set([...menus, ...[{ no: 3, menu: '(로드맵)' }]])]
  if (modules.value?.issue) menus = [...new Set([...menus, ...[{ no: 4, menu: '(업무)' }]])]
  if (modules.value?.time) menus = [...new Set([...menus, ...[{ no: 5, menu: '(소요시간)' }]])]
  if (modules.value?.gantt) menus = [...new Set([...menus, ...[{ no: 6, menu: '(간트차트)' }]])]
  if (modules.value?.calendar) menus = [...new Set([...menus, ...[{ no: 7, menu: '(달력)' }]])]
  if (modules.value?.news) menus = [...new Set([...menus, ...[{ no: 8, menu: '(공지)' }]])]
  if (modules.value?.document) menus = [...new Set([...menus, ...[{ no: 9, menu: '(문서)' }]])]
  if (modules.value?.wiki) menus = [...new Set([...menus, ...[{ no: 10, menu: '(위키)' }]])]
  if (modules.value?.file) menus = [...new Set([...menus, ...[{ no: 11, menu: '(파일)' }]])]
  if (issueProject.value.status !== '9') menus = [...menus, ...[{ no: 12, menu: '(설정)' }]]

  return menus.sort((a, b) => a.no - b.no).map(m => m.menu)
})

const navMenu = computed(() =>
  routeName.value.includes('프로젝트') ? navMenus.value : projectNavMenus.value,
)

const sideNavCAll = () => cBody.value.toggle()

const workStore = useWork()
const issueProject = computed(() => workStore.issueProject as IssueProject)
provide('iProject', issueProject)
const issueProjects = computed(() => workStore.issueProjects)
const allProjects = computed(() => workStore.AllIssueProjects)
const getRoles = computed(() => workStore.getRoles)
const getTrackers = computed(() => workStore.getTrackers)
const getActivities = computed(() => workStore.getActivities)

const modules = computed(() => issueProject.value?.module)

const issue = computed(() => workStore.issue)

const onSubmit = (payload: any) => {
  payload.company = company?.value.pk
  workStore.createIssueProject(payload)
  setTimeout(() => {
    router.push({
      name: '(설정)',
      params: { projId: issueProject.value?.slug },
    })
  }, 500)
}

const filteringProject = (payload: any) => {
  console.log(payload)
  workStore.fetchIssueProjectList(payload)
}

const toDate = ref(new Date())
const fromDate = computed(() => new Date(toDate.value.getTime() - 9 * 24 * 60 * 60 * 1000))

const activityFilter = ref<ActLogEntryFilter>({
  project: '',
  project__search: '',
  to_act_date: dateFormat(toDate.value),
  from_act_date: dateFormat(fromDate.value),
  user: '',
  sort: [],
})

const toMove = (date: Date) => {
  toDate.value = date
  activityFilter.value.to_act_date = dateFormat(date)
  activityFilter.value.from_act_date = dateFormat(
    new Date(date.getTime() - 9 * 24 * 60 * 60 * 1000),
  )
  console.log(dateFormat(new Date(date.getTime() - 9 * 24 * 60 * 60 * 1000)))
  workStore.fetchActivityLogList(activityFilter.value)
}

const filterActivity = (payload: ActLogEntryFilter) => {
  console.log(payload)
  if (payload.to_act_date) toDate.value = new Date(payload.to_act_date)
  activityFilter.value.project = payload.project ?? ''
  activityFilter.value.project__search = payload.project__search ?? ''
  activityFilter.value.user = payload.user ?? ''
  activityFilter.value.sort = payload.sort
  workStore.fetchActivityLogList(payload)
}

watch(
  () => route.params,
  nVal => {
    if (nVal && nVal.projId) {
      activityFilter.value.project = nVal.projId as string
      workStore.fetchNewsList({ project: nVal.projId as string })
    }
  },
  { deep: true },
)

onBeforeRouteUpdate(async to => {
  if (to.params.projId) {
    await workStore.fetchIssueProject(to.params.projId as string)
    await workStore.fetchNewsList({ project: route.params.projId as string })
  } else {
    await workStore.fetchIssueProjectList({ status: '1' })
    workStore.removeIssueProject()
    workStore.newsList = []
  }
})

onBeforeMount(async () => {
  await workStore.fetchIssueProjectList({ status: '1' })
  await workStore.fetchAllIssueProjectList()
  await workStore.fetchRoleList()
  await workStore.fetchTrackerList()
  await workStore.fetchActivityList()
  if (route.params.projId) {
    activityFilter.value.project = route.params.projId as string
    await workStore.fetchIssueProject(route.params.projId as string)
    await workStore.fetchNewsList({ project: route.params.projId as string })
  }
})
</script>

<template>
  <Header
    :page-title="headerTitle"
    :nav-menu="navMenu"
    :family-tree="issueProject?.family_tree ?? []"
    @side-nav-call="sideNavCAll"
  />
  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="aside">
    <template v-slot:default>
      <ProjectList
        v-if="routeName === '프로젝트'"
        :project-list="issueProjects"
        :all-projects="allProjects"
        @aside-visible="asideVisible"
        @filter-submit="filteringProject"
      />

      <ProjectForm
        v-if="routeName === '프로젝트 - 추가'"
        title="새 프로젝트"
        :all-projects="allProjects"
        :all-roles="getRoles"
        :all-trackers="getTrackers"
        :get-activities="getActivities"
        @aside-visible="asideVisible"
        @on-submit="onSubmit"
      />

      <Overview v-if="routeName === '(개요)'" @aside-visible="asideVisible" />

      <Activity
        v-if="routeName === '(작업내역)'"
        :to-date="toDate"
        :activity-filter="activityFilter"
        @to-back="toMove"
        @to-next="toMove"
        @aside-visible="asideVisible"
      />

      <Roadmap v-if="routeName.includes('(로드맵)')" @aside-visible="asideVisible" />

      <Issues v-if="routeName.includes('(업무)')" @aside-visible="asideVisible" />

      <SpentTime v-if="routeName.includes('(소요시간)')" @aside-visible="asideVisible" />

      <Gantt v-if="routeName === '(간트차트)'" @aside-visible="asideVisible" />

      <Calendar v-if="routeName === '(달력)'" @aside-visible="asideVisible" />

      <News v-if="routeName === '(공지)'" @aside-visible="asideVisible" />

      <Documents v-if="routeName === '(문서)'" @aside-visible="asideVisible" />

      <Wiki v-if="routeName.includes('(위키)')" @aside-visible="asideVisible" />

      <Forums v-if="routeName === '(게시판)'" @aside-visible="asideVisible" />

      <Files v-if="routeName === '(파일)'" @aside-visible="asideVisible" />

      <Repository v-if="routeName === '(저장소)'" @aside-visible="asideVisible" />

      <Settings v-if="routeName.includes('(설정)')" @aside-visible="asideVisible" />
    </template>

    <template v-slot:aside>
      <AsideActivity
        v-if="routeName === '(작업내역)'"
        :to-date="toDate"
        :has-subs="!!issueProject?.sub_projects?.length"
        @filter-activity="filterActivity"
      />

      <AsideIssue
        v-if="routeName === '(업무)' || routeName === '(업무) - 보기'"
        :issuePk="issue?.pk as number"
        :watchers="issue?.watchers"
      />
    </template>
  </ContentBody>
</template>
