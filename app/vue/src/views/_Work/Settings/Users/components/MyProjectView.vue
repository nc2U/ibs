<script lang="ts" setup>
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import UserProjects from '@/views/_Work/Settings/Users/components/atomicViews/UserProjects.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
</script>

<template>
  <CRow class="py-2">
    <CCol class="mb-2">
      <span class="h5 me-2"> 내 프로젝트 목록 </span>
    </CCol>

    <CCol class="text-end form-text">
      <span class="me-2">
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
    <UserProjects v-if="userInfo?.pk" :user-pk="userInfo.pk" />
  </CRow>
</template>
