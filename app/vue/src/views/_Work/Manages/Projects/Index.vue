<script setup lang="ts">
import { computed, onBeforeMount, provide, ref } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { useCompany } from '@/store/pinia/company.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { useInform } from '@/store/pinia/work_inform.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { onBeforeRouteUpdate, useRoute } from 'vue-router'
import type { Company } from '@/store/types/settings'
import type { IssueProject } from '@/store/types/work_project.ts'
import Header from '@/views/_Work/components/Header/Index.vue'
import Loading from '@/components/Loading/Index.vue'

const cBody = ref()
const sideNavCAll = () => cBody.value.toggle()

const route = useRoute()

const routeName = computed(() => (route.name as string) ?? '')
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const headerTitle = computed(() =>
  routeName.value.includes('프로젝트') ? comName.value : currentProject.value?.name,
)

const navMenus = computed(() => (!allReadableProjectsFlat.value.length ? navMenu1 : navMenu2))

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
  const menus = [
    { no: 1, menu: '(개요)' },
    { no: 2, menu: '(회의)' },
    { no: 3, menu: '(업무실행내역)' },
  ]

  const project = currentProject.value

  if (project) {
    const modules = project.module
    if (project.versions?.length) menus.push({ no: 4, menu: '(로드맵)' })
    if (modules?.issue) menus.push({ no: 5, menu: '(업무)' })
    if (modules?.calendar) menus.push({ no: 7, menu: '(캘린더)' })
    if (modules?.news) menus.push({ no: 8, menu: '(공지)' })
    if (modules?.document) menus.push({ no: 9, menu: '(문서)' })
    if (modules?.forum && project.forums?.length) menus.push({ no: 10, menu: '(게시판)' })

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
const currentProject = computed(() => workStore.currentProject as IssueProject)
const allReadableProjectsFlat = computed(() => workStore.allReadableProjectsFlat)

const infStore = useInform()
onBeforeRouteUpdate(async (to, from) => {
  if (to.params.projId) {
    if (to.params.projId !== from.params.projId) {
      await workStore.fetchIssueProject(to.params.projId as string)
    }
  } else {
    if (from.params.projId) {
      await workStore.fetchAllProjectList()
      workStore.removeIssueProject()
      infStore.newsList = []
    }
  }
})

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  if (route.params.projId) await workStore.fetchIssueProject(route.params.projId as string)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header
    :page-title="headerTitle"
    :nav-menu="navMenu"
    :ancestors="currentProject?.ancestors ?? []"
    @side-nav-call="sideNavCAll"
  />

  <router-view v-slot="{ Component }">
    <component
      :is="Component"
      :current-project="currentProject"
      :nav-menu="navMenu"
      :query="route?.query"
      ref="cBody"
    />
  </router-view>
</template>
