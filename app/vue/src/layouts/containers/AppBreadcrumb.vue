<script setup lang="ts">
import { ref, watch } from 'vue'
import { type RouteLocationMatched, useRoute, useRouter } from 'vue-router'

interface BreadcrumbItem {
  active: boolean
  name: RouteLocationMatched['name']
  path: string
}

const route = useRoute()
const router = useRouter()
const breadcrumbs = ref<BreadcrumbItem[]>([])

const getBreadcrumbs = (): BreadcrumbItem[] => {
  const base = router.options.history.base || ''
  return route.matched.map((matched: RouteLocationMatched) => ({
    active: matched.path === route.fullPath || matched.path.includes(':'),
    name: matched.name,
    path: `${base}${matched.path}`,
  }))
}

watch(
  () => route.fullPath,
  () => {
    breadcrumbs.value = getBreadcrumbs()
  },
  { immediate: true },
)
</script>

<template>
  <CBreadcrumb class="d-md-down-none me-auto mb-0">
    <!--    <TransitionGroup name="breadcrumb">-->
    <CBreadcrumbItem
      v-for="item in breadcrumbs"
      :key="item.path"
      :href="item.active ? '' : item.path"
      :active="item.active"
    >
      {{ String(item.name ?? '').replace(/^\((.*)\)$/, '$1') }}
    </CBreadcrumbItem>
    <!--    </TransitionGroup>-->
  </CBreadcrumb>
</template>
