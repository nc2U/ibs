<script setup lang="ts">
import { ref, computed, onBeforeMount, watch } from 'vue'
import { pageTitle, navMenu } from '@/views/_Work/_menu/headermixin3'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import { useAccount } from '@/store/pinia/account'
import type { ActLogEntryFilter } from '@/store/types/work_project.ts'
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
const issueNumByMember = computed(() => workStore.issueNumByMember)
const fetchIssueByMember = (userId: string) => workStore.fetchIssueByMember(userId)
const fetchIssueProjectList = (payload: any) => workStore.fetchIssueProjectList(payload)
const fetchActivityLogList = (payload: ActLogEntryFilter) => workStore.fetchActivityLogList(payload)

const route = useRoute()
watch(route, nVal => {
  if (nVal.params.userId) {
    accStore.fetchUser(Number(nVal.params.userId))
    fetchIssueByMember(nVal.params.userId as string)
    fetchIssueProjectList({ member: Number(nVal.params.userId) })
    fetchActivityLogList({ user: nVal.params.userId as string, limit: 10 })
  }
})

onBeforeMount(() => {
  accStore.fetchUsersList()

  if (route.params.userId) {
    accStore.fetchUser(Number(route.params.userId))
    fetchIssueByMember(route.params.userId as string)
    fetchIssueProjectList({ member: Number(route.params.userId) })
    fetchActivityLogList({ user: route.params.userId as string, limit: 10 })
  }
})
</script>

<template>
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
