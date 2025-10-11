import { type Component, computed, defineComponent, h, onMounted, ref, resolveComponent } from 'vue'
import { storeToRefs } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { type RouteLocationNormalized, RouterLink, useRoute } from 'vue-router'
import { CBadge, CNavGroup, CNavItem, CNavTitle, CSidebarNav } from '@coreui/vue'
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

  // 정확한 매칭
  if (currentPath === targetPath) return true

  // 부모 경로 매칭: /contracts/succession은 /contracts의 하위
  return currentPath.startsWith(targetPath + '/')
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
    // Todo 페이지 새로고침 시 안정적으로 작동하도록 개선 요망
    const route = useRoute()
    const firstRender = ref(true)

    onMounted(() => {
      firstRender.value = false
    })

    // Pinia store: call once and destructure reactive refs
    const account = useAccount()
    const { workManager, isStaff, isComCash } = storeToRefs(account)

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

    // helper: 반복을 피하기 위해 콘텐츠(아이콘 + 이름 + 배지)를 렌더링.
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

    // renderItem: CNavGroup 또는 RouterLink로 래핑된 항목에 대한 VNode를 반환.
    const renderItem = (item: Item) => {
      // If item has children -> CNavGroup
      if (Array.isArray(item.items) && item.items.length > 0) {
        return h(
          CNavGroup,
          {
            // CoreUI 공식 로직: 첫 렌더링 시에만 visible 전달
            ...(firstRender.value && {
              visible: item.items.some(child => isActiveItem(route, child)),
            }),
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
