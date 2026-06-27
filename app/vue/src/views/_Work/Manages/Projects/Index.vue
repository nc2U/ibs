<script setup lang="ts">
import { computed, onBeforeMount, provide, ref } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { useCompany } from '@/store/pinia/company.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { useInform } from '@/store/pinia/work_inform.ts'
import { onBeforeRouteUpdate, useRoute } from 'vue-router'
import type { Company } from '@/store/types/settings'
import type { IssueProject } from '@/store/types/work_project.ts'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useAccount } from '@/store/pinia/account.ts'

const cBody = ref()
const sideNavCAll = () => cBody.value.toggle()

const route = useRoute()

const routeName = computed(() => (route.name as string) ?? '')
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const headerTitle = computed(() =>
  routeName.value.includes('프로젝트') ? comName.value : issueProject.value?.name,
)

const navMenus = computed(() => (!issueProjects.value.length ? navMenu1 : navMenu2))

const { can, PERM } = usePerms()
const accStore = useAccount()
const workManager = computed(() => accStore.workManager)
const canAccessSetting = computed(
  () =>
    !!workManager.value ||
    can(PERM.PROJECT_CREATE) ||
    can(PERM.PROJECT_UPDATE) ||
    can(PERM.PROJECT_DELETE) ||
    can(PERM.PROJECT_MEMBER) ||
    can(PERM.ISSUE_READ) ||
    can(PERM.ISSUE_CREATE) ||
    can(PERM.ISSUE_UPDATE) ||
    can(PERM.ISSUE_DELETE) ||
    can(PERM.PROJECT_VERSION) ||
    can(PERM.ISSUE_CATEGORY_MANAGE) ||
    can(PERM.FORUM_READ) ||
    can(PERM.FORUM_CREATE) ||
    can(PERM.FORUM_UPDATE) ||
    can(PERM.FORUM_DELETE),
)

const projectNavMenus = computed(() => {
  const project = issueProject.value
  const menus = [
    { no: 1, menu: '(개요)' },
    { no: 2, menu: '(회의)' },
    { no: 3, menu: '(실행기록)' },
  ]

  if (project) {
    const mods = project.module
    if (project.versions?.length) menus.push({ no: 4, menu: '(추진현황)' })
    if (mods?.issue) menus.push({ no: 5, menu: '(업무)' })
    if (mods?.calendar) menus.push({ no: 7, menu: '(달력)' })
    if (mods?.news) menus.push({ no: 8, menu: '(공지)' })
    if (mods?.document) menus.push({ no: 9, menu: '(문서)' })
    if (mods?.forum && project.forums?.length) menus.push({ no: 10, menu: '(게시판)' })

    // 권한 검사: 프로젝트 설정에 접근 가능한 메뉴가 하나라도 있는지 확인
    if (project.status !== '9' && canAccessSetting.value) menus.push({ no: 99, menu: '(설정)' })
  }

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
