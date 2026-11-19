<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, provide, ref, watch } from 'vue'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account'
import { type RouteRecordName, useRoute, useRouter } from 'vue-router'

defineProps({
  aside: { type: Boolean, default: true },
  navMenu: { type: Array as PropType<string[]>, default: () => [] },
})

const visible = ref(false)

const [route, router] = [useRoute(), useRouter()]

const isDark = computed(() => useStore().theme === 'dark')
const baseColor = computed(() => (isDark.value ? '#fff' : '#333'))
const bgColor = computed(() => (isDark.value ? '#24252F' : '#fefefe'))

const getTitle = (title: string) => (title ?? '').replace(/[() ]/gim, '')
const menuName = computed(() => String(route.name ?? '').split(/\s*-\s*/)[0].trim())

const isActive = (menu: string) => {
  const current = menuName.value
  const cleanM = getTitle(menu)
  const cleanCurrent = getTitle(current)
  return (
    current === menu ||
    cleanCurrent === cleanM ||
    (cleanCurrent === '문서사건' && cleanM === '문서')
  )
}

const accStore = useAccount()
const userInfo = computed(() => accStore.userInfo)
const logout = () => {
  visible.value = false
  accStore.logout()
  router.push({ name: 'Login' })
}

const goToMenu = (menu: string) => {
  const targetName = menu as RouteRecordName
  if (route.params['projId']) {
    router.push({ name: targetName, params: { projId: route.params['projId'] } })
  } else {
    router.push({ name: targetName })
  }
  visible.value = false
}

const navigateAndClose = (location: Parameters<typeof router.push>[0]) => {
  visible.value = false
  router.push(location)
}

const toggle = () => (visible.value = !visible.value)
provide('doingToggle', toggle)
defineExpose({ toggle })

const getGuide = () => {
  visible.value = false
  window.open('https://docs.dyibs.com/', '_blank', 'noopener,noreferrer')
}

// 검색 관련 기능 시작
const search = ref('')
const goSearch = () => {
  const q = search.value.trim()
  if (!q) return
  visible.value = false
  router.push({ name: '전체검색', query: { scope: '', q } })
}

// 우측 사이드바 컨트롤 (엔티티 ID 대신 정규화된 라우트 이름 기준 저장)
const sidebarKey = computed(() => `redmine-sidebar-visible-${menuName.value || 'work'}`)
const sidebarVisible = ref(true)
const sidebarWidth = computed(() => (sidebarVisible.value ? 420 : 30))

const loadSidebarVisible = () => {
  try {
    const raw = localStorage.getItem(sidebarKey.value)
    sidebarVisible.value = raw === null ? true : Boolean(JSON.parse(raw))
  } catch {
    sidebarVisible.value = true
  }
}

const sidebarToggle = () => {
  sidebarVisible.value = !sidebarVisible.value
  try {
    localStorage.setItem(sidebarKey.value, JSON.stringify(sidebarVisible.value))
  } catch {
    // ignore storage errors
  }
}

watch(sidebarKey, loadSidebarVisible)
watch(
  () => route.query.q,
  q => {
    if (typeof q === 'string') search.value = q
  },
)

onBeforeMount(() => {
  if (typeof route?.query.q === 'string') search.value = route.query.q
  loadSidebarVisible()
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
      <CRow class="mb-4 py-1 pointer sidebar-switch" @click="sidebarToggle">
        <CCol class="ps-0">
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
      @hide="visible = false"
    >
      <COffcanvasHeader class="mb-4">
        <COffcanvasTitle class="w-100 pe-2">
          <v-text-field
            v-model="search"
            placeholder="검색어 입력"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-magnify"
            hide-details
            @click:prepend-inner="goSearch"
            @keydown.enter="goSearch"
            class="search-field"
          />
        </COffcanvasTitle>
      </COffcanvasHeader>

      <COffcanvasBody class="p-0">
        <v-card class="mx-auto mb-5 pointer" max-width="500" border flat>
          <v-list density="compact" :base-color="baseColor" :bg-color="bgColor">
            <v-list-item variant="tonal" disabled>
              {{ route.path.startsWith('/work/') ? '업무관리' : '설정관리' }}
            </v-list-item>
            <v-list-item
              v-for="(menu, i) in navMenu"
              :active="isActive(menu as string)"
              :key="i"
              @click="goToMenu(menu as string)"
            >
              {{ (menu as string).replace(/^\((.*)\)$/, '$1') }}
            </v-list-item>
            <v-list-item variant="tonal" disabled>일반</v-list-item>
            <v-list-item @click="navigateAndClose({ name: '업 무 관 리' })">업무관리</v-list-item>
            <v-list-item @click="navigateAndClose({ name: '설 정 관 리' })">설정관리</v-list-item>
            <v-list-item variant="tonal" disabled>사용자정보</v-list-item>
            <v-list-item @click="getGuide"> 도움말</v-list-item>
            <v-list-item
              v-if="userInfo?.pk"
              @click="navigateAndClose({ name: '사용자 - 보기', params: { userId: userInfo.pk } })"
            >
              내 정보 보기
            </v-list-item>
            <v-list-item @click="navigateAndClose({ name: '사용자 - 내 계정' })">
              내 계정 관리
            </v-list-item>
            <v-list-item @click="logout">로그아웃</v-list-item>
          </v-list>
        </v-card>

        <slot v-if="aside && visible" name="aside"></slot>
      </COffcanvasBody>
    </COffcanvas>
  </CRow>
</template>

<style lang="scss" scoped>
.main {
  background: #ffffff;
  border-right: 1px solid #ddd !important;
  flex: 1 1 0%;
  min-width: 0; // 중요: Flex 자식 요소가 내부 콘텐츠 폭에 의해 늘어나는 것 방지
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
</style>
