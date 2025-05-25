<script lang="ts" setup>
import { computed, inject, onBeforeMount, ref } from 'vue'
import { onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'

const menu = ref<'일반' | '프로젝트'>('일반')

const workManager = inject('workManager', false)

const accStore = useAccount()
const user = computed(() => accStore.user)

const [route, router] = [useRoute(), useRouter()]
onBeforeRouteUpdate(async to => {
  if (to.params.userId) await accStore.fetchUser(Number(to.params.userId))
  else accStore.user = null
})

onBeforeMount(() => {
  if (route.params.userId) accStore.fetchUser(Number(route.params.userId))
  if (route.query.tab) router.replace({ name: '사용자 - 수정', params: { userId: user.value?.pk } })
})
</script>

<template>
  <CRow class="py-2">
    <CCol class="mb-2">
      <span class="h5 mr-2">
        <router-link :to="{ name: '사용자' }">사용자</router-link>
      </span>
      <span class="mr-2">»</span>
      <span class="h5">{{ user ? 'austin1' : '새 사용자' }}</span>
    </CCol>

    <CCol v-if="user && workManager" class="text-right form-text">
      <span class="mr-2">
        <v-icon icon="mdi-account" color="success" size="sm" />
        <router-link :to="{ name: '사용자 - 보기', params: { userId: user.pk } }" class="ml-1">
          사용자 정보
        </router-link>
      </span>
    </CCol>
  </CRow>

  <CRow v-if="user" class="mb-3">
    <CCol>
      <v-tabs v-model="menu" density="compact">
        <v-tab value="일반" variant="tonal"> 일반</v-tab>
        <v-tab value="프로젝트" variant="tonal"> 프로젝트</v-tab>
      </v-tabs>
    </CCol>
  </CRow>
  <CRow v-if="menu === '일반'">
    <CCol>User Form</CCol>
  </CRow>

  <CRow v-if="menu === '프로젝트'">
    <CCol> 프로젝트 탭</CCol>
  </CRow>
</template>
