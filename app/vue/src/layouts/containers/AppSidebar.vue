<script lang="ts" setup>
import { computed } from 'vue'
import { useStore } from '@/store'
import { AppSidebarNav } from './AppSidebarNav'
import { logoNegative, sygnet } from '@/assets/brand/current-logo'

const store = useStore()
const sidebarUnfoldable = computed(() => store.sidebarUnfoldable)
const sidebarVisible = computed(() => store.sidebarVisible)
const toggleUnfoldable = () => store.toggleUnfoldable()
</script>

<template>
  <CSidebar
    position="fixed"
    self-hiding="md"
    :unfoldable="!!sidebarUnfoldable"
    :visible="!!sidebarVisible"
  >
    <CSidebarBrand>
      <CIcon custom-class-name="sidebar-brand-full" :icon="logoNegative" :height="30" />
      <CIcon custom-class-name="sidebar-brand-narrow" :icon="sygnet" :height="30" />
    </CSidebarBrand>

    <AppSidebarNav />

    <CSidebarToggler class="d-none d-lg-flex" @click="toggleUnfoldable" />
  </CSidebar>
</template>
