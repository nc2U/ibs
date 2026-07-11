<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import { useWork } from '@/store/pinia/work_project'
import Loading from '@/components/Loading/Index.vue'

const workStore = useWork()
const loading = ref(true)

onBeforeMount(async () => {
  try {
    // 업무 및 일정 관리에 필수적인 데이터 페치
    await Promise.all([
      workStore.fetchAllProjectList(),
      workStore.fetchMyProjectsList(),
      workStore.fetchRoleList(),
      workStore.fetchPermissionList(),
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
