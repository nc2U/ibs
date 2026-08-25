<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useStore } from '@/store'
import { useRouter } from 'vue-router'
import { useAccount } from '@/store/pinia/account'
import type { User } from '@/store/types/accounts'
import { directive as vFullscreen } from 'vue-fullscreen'
import { logo } from '@/assets/brand/current-logo'
import AppBreadcrumb from './AppBreadcrumb.vue'
import AppHeaderDropdown from './AppHeaderDropdown.vue'
import AppHeaderNotifications from './AppHeaderNotifications.vue'
import TagsView from '@/layouts/containers/TagsView.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher/Index.vue'

const router = useRouter()

const store = useStore()
const accountStore = useAccount()

const screenIcon = ref('mdi-fullscreen')
const screenGuide = ref('전체화면')

const options = ref({
  target: '.fullscreen-wrapper',
  callback(isFullscreen: boolean) {
    screenIcon.value = !isFullscreen ? 'mdi-fullscreen' : 'mdi-fullscreen-exit'
    screenGuide.value = !isFullscreen ? '전체화면' : '전체화면 종료'
  },
})

const userInfo = computed(() => accountStore.userInfo)
const profile = computed(() => accountStore.profile)
const isAuthorized = computed(() => accountStore.isAuthorized)
const isVisible = computed(() => store.sidebarVisible)
const theme = computed(() => store.theme)

const toggleSidebar = () => store.toggleSidebar()
const toggleAside = () => store.toggleAside()
</script>

<template>
  <CHeader position="sticky" class="pb-0">
    <CContainer fluid>
      <CHeaderToggler class="ps-1" @click="toggleSidebar">
        <v-icon v-if="isVisible" icon=" mdi-format-indent-decrease" size="small" class="text-50" />
        <v-icon v-else icon="mdi-format-indent-increase" size="small" class="text-50" />
      </CHeaderToggler>

      <CHeaderBrand class="pl-3 d-md-none pointer" to="/" @click="router.push({ path: '/' })">
        <CIcon :icon="logo" height="31" alt="Logo" />
      </CHeaderBrand>

      <CHeaderNav class="d-none d-md-flex me-auto align-items-center">
        <AppBreadcrumb />
      </CHeaderNav>

      <CHeaderNav class="ms-auto me-sm-0 me-md-2 align-items-center">
        <CHeaderToggler v-fullscreen.teleport="options" class="d-none d-lg-block mr-2">
          <v-icon large :icon="screenIcon" class="text-50" />
          <v-tooltip activator="parent" location="bottom">
            {{ screenGuide }}
          </v-tooltip>
        </CHeaderToggler>

        <!-- 테마 전환 토글 버튼 (라이트 -> 다크 -> 기기설정 로테이션) -->
        <ThemeSwitcher custom-class="mr-1" />
      </CHeaderNav>

      <!-- 상단 헤더 실시간 알림 섹션 (결재 대기 / 담당 업무 / 할일) -->
      <CHeaderNav class="d-none d-sm-flex align-items-center mx-2">
        <AppHeaderNotifications />
      </CHeaderNav>

      <CHeaderNav class="mr-sm-0 mr-lg-2">
        <AppHeaderDropdown v-if="isAuthorized" :user-info="userInfo as User" :profile="profile" />
        <router-link v-else :to="{ name: 'Login' }" class="btn btn-outline-primary">
          로그인
        </router-link>
      </CHeaderNav>

      <CHeaderToggler class="px-md-0 me-md-3 d-none d-md-block" @click="toggleAside">
        <v-btn icon size="small" flat :color="theme">
          <v-icon icon="mdi-apps" size="large" class="text-50" />
        </v-btn>
      </CHeaderToggler>
    </CContainer>

    <CHeaderDivider class="mb-0" />

    <CContainer fluid class="px-3">
      <TagsView />
    </CContainer>
  </CHeader>
</template>
