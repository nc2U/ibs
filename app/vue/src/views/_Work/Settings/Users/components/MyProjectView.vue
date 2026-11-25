<script lang="ts" setup>
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import UserProjects from '@/views/_Work/Settings/Users/components/atomicViews/UserProjects.vue'
import MyMenuLinks from '@/views/_Work/Settings/Users/components/atomicViews/MyMenuLinks.vue'

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
</script>

<template>
  <CRow class="py-2 align-items-center">
    <CCol class="mb-2">
      <span class="h5 me-2"> 내 워크스페이스 목록 </span>
    </CCol>

    <MyMenuLinks current="project-view" />
  </CRow>

  <CRow>
    <UserProjects v-if="userInfo?.pk" :user-pk="userInfo.pk" />
  </CRow>
</template>
