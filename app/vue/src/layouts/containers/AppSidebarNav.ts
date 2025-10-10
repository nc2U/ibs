import { defineComponent, h, ref, resolveComponent, computed, type Component } from 'vue'
import { storeToRefs } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { RouterLink, useRoute, type RouteLocationNormalized } from 'vue-router'
import { CBadge, CNavGroup, CNavItem, CSidebarNav, CNavTitle } from '@coreui/vue'
import { CIcon } from '@coreui/icons-vue'

import nav from '@/layouts/_nav'

/* ---------------------------
   Types
   --------------------------- */
type Badge = {
  color?: string
  text?: string
}

type Item = {
  badge?: Badge
  component: string | Component
  icon?: string
  items?: Item[]
  name?: string
  to?: string
}

/* ---------------------------
   Utility: normalizePath
   - decode + strip hash + remove index/.html suffix
   --------------------------- */
const normalizePath = (path = '') =>
  decodeURI(path)
    .replace(/#.*$/, '')
    .replace(/(index)?\.(html)$/, '')

/* ---------------------------
   isActiveLink & isActiveItem
   - Pure functions: 입력만으로 결과 결정 (테스트 용이)
   --------------------------- */
const isActiveLink = (route: RouteLocationNormalized, link?: string) => {
  if (!link) return false
  if (route.hash && route.hash === link) return true

  const currentPath = normalizePath(route.path || '')
  const targetPath = normalizePath(link)
  return currentPath === targetPath
}

const isActiveItem = (route: RouteLocationNormalized, item: Item): boolean => {
  // Direct link match
  if (item.to && isActiveLink(route, item.to)) return true

  // Recursively check children
  if (Array.isArray(item.items) && item.items.length > 0) {
    return item.items.some(child => isActiveItem(route, child))
  }

  // Fallback: compare by name <-> route.meta.title (if provided)
  const metaTitle = (route.meta && (route.meta.title as string | undefined)) || undefined
  if (item.name && metaTitle) return item.name === metaTitle

  return false
}

/* ---------------------------
   Recursive filter for nav items
   - 필터 규칙을 재귀 적용 (children 포함)
   --------------------------- */
function filterNavItems(items: Item[], predicates: ((it: Item) => boolean)[]): Item[] {
  const passAllPredicates = (it: Item): boolean => predicates.every(p => p(it))

  return items
    .map(
      (it): Item => ({
        ...it,
        items: it.items ? filterNavItems(it.items, predicates) : undefined,
      }),
    )
    .filter(it => {
      const passes = passAllPredicates(it)
      const hasChildren = Array.isArray(it.items) && it.items.length > 0
      return passes || hasChildren
    })
}

/* ---------------------------
   Find active menu path
   - 현재 라우트에 해당하는 메뉴의 경로를 찾음
   --------------------------- */
function findActiveMenuPath(
  items: Item[],
  route: RouteLocationNormalized,
  currentPath: string[] = [],
): string[] | null {
  for (const item of items) {
    const itemPath = [...currentPath, item.name || 'unnamed']

    // 현재 아이템이 활성 링크인지 확인
    if (item.to && isActiveLink(route, item.to)) {
      return itemPath
    }

    // 자식이 있으면 재귀 탐색
    if (item.items) {
      const childPath = findActiveMenuPath(item.items, route, itemPath)
      if (childPath) return childPath
    }
  }

  return null
}

/* ---------------------------
   Component
   --------------------------- */
const AppSidebarNav = defineComponent({
  name: 'AppSidebarNav',
  components: {
    CNavItem,
    CNavGroup,
    CNavTitle,
  },
  setup() {
    const route = useRoute()

    // Pinia store: call once and destructure reactive refs
    const account = useAccount()
    const { workManager, isStaff, isComCash } = storeToRefs(account)

    // First render flag (still kept but used only for firstRender behavior if desired)
    const firstRender = ref(true)

    // Predicates for filtering top-level items (you can extend these)
    const predicates = computed(() => {
      const list: ((it: Item) => boolean)[] = []

      if (!workManager.value) list.push(it => (it.name || '') !== '설 정 관 리')

      if (!isStaff.value) {
        // remove company-related
        const companyMenus = new Set(['본사 문서 관리', '본사 인사 관리'])
        list.push(it => (it.name || '') !== '본사 관리' && !companyMenus.has(it.name || ''))
      } else if (!isComCash.value) {
        // staff but no cash permission
        list.push(it => (it.name || '') !== '본사 자금 관리')
      }

      return list
    })

    // filteredNav: 재귀 필터 적용
    const filteredNav = computed(() => {
      const items: Item[] = Array.isArray(nav) ? (nav as Item[]) : []
      return filterNavItems(items, predicates.value)
    })

    // helper: render the content (icon + name + badge) to avoid repetition
    const renderContent = (item: Item) => {
      const children: any[] = []

      if (item.icon) {
        children.push(
          h(CIcon, {
            customClassName: 'nav-icon',
            name: item.icon,
          }),
        )
      }

      if (item.name) children.push(item.name)

      if (item.badge) {
        children.push(
          h(
            CBadge,
            {
              class: 'ms-auto',
              color: item.badge.color,
            },
            () => item.badge && item.badge.text,
          ),
        )
      }

      return children
    }

    // computed to decide if a group should be visible (open) - dynamic on route change
    const groupVisibleFor = (group: Item) =>
      computed(() => {
        // If a group has direct children that match the current route, open it.
        if (!group.items) return false
        return group.items.some(child => isActiveItem(route, child))
      })

    // renderItem: returns VNode for CNavGroup or RouterLink-wrapped item
    const renderItem = (item: Item) => {
      // If item has children -> CNavGroup
      if (Array.isArray(item.items) && item.items.length > 0) {
        const visible = firstRender.value
          ? groupVisibleFor(item).value
          : groupVisibleFor(item).value
        // Note: firstRender kept for compatibility; you can remove the firstRender logic if unnecessary
        return h(
          CNavGroup,
          {
            visible,
          },
          {
            togglerContent: () => renderContent(item),
            default: () => item.items && item.items.map(child => renderItem(child)),
          },
        )
      }

      // Leaf item: render RouterLink (custom) so we get isActive props from Vue Router
      if (item.to) {
        return h(
          RouterLink,
          {
            to: item.to,
            custom: true,
          },
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
                  onClick: () => props.navigate(),
                },
                () => renderContent(item),
              )
            },
          },
        )
      }

      // No link: render as a static component
      const component =
        typeof item.component === 'string' ? resolveComponent(item.component) : item.component

      return h(component, {}, () => renderContent(item))
    }

    // After mount first render flag => false (optional)
    // If you want the firstRender behavior only on the initial display, you can toggle here.
    // (In composition API normal lifecycle you'd use onMounted(); but since this is a render-only component,
    //  leaving firstRender true for now; remove firstRender if not needed.)
    setTimeout(() => {
      firstRender.value = false
    }, 0)

    // render function
    return () =>
      h(
        CSidebarNav,
        {},
        {
          default: () => filteredNav.value.map((item: Item) => renderItem(item)),
        },
      )
  },
})

export { AppSidebarNav }
