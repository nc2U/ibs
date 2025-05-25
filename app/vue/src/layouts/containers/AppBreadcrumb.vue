<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { type RouteLocationMatched } from 'vue-router'
import router from '@/router'

const breadcrumbs = ref()

const getBreadcrumbs = () => {
  return router.currentRoute.value.matched.map((route: RouteLocationMatched) => ({
    active: route.path === router.currentRoute.value.fullPath || route.path.includes(':'),
    name: route.name,
    path: `${router.options.history.base}${route.path}`,
  }))
}

router.afterEach(() => (breadcrumbs.value = getBreadcrumbs()))

onBeforeMount(() => (breadcrumbs.value = getBreadcrumbs()))
</script>

<template>
  <CBreadcrumb class="d-md-down-none me-auto mb-0">
    <!--    <TransitionGroup name="breadcrumb">-->
    <CBreadcrumbItem
      v-for="item in breadcrumbs"
      :key="item"
      :href="item.active ? '' : item.path"
      :active="item.active"
    >
      {{ item.name.replace(/^\((.*)\)$/, '$1') }}
    </CBreadcrumbItem>
    <!--    </TransitionGroup>-->
  </CBreadcrumb>
</template>
