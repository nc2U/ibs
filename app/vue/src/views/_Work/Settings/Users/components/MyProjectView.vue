<script lang="ts" setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import UserProjects from '@/views/_Work/Settings/Users/components/atomicViews/UserProjects.vue'

const router = useRouter()
const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const usernameVal = computed(() => userInfo.value?.username || '')
</script>

<template>
  <CRow class="py-2">
    <CCol class="mb-2">
      <span class="h5 mr-2"> 내 프로젝트 목록 </span>
    </CCol>
  </CRow>

  <CRow>
    <UserProjects />
  </CRow>
</template>
