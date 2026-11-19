<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { useWork } from '@/store/pinia/work_project'
import { useAccount } from '@/store/pinia/account'
import Loading from '@/components/Loading/Index.vue'

const workStore = useWork()
const accStore = useAccount()
const loading = ref(true)

onBeforeMount(async () => {
  try {
    // 이전 워크스페이스 컨텍스트 잔류 방지
    workStore.removeIssueProject()
    // 설정 및 권한 관리에 필수적인 데이터 페치
    await Promise.all([
      workStore.fetchAllProjectList(),
      workStore.fetchRoleList(),
      workStore.fetchGroupedPermissions(),
      accStore.fetchUsersList('all'),
    ])
  } catch (error) {
    console.error('Failed to load settings work configurations', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <Loading v-model:active="loading" />
  <router-view v-if="!loading" />
</template>
