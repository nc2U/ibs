<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account'
import type { User } from '@/store/types/accounts'
import { directive as vFullscreen } from 'vue-fullscreen'
import { logo } from '@/assets/brand/current-logo'
import AppBreadcrumb from './AppBreadcrumb.vue'
import AppHeaderDropdown from './AppHeaderDropdown.vue'
import TagsView from '@/layouts/containers/TagsView.vue'

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
const toggleTheme = (theme: 'default' | 'dark') => store.toggleTheme(theme)
const toggleAside = () => store.toggleAside()
</script>

<template>
  <CHeader position="sticky" class="pb-0">
    <CContainer fluid>
      <CHeaderToggler class="ps-1" @click="toggleSidebar">
        <v-icon
          v-if="isVisible"
          icon="mdi mdi-format-indent-decrease"
          size="small"
          class="text-50"
        />
        <v-icon v-else icon="mdi mdi-format-indent-increase" size="small" class="text-50" />
      </CHeaderToggler>

      <CHeaderBrand class="mx-auto d-lg-none" to="/">
        <CIcon :icon="logo" height="31" alt="Logo" />
      </CHeaderBrand>

      <CHeaderNav class="d-none d-lg-flex me-auto">
        <AppBreadcrumb />
      </CHeaderNav>

      <CHeaderNav class="ms-auto me-4">
        <CHeaderToggler v-fullscreen.teleport="options" class="d-none d-lg-block">
          <v-icon large :icon="screenIcon" class="text-50" />
          <v-tooltip activator="parent" location="bottom">
            {{ screenGuide }}
          </v-tooltip>
        </CHeaderToggler>

        <CButtonGroup aria-label="Theme switch">
          <CFormCheck
            id="btn-light-theme"
            type="radio"
            :button="{ color: 'primary' }"
            name="theme-switch"
            auto-complete="off"
            :checked="theme === 'default'"
            @change="toggleTheme('default')"
          >
            <template #label>
              <CIcon icon="cil-sun" />
            </template>
          </CFormCheck>

          <CFormCheck
            id="btn-dark-theme"
            type="radio"
            :button="{ color: 'primary' }"
            name="theme-switch"
            auto-complete="off"
            :checked="theme === 'dark'"
            @change="toggleTheme('dark')"
          >
            <template #label>
              <CIcon icon="cil-moon" />
            </template>
          </CFormCheck>
        </CButtonGroup>
      </CHeaderNav>

      <CHeaderNav class="mr-4">
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
