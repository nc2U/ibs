<script lang="ts" setup>
import { computed } from 'vue'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account.ts'
import { type RouteRecordName, useRoute, useRouter } from 'vue-router'

defineProps({
  menus: { type: Array, required: true },
})

const accStore = useAccount()
const workManager = computed(() => accStore.workManager)

const [route, router] = [useRoute(), useRouter()]

const store = useStore()
const isDark = computed(() => store.theme === 'dark')

const menuName = computed(() => {
  const name = String(route.name ?? '')
  return name.split(/\s*-\s*/)[0]
})

const getTitle = (title: string) => title.replace(/[() ]/gim, '')
</script>

<template>
  <CNav variant="tabs" class="mb-0 pl-4">
    <CDropdown v-if="route.params['projId']">
      <CDropdownToggle :color="isDark ? 'dark' : 'light'" />
      <CDropdownMenu>
        <CDropdownItem @click="router.push({ name: '(업무) - 추가' })"> 새 업무 </CDropdownItem>
        <CDropdownItem v-if="workManager" @click="router.push({ name: '(설정) - 범주추가' })">
          새 업무 범주
        </CDropdownItem>
        <CDropdownItem v-if="workManager" @click="router.push({ name: '(로드맵) - 추가' })">
          새 단계
        </CDropdownItem>
        <CDropdownItem
          v-if="workManager"
          @click="router.push({ name: '(공지)', query: { viewForm: '1' } })"
        >
          새 공지
        </CDropdownItem>
        <CDropdownItem
          v-if="workManager"
          @click="router.push({ name: '(문서)', query: { viewForm: '1' } })"
        >
          새 문서
        </CDropdownItem>
      </CDropdownMenu>
    </CDropdown>
    <CNavItem v-for="(menu, i) in menus" :key="i">
      <CNavLink
        :active="menuName === menu || ((route.meta as any)?.title ?? '').includes(menu as string)"
        @click="router.push({ name: menu as RouteRecordName })"
      >
        {{ getTitle(menu as string) }}
      </CNavLink>
    </CNavItem>
  </CNav>
</template>
