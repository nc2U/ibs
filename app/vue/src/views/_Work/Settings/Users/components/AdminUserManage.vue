<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import type { User } from '@/store/types/accounts'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'
import UserForm from './atomicViews/UserForm.vue'
import UserProjects from './atomicViews/UserProjects.vue'

const menu = ref<'일반' | '워크스페이스'>('일반')

const accStore = useAccount()
const user = computed<User | null>(() => accStore.user)

const route = useRoute()

watch(
  () => route.params.userId,
  async rawId => {
    if (rawId) {
      const uid = Number(rawId)
      const savedTab = localStorage.getItem('admin-user-menu-tab') as
        | '일반'
        | '워크스페이스'
        | null
      menu.value = savedTab === '일반' || savedTab === '워크스페이스' ? savedTab : '일반'
      if (accStore.user?.pk !== uid) {
        await accStore.fetchUser(uid)
      }
    } else {
      accStore.removeUser()
      menu.value = '일반'
    }
  },
  { immediate: true },
)

watch(menu, newVal => {
  if (user.value?.pk) {
    localStorage.setItem('admin-user-menu-tab', newVal)
  }
})
</script>

<template>
  <CRow class="py-2">
    <CCol class="mb-2">
      <span class="h5 me-2">
        <router-link :to="{ name: '사용자' }">사용자</router-link>
      </span>
      <span class="me-2">»</span>
      <span class="h5">{{ user?.pk ? user.username : '새 사용자' }}</span>
    </CCol>

    <CCol v-if="user?.pk" class="text-end form-text">
      <span class="me-2">
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
        <v-tab value="워크스페이스" variant="tonal"> 워크스페이스</v-tab>
      </v-tabs>
    </CCol>
  </CRow>

  <CRow v-if="menu === '일반' || !user?.pk">
    <UserForm :user="user" />
  </CRow>

  <CRow v-else>
    <UserProjects v-if="menu === '워크스페이스' && user?.pk" :user-pk="user.pk" />
  </CRow>
</template>
