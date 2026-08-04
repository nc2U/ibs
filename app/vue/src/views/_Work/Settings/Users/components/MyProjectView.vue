<script lang="ts" setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import UserProjects from '@/views/_Work/Settings/Users/components/atomicViews/UserProjects.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

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

    <CCol class="text-right form-text">
      <span class="mr-2">
        <TextButton
          name="내 계정"
          :to="{ name: '사용자 - 내 계정' }"
          icon="mdi-pencil"
          icon-color="amber"
        />
      </span>
    </CCol>
  </CRow>

  <CRow>
    <UserProjects :user-pk="userInfo?.pk as number" />
  </CRow>
</template>
