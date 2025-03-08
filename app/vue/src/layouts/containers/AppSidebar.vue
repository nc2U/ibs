<script lang="ts" setup>
import { computed } from 'vue'
import { useStore } from '@/store'
import { AppSidebarNav } from './AppSidebarNav'
import { logoNegative1, sygnet1 } from '@/assets/brand/current-logo'

const store = useStore()

const sidebarUnfoldable = computed(() => store.sidebarUnfoldable)
const sidebarVisible = computed(() => store.sidebarVisible)
</script>

<template>
  <CSidebar
    position="fixed"
    self-hiding="md"
    :unfoldable="sidebarUnfoldable"
    :visible="sidebarVisible"
    @visible-change="(event: any) => store.updateSidebarVisible(event)"
  >
    <CSidebarBrand>
      <CIcon custom-class-name="sidebar-brand-full" :icon="logoNegative1" :height="30" />
      <CIcon custom-class-name="sidebar-brand-narrow" :icon="sygnet1" :height="30" />
    </CSidebarBrand>

    <AppSidebarNav />

    <CSidebarToggler class="d-none d-lg-flex" @click="store.toggleUnfoldable" />
  </CSidebar>
</template>
