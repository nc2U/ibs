import { defineComponent, h, ref, resolveComponent, computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { RouterLink, useRoute, type RouteLocation } from 'vue-router'

import { CBadge, CNavGroup, CNavItem, CSidebarNav, CNavTitle } from '@coreui/vue'
import { CIcon } from '@coreui/icons-vue'
import nav from '@/layouts/_nav'

type Badge = {
  color?: string
  text?: string
}

type Item = {
  badge?: Badge
  component: string
  icon?: string
  items?: Item[]
  name?: string
  to?: string
}

const workManager = computed(() => useAccount().workManager)
const isStaff = computed(() => useAccount().isStaff)
const isComCash = computed(() => useAccount().isComCash)

const normalizePath = (path: string) =>
  decodeURI(path)
    .replace(/#.*$/, '')
    .replace(/(index)?\.(html)$/, '')

const isActiveLink = (route: RouteLocation, link: string) => {
  if (link === undefined) return false

  if (route.hash === link) return true

  const currentPath = normalizePath(route.path)
  const targetPath = normalizePath(link)

  return currentPath === targetPath
}

const isActiveItem = (route: RouteLocation, item: Item): boolean => {
  if (item.to && isActiveLink(route, item.to)) return true

  if (item.items) return item.items.some(child => isActiveItem(route, child))

  if (item.name && route.meta.title) return item.name === route.meta.title

  return false
}

const AppSidebarNav = defineComponent({
  name: 'AppSidebarNav',
  components: {
    CNavItem,
    CNavGroup,
    CNavTitle,
  },
  // eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
  setup: function () {
    const route = useRoute()
    const firstRender = ref(true)

    const renderItem = (item: Item) => {
      if (item.items) {
        return h(
          CNavGroup,
          {
            ...(firstRender.value && {
              visible: item.items.some(child => isActiveItem(route, child)),
            }),
          },
          {
            togglerContent: () => [
              h(CIcon, {
                customClassName: 'nav-icon',
                name: item.icon,
              }),
              item.name,
            ],
            default: () => item.items && item.items.map(child => renderItem(child)),
          },
        )
      }

      return item.to
        ? h(
            RouterLink,
            {
              to: item.to,
              custom: true,
            },
            {
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              default: (props: any) =>
                h(
                  resolveComponent(item.component),
                  {
                    active: props.isActive,
                    href: props.href,
                    onClick: () => props.navigate(),
                  },
                  () => [
                    item.icon &&
                      h(CIcon, {
                        customClassName: 'nav-icon',
                        name: item.icon,
                      }),
                    item.name,
                    item.badge &&
                      h(
                        CBadge,
                        {
                          class: 'ms-auto',
                          color: item.badge.color,
                        },
                        () => item.badge && item.badge.text,
                      ),
                  ],
                ),
            },
          )
        : h(resolveComponent(item.component), {}, () => item.name)
    }

    // 권한에 따라 메뉴 필터링 (reactive computed)
    const filteredNav = computed(() => {
      let items = [...nav] // 원본 배열을 변경하지 않도록 복사

      // 업무 설정 관리 메뉴 제외
      if (!workManager.value) {
        items = items.filter((item) => item.name !== '설 정 관 리')
      }

      // 본사 관리 직원 권한이 없으면 본사 관련 메뉴 제외
      if (!isStaff.value) {
        const companyMenus = ['본사 자금 관리', '본사 문서 관리', '본사 인사 관리']
        items = items.filter(
          (item) => item.name !== '본사 관리' && !companyMenus.includes(item.name || ''),
        )
      }
      // 본사 자금 관리 권한 없으면 자금 관리 메뉴 제외
      else if (!isComCash.value) {
        items = items.filter((item) => item.name !== '본사 자금 관리')
      }

      return items
    })

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
