import { type Component, computed, defineComponent, h, onMounted, ref, resolveComponent, reactive } from 'vue'
import { storeToRefs } from 'pinia'
import { useAccount } from '@/store/pinia/account'
import { type RouteLocationNormalized, RouterLink, useRoute } from 'vue-router'
import { CBadge, CNavGroup, CNavItem, CNavTitle, CSidebarNav } from '@coreui/vue'
import { CIcon } from '@coreui/icons-vue'

import nav from '@/layouts/_nav'

/* ---------------------------
   Types
--------------------------- */
type Badge = { color?: string; text?: string }
export type Item = { badge?: Badge; component: string | Component; icon?: string; items?: Item[]; name?: string; to?: string; visible?: boolean; manuallyToggled?: boolean }

/* ---------------------------
   normalizePath
--------------------------- */
export const normalizePath = (path = '') =>
  decodeURI(path)
    .replace(/#.*$/, '')
    .replace(/(index)?\.(html)$/, '')

/* ---------------------------
   isActiveItem
--------------------------- */
export const isActiveLink = (route: RouteLocationNormalized, link?: string) => {
  if (!link) return false
  if (route.hash && route.hash === link) return true
  const currentPath = normalizePath(route.path || '')
  const targetPath = normalizePath(link)
  return currentPath === targetPath || currentPath.startsWith(targetPath + '/')
}

export const isActiveItem = (route: RouteLocationNormalized, item: Item): boolean => {
  if (item.to && isActiveLink(route, item.to)) return true
  if (Array.isArray(item.items) && item.items.length > 0) return item.items.some(child => isActiveItem(route, child))
  const metaTitle = (route.meta && (route.meta.title as string | undefined)) || undefined
  if (item.name && metaTitle) return item.name === metaTitle
  return false
}

/* ---------------------------
   filterNavItems
--------------------------- */
function filterNavItems(items: Item[], predicates: ((it: Item) => boolean)[]): Item[] {
  const passAllPredicates = (it: Item) => predicates.every(p => p(it))
  return items
    .map(it => ({ ...it, items: it.items ? filterNavItems(it.items, predicates) : undefined }))
    .filter(it => passAllPredicates(it) || (Array.isArray(it.items) && it.items.length > 0))
}

/* ---------------------------
   reactiveNav export
--------------------------- */
export const reactiveNav = reactive(filterNavItems(nav as Item[], [])) // 기본 필터 없이 초기화

/* ---------------------------
   AppSidebarNav Component
--------------------------- */
const AppSidebarNav = defineComponent({
  name: 'AppSidebarNav',
  components: { CNavItem, CNavGroup, CNavTitle },
  setup() {
    const route = useRoute()
    const firstRender = ref(true)

    onMounted(() => {
      firstRender.value = false
    })

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

    const filteredNav = computed(() => filterNavItems(reactiveNav, predicates.value))

    const renderContent = (item: Item) => {
      const children: any[] = []
      if (item.icon) children.push(h(CIcon, { customClassName: 'nav-icon', name: item.icon }))
      if (item.name) children.push(item.name)
      if (item.badge) children.push(h(CBadge, { class: 'ms-auto', color: item.badge.color }, () => item.badge && item.badge.text))
      return children
    }

    const renderItem = (item: Item) => {
      if (Array.isArray(item.items) && item.items.length > 0) {
        return h(CNavGroup,
          {
            visible: firstRender.value ? item.items.some(child => isActiveItem(route, child)) : item.visible,
            onUpdateVisible: (val: boolean) => { item.visible = val; item.manuallyToggled = true }
          },
          {
            togglerContent: () => renderContent(item),
            default: () => item.items && item.items.map(child => renderItem(child)),
          }
        )
      }

      if (item.to) {
        return h(RouterLink, { to: item.to, custom: true }, {
          default: (props: any) => {
            const component = typeof item.component === 'string' ? resolveComponent(item.component) : item.component
            return h(component, { active: props.isActive, href: props.href, onClick: () => props.navigate() }, () => renderContent(item))
          }
        })
      }

      const component = typeof item.component === 'string' ? resolveComponent(item.component) : item.component
      return h(component, {}, () => renderContent(item))
    }

    return () => h(CSidebarNav, {}, { default: () => filteredNav.value.map(item => renderItem(item)) })
  }
})

export { AppSidebarNav }
