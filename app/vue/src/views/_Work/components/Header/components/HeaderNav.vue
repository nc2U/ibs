<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useStore } from '@/store'
import { useWork } from '@/store/pinia/work_project'
import { usePerms } from '@/composables/usePerms'
import { type RouteRecordName, useRoute, useRouter } from 'vue-router'

defineProps({
  menus: { type: Array as PropType<string[]>, required: true },
})

const { can, PERM } = usePerms()
const workStore = useWork()
const currentProject = computed(() => workStore.currentProject)
const isProjectActive = computed(() => currentProject.value?.status === '1')

const [route, router] = [useRoute(), useRouter()]
const projParams = computed(() => ({ projId: route.params['projId'] }))

const canQuickIssue = computed(
  () => !!currentProject.value?.module?.issue && can(PERM.ISSUE_CREATE),
)
const canQuickCategory = computed(
  () => !!currentProject.value?.module?.issue && can(PERM.ISSUE_CATEGORY_MANAGE),
)
const canQuickVersion = computed(() => can(PERM.PROJECT_VERSION))
const canQuickNews = computed(
  () => !!currentProject.value?.module?.news && can(PERM.NEWS_MANAGE),
)
const canQuickDocs = computed(
  () => !!currentProject.value?.module?.document && can(PERM.DOCS_CREATE),
)
const hasQuickCreate = computed(
  () =>
    canQuickIssue.value ||
    canQuickCategory.value ||
    canQuickVersion.value ||
    canQuickNews.value ||
    canQuickDocs.value,
)

const store = useStore()
const isDark = computed(() => store.theme === 'dark')

const menuName = computed(() => {
  const name = String(route.name ?? '')
  return name.split(/\s*-\s*/)[0].trim()
})

const isMenuActive = (menu: unknown) => {
  const m = String(menu ?? '')
  const current = menuName.value
  const cleanM = getTitle(m)
  const cleanCurrent = getTitle(current)

  return (
    current === m ||
    cleanCurrent === cleanM ||
    current.startsWith(`${m} `) ||
    (cleanCurrent.startsWith(cleanM) && cleanCurrent === '문서사건' && cleanM === '문서') ||
    ((route.meta as { title?: string })?.title ?? '').includes(m)
  )
}

const getTitle = (title: string) => (title ?? '').replace(/[() ]/gim, '')

const toLocation = (menu: string) => {
  const targetName = menu as RouteRecordName
  if (route.params['projId']) {
    return { name: targetName, params: { projId: route.params['projId'] } }
  }
  return { name: targetName }
}
</script>

<template>
  <CNav variant="tabs" class="mb-0 ps-4">
    <CDropdown v-if="route.params['projId'] && isProjectActive && hasQuickCreate">
      <CDropdownToggle :color="isDark ? 'dark' : 'light'" />
      <CDropdownMenu>
        <CDropdownItem
          v-if="canQuickIssue"
          @click="router.push({ name: '(업무) - 추가', params: projParams })"
        >
          새 업무
        </CDropdownItem>
        <CDropdownItem
          v-if="canQuickCategory"
          @click="router.push({ name: '(설정) - 범주추가', params: projParams })"
        >
          새 업무 범주
        </CDropdownItem>
        <CDropdownItem
          v-if="canQuickVersion"
          @click="router.push({ name: '(로드맵) - 추가', params: projParams })"
        >
          새 단계
        </CDropdownItem>
        <CDropdownItem
          v-if="canQuickNews"
          @click="router.push({ name: '(공지)', params: projParams, query: { viewForm: '1' } })"
        >
          새 공지
        </CDropdownItem>
        <CDropdownItem
          v-if="canQuickDocs"
          @click="router.push({ name: '(문서)', params: projParams, query: { viewForm: '1' } })"
        >
          새 문서
        </CDropdownItem>
      </CDropdownMenu>
    </CDropdown>
    <CNavItem v-for="(menu, i) in menus" :key="i">
      <CNavLink :active="isMenuActive(menu)" @click="router.push(toLocation(menu as string))">
        {{ getTitle(menu as string) }}
      </CNavLink>
    </CNavItem>
  </CNav>
</template>
