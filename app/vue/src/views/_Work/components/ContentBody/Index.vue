<script lang="ts" setup>
import { computed, inject, onBeforeMount, provide, ref } from 'vue'
import { useStore } from '@/store'
import type { User } from '@/store/types/accounts.ts'
import { type RouteRecordName, useRoute, useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account.ts'

const props = defineProps({ aside: { type: Boolean, default: true } })

const visible = ref(false)

const query = inject('query') as Record<string, any>
const navMenu = inject('navMenu')

const [route, router] = [useRoute(), useRouter()]

const isDark = computed(() => useStore().theme === 'dark')
const baseColor = computed(() => (isDark.value ? '#fff' : '#333'))
const bgColor = computed(() => (isDark.value ? '#24252F' : '#fefefe'))
const isActive = (menu: string) =>
  (route.name as string).includes(menu) || (route.meta as any).title.includes(menu)

const accStore = useAccount()
const userInfo = computed<User | null>(() => accStore.userInfo)
const logout = () => {
  accStore.logout()
  router.push({ name: 'Login' })
}

const goToMenu = (menu: string) => {
  router.push({ name: menu as RouteRecordName, query: { ...query } })
  visible.value = false
}
const toggle = () => (visible.value = !visible.value)
provide('doingToggle', toggle)
defineExpose({ toggle })

const getGuide = () => window.open('https://www.redmine.org/guide', '_blank', 'noopener,noreferrer')

// 검색 관련 기능 시작
const search = ref('')
const goSearch = () => router.push({ name: '전체검색', query: { scope: '', q: search.value } })

onBeforeMount(async () => {
  if (route?.query.q) search.value = route.query.q as string
})
</script>

<template>
  <CRow class="flex-grow-1">
    <CCol class="text-body main p-4 px-lg-5 mx-3">
      <slot> Under Construction!</slot>
    </CCol>

    <CCol v-if="aside" class="text-body p-4 d-none d-xl-block col-lg-2">
      <slot name="aside"> Under Construction!</slot>
    </CCol>

    <COffcanvas placement="end" class="p-2" :visible="visible" @hide="() => (visible = !visible)">
      <COffcanvasHeader>
        <CCol class="mr-2">
          <COffcanvasTitle>
            <CFormInput
              v-model="search"
              placeholder="검색"
              @keydown.enter="goSearch"
              @focusin="search = ''"
            />
          </COffcanvasTitle>
        </CCol>
        <CCloseButton class="text-reset" @click="() => (visible = false)" />
      </COffcanvasHeader>

      <v-divider />

      <COffcanvasBody class="p-0">
        <v-card class="mx-auto mb-5 pointer" max-width="500" border flat>
          <v-list density="compact" :base-color="baseColor" :bg-color="bgColor">
            <v-list-item
              @click="router.push({ name: '사용자 - 보기', params: { userId: userInfo?.pk } })"
            >
              {{ userInfo?.username }}
            </v-list-item>
            <template v-if="route.path.startsWith('/work/project')">
              <v-list-item variant="tonal" disabled>프로젝트</v-list-item>
              <v-list-item
                v-for="(menu, i) in navMenu"
                :active="isActive(menu)"
                :key="i"
                @click="goToMenu(menu as string)"
              >
                {{ (menu as string).replace(/^\((.*)\)$/, '$1') }}
              </v-list-item>
            </template>
            <v-list-item variant="tonal" disabled>일반</v-list-item>
            <v-list-item @click="router.push({ name: '업 무 관 리' })">프로젝트</v-list-item>
            <v-list-item @click="router.push({ name: '설 정 관 리' })">설정관리</v-list-item>
            <v-list-item @click="getGuide"> 도움말</v-list-item>
            <v-list-item variant="tonal" disabled>사용자정보</v-list-item>
            <v-list-item @click="router.push({ name: '내 정보' })">내 계정</v-list-item>
            <v-list-item @click="logout">로그아웃</v-list-item>
          </v-list>
        </v-card>

        <v-divider />

        <slot name="aside">
          Content for the offcanvas goes here. You can place just about any Bootstrap component or
          custom elements here.
        </slot>
      </COffcanvasBody>
    </COffcanvas>
  </CRow>
</template>

<style lang="scss" scoped>
.main {
  background: #ffffff;
  border-right: 1px solid #ddd !important;
}

.dark-theme .main {
  background: #1c1d26;
  border-right: 1px solid #333 !important;
}

.active {
  font-weight: bold;
  background: #e5e7eb;
}

.dark-theme .active {
  background: #32333d;
}
</style>
