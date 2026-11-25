<script setup lang="ts">
import { ref, computed, onBeforeMount, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/_Work/_menu/headermixin2'
import type { ActLogEntryFilter } from '@/store/types/work_logging'
import { useRoute } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project'
import { useIssue } from '@/store/pinia/work_issue'
import { useLogging } from '@/store/pinia/work_logging'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import UserList from '@/views/_Work/Settings/Users/components/UserList.vue'
import UserDetail from './components/UserDetail.vue'
import AdminUserManage from './components/AdminUserManage.vue'
import MyAccountForm from './components/MyAccountForm.vue'
import MyPasswordForm from './components/MyPasswordForm.vue'
import MyProjectView from '@/views/_Work/Settings/Users/components/MyProjectView.vue'
import MyScrapView from './components/MyScrapView.vue'
import MyActivityView from './components/MyActivityView.vue'

const cBody = ref<InstanceType<typeof ContentBody> | null>(null)

const sideNavCAll = () => cBody.value?.toggle()

const component = computed(() => {
  if (route.name === '사용자') return '목록보기'
  if (route.name === '사용자 - 보기') return '상세보기'
  if (route.name === '사용자 - 생성' || route.name === '사용자 - 수정') return '관리자 메뉴'
  if (route.name === '사용자 - 내 계정') return '내 계정'
  if (route.name === '사용자 - 비밀번호 변경') return '비밀번호 변경'
  if (route.name === '사용자 - 프로젝트 보기') return '프로젝트 보기'
  if (route.name === '사용자 - 내 스크랩') return '내 스크랩'
  if (route.name === '사용자 - 내 활동') return '내 활동'
  return '목록'
})

const accStore = useAccount()
const usersList = computed(() => accStore.usersList)

const workStore = useWork()
const projectResultsTree = computed(() => workStore.projectResultsTree)
const fetchIssueProjectList = (payload: any) => workStore.fetchIssueProjectList(payload)

const issueStore = useIssue()
const issueNumByMember = computed(() => issueStore.issueNumByMember)
const fetchIssueByMember = (userId: string) => issueStore.fetchIssueByMember(userId)

const logStore = useLogging()
const fetchActivityLogList = (payload: ActLogEntryFilter) => logStore.fetchActivityLogList(payload)

const route = useRoute()
const loading = ref(true)

const loadRouteData = async (name: unknown, rawUserId: unknown) => {
  const userId = rawUserId ? Number(rawUserId) : null
  if (name === '사용자 - 보기' && userId && !Number.isNaN(userId)) {
    loading.value = true
    accStore.removeUser()
    logStore.activityLogList = []
    workStore.clearProjectResults()
    try {
      await Promise.all([
        accStore.fetchUser(userId),
        fetchIssueByMember(String(userId)),
        fetchIssueProjectList({ member: userId }),
        fetchActivityLogList({ creator: String(userId), limit: 10 }),
      ])
    } catch (err) {
      console.error('Failed to load user settings data:', err)
    } finally {
      loading.value = false
    }
  } else if (name === '사용자 - 수정' && userId && !Number.isNaN(userId)) {
    loading.value = true
    try {
      await accStore.fetchUser(userId)
    } catch (err) {
      console.error('Failed to load user data:', err)
    } finally {
      loading.value = false
    }
  } else if (name === '사용자 - 생성') {
    accStore.removeUser()
    loading.value = false
  } else {
    loading.value = false
  }
}

watch([() => route.name, () => route.params.userId], ([name, userId]) => {
  loadRouteData(name, userId)
})

onBeforeMount(async () => {
  await loadRouteData(route.name, route.params.userId)
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="pageTitle" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="false">
    <template v-slot:default>
      <UserList v-if="component === '목록보기'" :user-list="usersList" />

      <UserDetail
        v-else-if="component === '상세보기'"
        :project-results="projectResultsTree"
        :issue-num="issueNumByMember"
      />

      <AdminUserManage v-else-if="component === '관리자 메뉴'" />

      <MyAccountForm v-else-if="component === '내 계정'" />
      <MyPasswordForm v-else-if="component === '비밀번호 변경'" />
      <MyProjectView v-else-if="component === '프로젝트 보기'" />
      <MyScrapView v-else-if="component === '내 스크랩'" />
      <MyActivityView v-else-if="component === '내 활동'" />
    </template>
  </ContentBody>
</template>
