<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { onBeforeRouteUpdate, useRoute } from 'vue-router'
import { useAccount } from '@/store/pinia/account.ts'
import type { User } from '@/store/types/accounts.ts'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import UserForm from './atomicViews/UserForm.vue'
import UserProjects from './atomicViews/UserProjects.vue'

const menu = ref<'일반' | '프로젝트'>('일반')

const accStore = useAccount()
const user = computed<User | null>(() => accStore.user)

const route = useRoute()

onBeforeMount(async () => {
  const savedTab = localStorage.getItem('admin-user-menu-tab') as '일반' | '프로젝트' | null
  if (savedTab === '일반' || savedTab === '프로젝트') {
    menu.value = savedTab
  }

  if (route.params.userId) await accStore.fetchUser(Number(route.params.userId))
  else accStore.user = null
})

onBeforeRouteUpdate(async to => {
  if (to.params.userId) await accStore.fetchUser(Number(to.params.userId))
  else accStore.user = null
})

watch(menu, newVal => {
  localStorage.setItem('admin-user-menu-tab', newVal)
})
</script>

<template>
  <CRow class="py-2">
    <CCol class="mb-2">
      <span class="h5 mr-2">
        <router-link :to="{ name: '사용자' }">사용자</router-link>
      </span>
      <span class="mr-2">»</span>
      <span class="h5">{{ user?.pk ? user.username : '새 사용자' }}</span>
    </CCol>

    <CCol v-if="user?.pk" class="text-right form-text">
      <span class="mr-2">
        <TextButton
          name="사용자 정보"
          icon="mdi-account"
          :to="{ name: '사용자 - 보기', params: { userId: user.pk } }"
        />
      </span>
    </CCol>
  </CRow>

  <!-- Edit Mode Tabs -->
  <CRow v-if="user?.pk" class="mb-3">
    <CCol>
      <v-tabs v-model="menu" density="compact">
        <v-tab value="일반" variant="tonal"> 일반</v-tab>
        <v-tab value="프로젝트" variant="tonal"> 프로젝트</v-tab>
      </v-tabs>
    </CCol>
  </CRow>

  <CRow v-if="menu === '일반'">
    <UserForm :user="user" />
  </CRow>

  <CRow v-else>
    <UserProjects v-if="menu === '프로젝트'" />
  </CRow>
</template>
