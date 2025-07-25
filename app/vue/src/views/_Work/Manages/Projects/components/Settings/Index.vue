<script lang="ts" setup>
import Cookies from 'js-cookie'
import { computed, type ComputedRef, inject, onBeforeMount, ref, watch } from 'vue'
import { type IssueProject } from '@/store/types/work_project.ts'
import { type IssueCategory as ICategory } from '@/store/types/work_issue.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useGitRepo } from '@/store/pinia/work_git_repo.ts'
import { useRoute, useRouter } from 'vue-router'
import Loading from '@/components/Loading/Index.vue'
import ProjectForm from '@/views/_Work/Manages/Projects/components/ProjectForm.vue'
import Member from '@/views/_Work/Manages/Projects/components/Settings/components/Member.vue'
import IssueTracking from '@/views/_Work/Manages/Projects/components/Settings/components/IssueTracking.vue'
import Version from '@/views/_Work/Manages/Projects/components/Settings/components/Version.vue'
import IssueCategory from '@/views/_Work/Manages/Projects/components/Settings/components/IssueCategory.vue'
import Repository from '@/views/_Work/Manages/Projects/components/Settings/components/Repository.vue'
import Board from '@/views/_Work/Manages/Projects/components/Settings/components/Board.vue'
import TimeTracking from '@/views/_Work/Manages/Projects/components/Settings/components/TimeTracking.vue'
import CategoryForm from '@/views/_Work/Manages/Projects/components/Settings/category/CategoryForm.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const menu = ref('프로젝트')

const workManager = inject<ComputedRef<boolean>>('workManager')

const [route, router] = [useRoute(), useRouter()]
watch(route, newVal => {
  if (newVal.query?.menu) menu.value = newVal.query.menu as string
})

const initMenu = computed(() => (!!workManager?.value ? '프로젝트' : '버전'))

const settingMenus = computed(() => {
  let menus = [{ no: 4, menu: '버전' }]

  if (!!workManager?.value || my_perms.value?.project_update) {
    menus = [...new Set([...menus, ...[{ no: 1, menu: '프로젝트' }]])]
  }

  if (!!workManager?.value || my_perms.value?.project_member) {
    menus = [...new Set([...menus, ...[{ no: 2, menu: '구성원' }]])]
  }

  if (!!workManager?.value && modules.value?.issue)
    menus = [...new Set([...menus, ...[{ no: 3, menu: '업무추적' }]])]
  if (modules.value?.issue) menus = [...new Set([...menus, ...[{ no: 5, menu: '업무범주' }]])]

  if (!!workManager?.value && modules.value?.time)
    menus = [...new Set([...menus, ...[{ no: 8, menu: '시간추적' }]])]
  if (!!workManager?.value && modules.value?.repository)
    menus = [...new Set([...menus, ...[{ no: 6, menu: '저장소' }]])]
  if (!!workManager?.value && modules.value?.forum)
    menus = [...new Set([...menus, ...[{ no: 7, menu: '게시판' }]])]

  return menus.sort((a, b) => a.no - b.no).map(m => m.menu)
})

const workStore = useWork()
const issueProject = computed<IssueProject | null>(() => workStore.issueProject)
const my_perms = computed(() => (workStore.issueProject as IssueProject)?.my_perms)
const modules = computed(() => issueProject.value?.module)
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
const activityList = computed(() => issueStore.activityList)

const categorySubmit = (payload: ICategory) => {
  if (payload.pk) issueStore.updateCategory(payload)
  else issueStore.createCategory(payload)
  router.push({ name: '(설정)' })
}
const deleteCategory = (pk: number) => issueStore.deleteCategory(pk, issueProject.value?.slug)

const submitActs = (payload: number[]) => {
  const activities = payload.sort((a, b) => a - b)
  workStore.patchIssueProject({
    slug: issueProject.value?.slug as string,
    activities,
    users: [],
    roles: [],
  })
}

const versionFilter = async (payload: { status?: '' | '1' | '2' | '3'; search?: string }) => {
  const { status, search } = payload
  if (route.params.projId) {
    const projId = route.params.projId as string
    await workStore.fetchVersionList({ project: projId, status, search })
  }
}

const gitStore = useGitRepo()
const repositoryList = computed(() => gitStore.repositoryList)

const submitRepo = (payload: any) => {
  if (!payload.project) payload.project = issueProject.value?.pk
  if (!payload.pk) gitStore.createRepo(payload)
  else gitStore.patchRepo(payload)
}
const deleteRepo = (pk: number) => gitStore.deleteRepo(pk, issueProject.value?.pk)

watch(
  () => route.params?.projId,
  async nVal => {
    if (nVal) {
      await workStore.fetchIssueProject(nVal as string)
      await workStore.fetchVersionList({ project: nVal as string })
      await gitStore.fetchRepoList(issueProject.value?.pk ?? '')
    } else {
      workStore.removeIssueProject()
      await workStore.fetchIssueProjectList({ status: '1' })
    }
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  if (route.query.menu) menu.value = route.query.menu as string
  else menu.value = Cookies.get('workSettingMenu') ?? initMenu.value

  await workStore.fetchIssueProjectList({})
  await workStore.fetchRoleList()
  await issueStore.fetchTrackerList()
  await issueStore.fetchActivityList()
  await gitStore.fetchRepoList(issueProject.value?.pk ?? '')

  if (route.params.projId) {
    const projId = route.params.projId as string
    await workStore.fetchIssueProject(projId)
    await workStore.fetchVersionList({ project: projId, status: '1' })
  }
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
          v-if="menu === '버전'"
          :versions="versionList"
          @version-filter="versionFilter"
          @delete-version="deleteVersion"
        />

        <IssueCategory
          v-if="menu === '업무범주'"
          :categories="issueProject?.categories"
          @delete-category="deleteCategory"
        />

        <Repository
          v-if="menu === '저장소'"
          :proj-id="issueProject?.slug as string"
          :repo-list="repositoryList"
          @submit-repo="submitRepo"
          @delete-repo="deleteRepo"
        />

        <Board v-if="menu === '게시판'" :project="issueProject?.pk as number" />

        <TimeTracking
          v-if="menu === '시간추적'"
          :activities="issueProject?.activities"
          :activity-list="activityList"
          @submit-acts="submitActs"
        />
      </template>

      <template v-if="route.name === '(설정) - 범주추가' || route.name === '(설정) - 범주수정'">
        <CategoryForm :member-list="memberList" @category-submit="categorySubmit" />
      </template>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
