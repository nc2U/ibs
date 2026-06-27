<script lang="ts" setup>
import Cookies from 'js-cookie'
import { computed, onBeforeMount, ref, watch } from 'vue'
import { type IssueProject } from '@/store/types/work_project.ts'
import { type IssueCategory as ICategory } from '@/store/types/work_issue.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useAccount } from '@/store/pinia/account.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { useRoute, useRouter } from 'vue-router'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ProjectForm from '@/views/_Work/Manages/Projects/components/ProjectForm.vue'
import Member from './components/Member.vue'
import IssueTracking from './components/IssueTracking.vue'
import Version from './components/Version.vue'
import IssueCategory from './components/IssueCategory.vue'
import CategoryForm from './category/CategoryForm.vue'
import Forum from './components/Forum.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const menu = ref('프로젝트')

const { can, PERM } = usePerms()

const accStore = useAccount()
const workManager = computed(() => accStore.workManager)

const canAccessProject = computed(() => {
  if (workManager.value) return true
  return can(PERM.PROJECT_CREATE) || can(PERM.PROJECT_UPDATE) || can(PERM.PROJECT_DELETE)
})

const canAccessIssue = computed(() => {
  if (workManager.value) return true
  return (
    can(PERM.ISSUE_READ) ||
    can(PERM.ISSUE_CREATE) ||
    can(PERM.ISSUE_UPDATE) ||
    can(PERM.ISSUE_DELETE)
  )
})

const canAccessForum = computed(() => {
  if (workManager.value) return true
  return (
    can(PERM.FORUM_READ) ||
    can(PERM.FORUM_CREATE) ||
    can(PERM.FORUM_UPDATE) ||
    can(PERM.FORUM_DELETE)
  )
})

const [route, router] = [useRoute(), useRouter()]
watch(route, newVal => {
  if (newVal.query?.menu) menu.value = newVal.query.menu as string
})

const initMenu = computed(() => settingMenus.value[0] || '')

const settingMenus = computed(() => {
  const menus = []

  // PERM 상수를 기반으로 권한 체크
  if (canAccessProject.value) menus.push({ no: 1, menu: '프로젝트' })
  if (workManager.value || can(PERM.PROJECT_MEMBER)) menus.push({ no: 2, menu: '구성원' })
  if (canAccessIssue.value) menus.push({ no: 3, menu: '업무추적' })
  if (workManager.value || can(PERM.PROJECT_VERSION)) menus.push({ no: 4, menu: '단계' })
  if (workManager.value || can(PERM.ISSUE_CATEGORY_MANAGE)) menus.push({ no: 5, menu: '업무범주' })
  if (canAccessForum.value) menus.push({ no: 7, menu: '게시판' })

  return menus.sort((a, b) => a.no - b.no).map(m => m.menu)
})

const workStore = useWork()
const issueProject = computed<IssueProject | null>(() => workStore.issueProject)
const versionList = computed(() => workStore.versionList)
const memberList = computed(() =>
  (
    (issueProject.value
      ? issueProject.value.all_members
      : [...new Map(workStore.memberList.map(m => [m.user.pk, m])).values()]) as any[]
  ).map(m => m.user),
)

const deleteVersion = (pk: number) => workStore.deleteVersion(pk, issueProject.value?.slug)

const issueStore = useIssue()

const categorySubmit = (payload: ICategory) => {
  if (payload.pk) issueStore.updateCategory(payload)
  else issueStore.createCategory(payload)
  router.push({ name: '(설정)' })
}
const deleteCategory = (pk: number) => issueStore.deleteCategory(pk, issueProject.value?.slug)

const versionFilter = async (payload: { status?: '' | '1' | '2' | '3'; search?: string }) => {
  const { status, search } = payload
  if (route.params.projId) {
    const projId = route.params.projId as string
    await workStore.fetchVersionList({ project: projId, status, search })
  }
}

watch(
  () => route.params?.projId,
  async nVal => {
    if (nVal) {
      await workStore.fetchIssueProject(nVal as string)
      await workStore.fetchVersionList({ project: nVal as string })
    } else {
      workStore.removeIssueProject()
      await workStore.fetchIssueProjectList({ status: '1' })
    }
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  await workStore.fetchIssueProjectList({})
  await workStore.fetchRoleList()
  await issueStore.fetchTrackerList()

  if (route.params.projId) {
    const projId = route.params.projId as string
    await workStore.fetchIssueProject(projId)
    await workStore.fetchVersionList({ project: projId, status: '' })
  }

  // 메뉴 초기화 로직 보완
  const cookieMenu = Cookies.get('workSettingMenu')
  if (route.query.menu) menu.value = route.query.menu as string
  else if (cookieMenu && settingMenus.value.includes(cookieMenu)) menu.value = cookieMenu
  else menu.value = initMenu.value

  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody" :aside="false">
    <template v-slot:default>
      <template v-if="route.name === '(설정)'">
        <CRow class="py-2">
          <CCol>
            <h5>설정</h5>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol>
            <v-tabs v-model="menu" density="compact">
              <v-tab
                v-for="m in settingMenus"
                :value="m"
                :key="m"
                variant="tonal"
                :active="menu === m"
                @click="Cookies.set('workSettingMenu', m)"
              >
                {{ m }}
              </v-tab>
            </v-tabs>
          </CCol>
        </CRow>

        <ProjectForm v-if="menu === '프로젝트'" :project="issueProject" />

        <Member v-if="menu === '구성원'" />

        <IssueTracking v-if="menu === '업무추적'" />

        <Version
          v-if="menu === '단계'"
          :versions="versionList"
          @version-filter="versionFilter"
          @delete-version="deleteVersion"
        />

        <IssueCategory
          v-if="menu === '업무범주'"
          :categories="issueProject?.categories"
          @delete-category="deleteCategory"
        />

        <Forum v-if="menu === '게시판'" :project="issueProject?.pk as number" />
      </template>

      <template v-if="route.name === '(설정) - 범주추가' || route.name === '(설정) - 범주수정'">
        <CategoryForm :member-list="memberList" @category-submit="categorySubmit" />
      </template>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
