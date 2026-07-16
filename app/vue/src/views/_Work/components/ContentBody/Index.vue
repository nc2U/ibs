<script lang="ts" setup>
import { computed, inject, onBeforeMount, provide, ref } from 'vue'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account.ts'
import type { User } from '@/store/types/accounts.ts'
import { type RouteRecordName, useRoute, useRouter } from 'vue-router'

defineProps({ aside: { type: Boolean, default: true } })

const visible = ref(false)

const query = inject('query') as Record<string, any>
const navMenu = inject('navMenu')

const [route, router] = [useRoute(), useRouter()]

const isDark = computed(() => useStore().theme === 'dark')
const baseColor = computed(() => (isDark.value ? '#fff' : '#333'))
const bgColor = computed(() => (isDark.value ? '#24252F' : '#fefefe'))

const isActive = (menu: string) =>
  ((route.name as string) ?? '').includes(menu) || ((route.meta as any)?.title ?? '').includes(menu)

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo as User)
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

// 우측 사이드바 컨트롤
const routeSlug = computed(() => route.path.split('/').pop())
const sidebarVisible = ref(true)
const sidebarWidth = computed(() => (sidebarVisible.value ? 420 : 30))
const sidebarToggle = () => {
  sidebarVisible.value = !sidebarVisible.value
  localStorage.setItem(
    `redmine-sidebar-visible-${routeSlug.value}`,
    JSON.stringify(sidebarVisible.value),
  )
}

onBeforeMount(async () => {
  if (route?.query.q) search.value = route.query.q as string
  sidebarVisible.value = JSON.parse(
    localStorage.getItem(`redmine-sidebar-visible-${routeSlug.value}`) ?? 'true',
  )
})
</script>

<template>
  <CRow class="d-flex flex-row flex-grow-1 main-layout">
    <!--    Main Content-->
    <CCol class="text-body main flex-grow-1 p-4 px-lg-5 mx-3">
      <slot></slot>
    </CCol>

    <!--    Sidebar-->
    <CCol
      v-if="aside"
      id="sidebar"
      class="text-body d-none d-lg-block p-0 col-lg-2"
      :style="{ width: sidebarWidth + 'px', flexShrink: 0 }"
    >
      <CRow class="mb-4 py-1 pointer sidebar-switch" @mousedown="sidebarToggle">
        <CCol class="pl-0">
          <v-icon :icon="`mdi-chevron-double-${sidebarVisible ? 'right' : 'left'}`" color="grey" />
        </CCol>
      </CRow>

      <CRow v-show="sidebarVisible">
        <CCol class="px-3" style="position: relative">
          <slot name="aside"></slot>
        </CCol>
      </CRow>
    </CCol>

    <!--    Off canvas-->
    <COffcanvas
      placement="end"
      class="px-2 pt-4"
      :visible="visible"
      @hide="() => (visible = !visible)"
    >
      <COffcanvasHeader class="mb-4">
        <COffcanvasTitle class="w-100 pr-2">
          <v-text-field
            v-model="search"
            placeholder="검색어 입력"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-magnify"
            hide-details
            @keydown.enter="goSearch"
            @focusin="search = ''"
            class="search-field"
          />
        </COffcanvasTitle>
      </COffcanvasHeader>

      <COffcanvasBody class="p-0">
        <v-card class="mx-auto mb-5 pointer" max-width="500" border flat>
          <v-list density="compact" :base-color="baseColor" :bg-color="bgColor">
            <v-list-item
              @click="router.push({ name: '사용자 - 보기', params: { userId: userInfo?.pk } })"
            >
              {{ userInfo?.username }}
            </v-list-item>
            <template v-if="route.path.startsWith('/work/')">
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

        <slot name="aside"></slot>
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

#sidebar {
  transition: width 0.3s ease; /* 너비 변경에 트랜지션 적용 */
}

.sidebar-switch:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark-theme .sidebar-switch:hover {
  background: #2a2b36;
}

.main {
  background: #ffffff;
  border-right: 1px solid #ddd !important;

  // 추가: 메인 콘텐츠가 사이드바 공간을 침범하지 않게 함
  flex: 1 1 0%;
  min-width: 0; // 중요: Flex 자식 요소가 내부 콘텐츠 폭에 의해 늘어나는 것 방지
}
</style>
