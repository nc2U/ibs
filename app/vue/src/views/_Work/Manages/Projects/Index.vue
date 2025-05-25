<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, provide, ref, watch } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { dateFormat } from '@/utils/baseMixins'
import { useWork } from '@/store/pinia/work'
import { onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import type { Company } from '@/store/types/settings'
import type { ActLogEntryFilter, Issue, IssueProject } from '@/store/types/work'
import Header from '@/views/_Work/components/Header/Index.vue'

const cBody = ref()
const sideNavCAll = () => cBody.value.toggle()

const [route, router] = [useRoute(), useRouter()]

const routeName = computed(() => route.name as string)
const companyInject = inject<ComputedRef<Company>>('company')
const company = computed(() => companyInject?.value.pk ?? undefined)
const comName = computed(() => companyInject?.value?.name)
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
  if (modules.value?.repository) menus = [...new Set([...menus, ...[{ no: 12, menu: '(저장소)' }]])]
  if (issueProject.value?.status !== '9') menus = [...menus, ...[{ no: 13, menu: '(설정)' }]]

  return menus.sort((a, b) => a.no - b.no).map(m => m.menu)
})

const navMenu = computed(() =>
  routeName.value.includes('프로젝트') ? navMenus.value : projectNavMenus.value,
)

provide('navMenu', navMenu)
provide('query', route?.query)

const workStore = useWork()
const issueProject = computed(() => workStore.issueProject as IssueProject)
provide('iProject', issueProject)
const issueProjects = computed(() => workStore.issueProjects)
const allProjects = computed(() => workStore.AllIssueProjects)

const modules = computed(() => issueProject.value?.module)

const issue = computed<Issue | null>(() => workStore.issue)

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

  <router-view v-slot="{ Component }">
    <component :is="Component" :nav-menu="navMenu" :query="route?.query" ref="cBody" />
  </router-view>
</template>
