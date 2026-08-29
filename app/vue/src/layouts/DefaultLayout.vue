<script lang="ts" setup>
import { onMounted, onUnmounted } from 'vue'
import AppSidebar from '@/layouts/containers/AppSidebar.vue'
import AppHeader from '@/layouts/containers/AppHeader.vue'
import AppFooter from '@/layouts/containers/AppFooter.vue'
import AppAside from '@/layouts/containers/AppAside.vue'
import BackToTop from '@/components/BackToTop/index.vue'
import ChatDrawer from '@/components/Chat/ChatDrawer.vue'
import { useSSE } from '@/composables/useSSE'

const { connect, disconnect } = useSSE()

onMounted(() => {
  connect()
})

onUnmounted(() => {
  disconnect()
})
</script>

<template>
  <AppSidebar />
  <div class="wrapper d-flex flex-column min-vh-100 bg-light dark:bg-body">
    <AppHeader />
    <div class="body d-flex flex-column flex-grow-1">
      <CContainer fluid class="d-flex flex-column flex-grow-1 p-0">
        <router-view />
      </CContainer>
    </div>
    <AppFooter />
  </div>
  <AppAside />
  <BackToTop />
  <ChatDrawer />
</template>
