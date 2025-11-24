import {
  type Component,
  computed,
  defineComponent,
  h,
  nextTick,
  reactive,
  ref,
  resolveComponent,
  watch,
} from 'vue'
import { storeToRefs } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { type RouteLocationNormalized, RouterLink, useRoute } from 'vue-router'
import { CBadge, CNavGroup, CSidebarNav } from '@coreui/vue'
import { CIcon } from '@coreui/icons-vue'
import nav from '@/layouts/_nav'

type Badge = { color?: string; text?: string }
type Item = {
  badge?: Badge
  component: string | Component
  icon?: string
  items?: Item[]
  name?: string
  to?: string
  visible?: boolean
  manuallyToggled?: boolean
}

const normalizePath = (path = '') =>
  decodeURI(path)
    .replace(/#.*$/, '')
    .replace(/(index)?\.(html)$/, '')

const isActiveLink = (route: RouteLocationNormalized, link?: string) => {
  if (!link) return false
  if (route.hash && route.hash === link) return true
  const currentPath = normalizePath(route.path || '')
  const targetPath = normalizePath(link)
  return currentPath === targetPath || currentPath.startsWith(targetPath + '/')
}

const isActiveItem = (route: RouteLocationNormalized, item: Item): boolean => {
  if (item.to && isActiveLink(route, item.to)) return true
  if (Array.isArray(item.items)) return item.items.some(child => isActiveItem(route, child))
  const metaTitle = route.meta?.title as string | undefined
  return !!(item.name && metaTitle && item.name === metaTitle)
}

function filterNavItems(items: Item[], predicates: ((it: Item) => boolean)[]): Item[] {
  const passAllPredicates = (it: Item) => predicates.every(p => p(it))
  return items
    .map(it => ({ ...it, items: it.items ? filterNavItems(it.items, predicates) : undefined }))
    .filter(it => passAllPredicates(it) || (Array.isArray(it.items) && it.items.length > 0))
}

const AppSidebarNav = defineComponent({
  name: 'AppSidebarNav',
  setup() {
    const route = useRoute()
    const userClickedSidebar = reactive({ value: false })
    const sidebarKey = ref(0)

    // Pinia store
    const account = useAccount()
    const { workManager, isStaff, isComCash } = storeToRefs(account)

    const predicates = computed(() => {
      const list: ((it: Item) => boolean)[] = []
      if (!workManager.value) list.push(it => (it.name || '') !== '설 정 관 리')
      if (!isStaff.value) {
        const companyMenus = new Set(['본사 문서 관리', '본사 인사 관리'])
        list.push(it => (it.name || '') !== '본사 관리' && !companyMenus.has(it.name || ''))
      } else if (!isComCash.value) {
        list.push(it => (it.name || '') !== '본사 자금 관리')
      }
      return list
    })

    const reactiveNav = reactive(
      filterNavItems(Array.isArray(nav) ? (nav as Item[]) : [], predicates.value),
    )

    // ---------------------------
    // 활성 메뉴 자동 열기/닫기
    // ---------------------------
    const openActiveMenu = (items: Item[]) => {
      items.forEach(item => {
        if (Array.isArray(item.items) && item.items.length > 0) {
          item.visible = item.items.some(child => isActiveItem(route, child))
          item.manuallyToggled = false
          openActiveMenu(item.items)
        }
      })
    }

    // ---------------------------
    // 렌더 헬퍼
    // ---------------------------
    const renderContent = (item: Item) => {
      const children: any[] = []
      if (item.icon) children.push(h(CIcon, { customClassName: 'nav-icon', name: item.icon }))
      if (item.name) children.push(item.name)
      if (item.badge)
        children.push(
          h(CBadge, { class: 'ms-auto', color: item.badge.color }, () => item.badge?.text),
        )
      return children
    }

    const renderItem = (item: Item) => {
      if (Array.isArray(item.items) && item.items.length > 0) {
        return h(
          CNavGroup,
          {
            visible: !!item.visible,
            onToggle: (visible: boolean) => {
              item.manuallyToggled = true
              item.visible = visible
            },
          },
          {
            togglerContent: () => renderContent(item),
            default: () => item.items!.map(renderItem),
          },
        )
      }

      if (item.to) {
        return h(
          RouterLink,
          { to: item.to, custom: true },
          {
            default: (props: any) => {
              const component =
                typeof item.component === 'string'
                  ? resolveComponent(item.component)
                  : item.component
              return h(
                component,
                {
                  active: props.isActive,
                  href: props.href,
                  onClick: () => {
                    userClickedSidebar.value = true
                    props.navigate()
                  },
                },
                () => renderContent(item),
              )
            },
          },
        )
      }

      const component =
        typeof item.component === 'string' ? resolveComponent(item.component) : item.component
      return h(component, {}, () => renderContent(item))
    }

    // ---------------------------
    // 라우트 변경 감지 (사이드바 클릭 제외)
    // ---------------------------
    watch(
      () => route.fullPath,
      async () => {
        if (userClickedSidebar.value) {
          userClickedSidebar.value = false
          return
        }
        await nextTick()
        openActiveMenu(reactiveNav)
        sidebarKey.value++ // 강제 재렌더링
      },
      { immediate: true },
    )

    return () =>
      h(CSidebarNav, { key: sidebarKey.value }, { default: () => reactiveNav.map(renderItem) })
  },
})

export { AppSidebarNav }
