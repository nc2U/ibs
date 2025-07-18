<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, provide, ref } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { useWork } from '@/store/pinia/work_project.ts'
import { useInform } from '@/store/pinia/work_inform.ts'
import { onBeforeRouteUpdate, useRoute } from 'vue-router'
import type { Company } from '@/store/types/settings'
import type { IssueProject } from '@/store/types/work_project.ts'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'

const cBody = ref()
const sideNavCAll = () => cBody.value.toggle()

const route = useRoute()

const routeName = computed(() => route.name as string)
const company = inject<ComputedRef<Company | null>>('company')
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
  const project = issueProject.value
  if (project?.versions?.length) menus = [...new Set([...menus, ...[{ no: 3, menu: '(로드맵)' }]])]
  if (modules.value?.issue) menus = [...new Set([...menus, ...[{ no: 4, menu: '(업무)' }]])]
  if (modules.value?.time) menus = [...new Set([...menus, ...[{ no: 5, menu: '(소요시간)' }]])]
  if (modules.value?.gantt) menus = [...new Set([...menus, ...[{ no: 6, menu: '(간트차트)' }]])]
  if (modules.value?.calendar) menus = [...new Set([...menus, ...[{ no: 7, menu: '(달력)' }]])]
  if (modules.value?.news) menus = [...new Set([...menus, ...[{ no: 8, menu: '(공지)' }]])]
  if (modules.value?.document) menus = [...new Set([...menus, ...[{ no: 9, menu: '(문서)' }]])]
  if (modules.value?.wiki) menus = [...new Set([...menus, ...[{ no: 10, menu: '(위키)' }]])]
  if (modules.value?.forum && project.forums.length)
    menus = [...new Set([...menus, ...[{ no: 11, menu: '(게시판)' }]])]
  if (modules.value?.file) menus = [...new Set([...menus, ...[{ no: 12, menu: '(파일)' }]])]
  if (modules.value?.repository) menus = [...new Set([...menus, ...[{ no: 13, menu: '(저장소)' }]])]
  if (issueProject.value?.status !== '9') menus = [...menus, ...[{ no: 14, menu: '(설정)' }]]

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

const modules = computed(() => issueProject.value?.module)

const infStore = useInform()
onBeforeRouteUpdate(async to => {
  if (to.params.projId) {
    await workStore.fetchIssueProject(to.params.projId as string)
  } else {
    await workStore.fetchIssueProjectList({ status: '1' })
    workStore.removeIssueProject()
    infStore.newsList = []
  }
})

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await workStore.fetchIssueProjectList({ status: '1' })
  if (route.params.projId) await workStore.fetchIssueProject(route.params.projId as string)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header
    :page-title="headerTitle"
    :nav-menu="navMenu"
    :family-tree="issueProject?.family_tree ?? []"
    @side-nav-call="sideNavCAll"
  />

  <router-view v-slot="{ Component }">
    <component
      :is="Component"
      :issue-project="issueProject"
      :nav-menu="navMenu"
      :query="route?.query"
      ref="cBody"
    />
  </router-view>
</template>
