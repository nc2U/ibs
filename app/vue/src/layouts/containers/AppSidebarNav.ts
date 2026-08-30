import {
  type Component,
  computed,
  defineComponent,
  h,
  nextTick,
  onUnmounted,
  reactive,
  ref,
  resolveComponent,
  type VNode,
  watch,
} from 'vue'
import { CIcon } from '@coreui/icons-vue'
import { CBadge, CNavGroup, CSidebarNav } from '@coreui/vue'
import { useAccount } from '@/store/pinia/account'
import { useApproval } from '@/store/pinia/approval'
import { usePerms } from '@/composables/usePerms'
import { type RouteLocationNormalized, RouterLink, useRoute } from 'vue-router'
import nav from '@/layouts/_nav'

type Badge = { color?: string; text?: string }
type DynamicBadge = Badge | (() => Badge | undefined)
type Item = {
  auth?: string
  badge?: DynamicBadge
  component: string | Component
  icon?: string
  items?: Item[]
  name?: string
  to?: string
  visible?: boolean
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

const filterNavItems = (items: Item[], predicates: ((it: Item) => boolean)[]): Item[] => {
  const passAllPredicates = (it: Item) => predicates.every(p => p(it))

  return items
    .filter(it => passAllPredicates(it))
    .map(it => ({
      ...it,
      items: it.items ? filterNavItems(it.items, predicates) : undefined,
    }))
    .filter(it => it.component !== 'CNavGroup' || (Array.isArray(it.items) && it.items.length > 0))
}

const getAuthMap = (
  isStaff: boolean,
  permissions: {
    comLedgerRead: boolean
    hrWorkRead: boolean
    contractRead: boolean
    paymentRead: boolean
    noticeRead: boolean
    ledgerRead: boolean
    docsRead: boolean
    prManage: boolean
    siteRead: boolean
    comManage: boolean
    authManage: boolean
  },
) => ({
  isStaff,
  isCLManager: permissions.comLedgerRead,
  isHrManager: permissions.hrWorkRead,
  isContManager: permissions.contractRead,
  isPayManager: permissions.paymentRead,
  isNotiManager: permissions.noticeRead,
  isLedgerManager: permissions.ledgerRead,
  isDocsManager: permissions.docsRead,
  isProjManager: permissions.prManage,
  isSiteManager: permissions.siteRead,
  isSetMenu: permissions.comManage || permissions.authManage,
  isCompany: permissions.comManage,
  isAuthor: permissions.authManage,
})

const AppSidebarNav = defineComponent({
  name: 'AppSidebarNav',
  setup() {
    const route = useRoute()
    const userClickedSidebar = ref(false)

    // 메뉴 그룹의 열림 상태를 고유 Key(to 또는 name) 기반으로 관리할 반응형 맵 객체
    const openStates = reactive<Record<string, boolean>>({})

    // Pinia store
    const account = useAccount()
    const approvalStore = useApproval()
    const isStaff = computed(() => account.isStaff)

    // 결재 대기 문서 로드 및 폴링
    watch(
      isStaff,
      val => {
        if (val) {
          approvalStore.fetchMyPending()
          approvalStore.startPollingMyPending()
        } else {
          approvalStore.stopPollingMyPending()
        }
      },
      { immediate: true },
    )

    onUnmounted(() => {
      approvalStore.stopPollingMyPending()
    })

    const { canGlobal, PERM } = usePerms()
    const permissions = computed(() => ({
      comLedgerRead: canGlobal(PERM.HQ_LEDGER_READ),
      hrWorkRead: canGlobal(PERM.HQ_HR_WORK_READ),
      contractRead: canGlobal(PERM.CONTRACT_READ),
      paymentRead: canGlobal(PERM.PAYMENT_READ),
      noticeRead: canGlobal(PERM.NOTICE_READ),
      ledgerRead: canGlobal(PERM.LEDGER_READ),
      docsRead: canGlobal(PERM.DOCS_READ),
      prManage: canGlobal(PERM.PROJECT_CREATE) || canGlobal(PERM.PROJECT_UPDATE),
      siteRead: canGlobal(PERM.SITE_READ),
      comManage:
        isStaff.value && (canGlobal(PERM.PROJECT_CREATE) || canGlobal(PERM.PROJECT_UPDATE)),
      authManage: isStaff.value && canGlobal(PERM.PROJECT_MEMBER),
    }))

    const predicates = computed(() => {
      const authMap = getAuthMap(isStaff.value, permissions.value)
      type AuthKey = keyof typeof authMap

      return [
        (it: Item) => {
          if (it.auth) return authMap[it.auth as AuthKey] ?? false
          return true
        },
      ]
    })

    const reactiveNav = computed(() =>
      filterNavItems(Array.isArray(nav) ? (nav as Item[]) : [], predicates.value),
    )

    // ---------------------------
    // 활성 메뉴 자동 열기/닫기
    // ---------------------------
    const openActiveMenu = (items: Item[]) => {
      items.forEach(item => {
        if (Array.isArray(item.items) && item.items.length > 0) {
          const key = item.to || item.name || ''
          if (key) {
            const hasActiveChild = item.items.some(child => isActiveItem(route, child))
            if (hasActiveChild) {
              openStates[key] = true
            }
          }
          openActiveMenu(item.items)
        }
      })
    }

    // ---------------------------
    // 렌더 헬퍼
    // ---------------------------
    const renderContent = (item: Item): VNode[] => {
      const children: VNode[] = []
      if (item.icon) children.push(h(CIcon, { customClassName: 'nav-icon', name: item.icon }))
      if (item.name) children.push(h('span', {}, item.name))
      const badge = typeof item.badge === 'function' ? item.badge() : item.badge
      if (badge && badge.text) {
        children.push(
          h(
            CBadge,
            { class: 'ms-auto', color: badge.color || 'primary' },
            { default: () => badge.text },
          ),
        )
      }
      return children
    }

    const renderItem = (item: Item): VNode => {
      if (Array.isArray(item.items) && item.items.length > 0) {
        const key = item.to || item.name || ''
        const isOpen = key ? openStates[key] : false

        return h(
          CNavGroup,
          {
            visible: isOpen,
            onToggle: (visible: boolean) => {
              if (key) {
                openStates[key] = visible
              }
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
    // 라우트 변경 및 메뉴 데이터 로드 감지
    // ---------------------------
    watch(
      [() => route.fullPath, () => reactiveNav.value],
      async () => {
        if (userClickedSidebar.value) {
          userClickedSidebar.value = false
          return
        }
        await nextTick()
        openActiveMenu(reactiveNav.value)
      },
      { immediate: true },
    )

    return () => h(CSidebarNav, {}, { default: () => reactiveNav.value.map(renderItem) })
  },
})

export { AppSidebarNav }
