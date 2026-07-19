<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { useWork } from '@/store/pinia/work_project'
import { useAccount } from '@/store/pinia/account'
import { useIssue } from '@/store/pinia/work_issue'
import Loading from '@/components/Loading/Index.vue'

const workStore = useWork()
const accStore = useAccount()
const issueStore = useIssue()
const loading = ref(true)

onBeforeMount(async () => {
  try {
    // 업무 및 일정 관리에 필수적인 공통/메타 데이터 전역 페치
    await Promise.all([
      workStore.fetchAllProjectList(),
      workStore.fetchMyProjectsList(),
      workStore.fetchRoleList(),
      workStore.fetchPermissionList(),
      workStore.fetchVersionList(),
      issueStore.fetchTrackerList(),
      issueStore.fetchStatusList(),
      issueStore.fetchPriorityList(),
      accStore.fetchUsersList(),
    ])
  } catch (error) {
    console.error('Failed to load manages work configurations', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <Loading v-model:active="loading" />
  <router-view />
</template>
