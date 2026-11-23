<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { type LocationQueryRaw, type RouteRecordName, useRoute, useRouter } from 'vue-router'

const props = defineProps({
  menus: { type: Array as PropType<string[]>, required: true },
  query: { type: Object as PropType<LocationQueryRaw | null>, default: null },
})

const [route, router] = [useRoute(), useRouter()]

// 탭 전환 시 화면 종속 임시 파라미터(page, highlight_id, contractor 등)는 제외하고
// 전역 컨텍스트(project, company, main_project 등)만 유지하여 전달
const navQuery = computed<LocationQueryRaw | undefined>(() => {
  if (!props.query) return undefined
  const persistentKeys = ['project', 'company', 'main_project'] as const
  const filtered: LocationQueryRaw = {}
  for (const key of persistentKeys) {
    const val = props.query[key]
    if (val !== undefined && val !== null && val !== '') {
      filtered[key] = val
    }
  }
  return Object.keys(filtered).length > 0 ? filtered : undefined
})
</script>

<template>
  <CNav variant="tabs" class="mb-5">
    <CNavItem v-for="(menu, i) in menus" :key="i">
      <CNavLink
        :active="route?.name === menu || route?.meta.title === menu"
        @click="router.push({ name: menu as RouteRecordName, query: navQuery })"
      >
        {{ menu }}
      </CNavLink>
    </CNavItem>
  </CNav>
</template>
