<script setup lang="ts">
import { ref, computed, onBeforeMount, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/_Work/_menu/headermixin3'
import type { ActLogEntryFilter } from '@/store/types/work_logging.ts'
import { useRoute } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project.ts'
import { useIssue } from '@/store/pinia/work_issue.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import UserList from '@/views/_Work/Settings/Users/components/UserList.vue'
import UserView from '@/views/_Work/Settings/Users/components/UserView.vue'
import UserForm from '@/views/_Work/Settings/Users/components/UserForm.vue'

const cBody = ref()

const sideNavCAll = () => cBody.value.toggle()

const accStore = useAccount()
const usersList = computed(() => accStore.usersList)

const workStore = useWork()
const issueProjects = computed(() => workStore.issueProjects)
const fetchIssueProjectList = (payload: any) => workStore.fetchIssueProjectList(payload)

const issueStore = useIssue()
const issueNumByMember = computed(() => issueStore.issueNumByMember)
const fetchIssueByMember = (userId: string) => issueStore.fetchIssueByMember(userId)

const logStore = useLogging()
const fetchActivityLogList = (payload: ActLogEntryFilter) => logStore.fetchActivityLogList(payload)

const route = useRoute()
watch(route, nVal => {
  if (nVal.params.userId) {
    accStore.fetchUser(Number(nVal.params.userId))
    fetchIssueByMember(nVal.params.userId as string)
    fetchIssueProjectList({ member: Number(nVal.params.userId) })
    fetchActivityLogList({ creator: nVal.params.userId as string, limit: 10 })
  }
})

const loading = ref(true)
onBeforeMount(async () => {
  await accStore.fetchUsersList()

  if (route.params.userId) {
    await accStore.fetchUser(Number(route.params.userId))
    await fetchIssueByMember(route.params.userId as string)
    await fetchIssueProjectList({ member: Number(route.params.userId) })
    await fetchActivityLogList({ creator: route.params.userId as string, limit: 10 })
  }
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="pageTitle" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="true">
    <template v-slot:default>
      <UserList v-if="route.name === '사용자'" :user-list="usersList" />

      <UserView
        v-else-if="route.name === '사용자 - 보기'"
        :issue-projects="issueProjects"
        :issue-num="issueNumByMember"
      />

      <UserForm v-else-if="route.name === '사용자 - 생성'" />

      <UserForm v-else-if="route.name === '사용자 - 수정'" />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>
