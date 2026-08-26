import {
  type Component,
  computed,
  defineComponent,
  h,
  nextTick,
  onMounted,
  onUnmounted,
  reactive,
  ref,
  resolveComponent,
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
    .filter(
      it => it.component !== 'CNavGroup' || (Array.isArray(it.items) && it.items.length > 0),
    )
}

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

    // 결재 대기 문서 목록 로드 및 60초 주기 갱신
    watch(
      isStaff,
      async val => {
        if (val) {
          await approvalStore.fetchMyPending()
        }
      },
      { immediate: true },
    )

    let pollingTimer: ReturnType<typeof setInterval> | null = null
    onMounted(() => {
      pollingTimer = setInterval(async () => {
        if (isStaff.value) {
          await approvalStore.fetchMyPending()
        }
      }, 60000)
    })
    onUnmounted(() => {
      if (pollingTimer) clearInterval(pollingTimer)
    })

    const { canGlobal, PERM } = usePerms()
    const comLedgerRead = computed(() => canGlobal(PERM.LEDGER_COM_READ))
    const hrWorkRead = computed(() => canGlobal(PERM.HR_WORK_READ))

    const contractRead = computed(() => canGlobal(PERM.CONTRACT_READ))
    const paymentRead = computed(() => canGlobal(PERM.PAYMENT_READ))
    const noticeRead = computed(() => canGlobal(PERM.NOTICE_READ))
    const ledgerRead = computed(() => canGlobal(PERM.LEDGER_READ))
    const docsRead = computed(() => canGlobal(PERM.DOCS_READ))
    const prManage = computed(
      () => canGlobal(PERM.PROJECT_CREATE) || canGlobal(PERM.PROJECT_UPDATE),
    )
    const siteRead = computed(() => canGlobal(PERM.SITE_READ))

    const comManage = computed(() => isStaff.value && prManage.value)
    const authManage = computed(() => isStaff.value && canGlobal(PERM.PROJECT_MEMBER))

    const predicates = computed(() => {
      // 권한 키별 접근 제어 매핑
      const authMap: Record<string, boolean> = {
        isStaff: isStaff.value,
        isCLManager: comLedgerRead.value,
        isHrManager: hrWorkRead.value,
        isContManager: contractRead.value,
        isPayManager: paymentRead.value,
        isNotiManager: noticeRead.value,
        isLedgerManager: ledgerRead.value,
        isDocsManager: docsRead.value,
        isProjManager: prManage.value,
        isSiteManager: siteRead.value,
        isSetMenu: comManage.value || authManage.value,
        isCompany: comManage.value,
        isAuthor: authManage.value,
      }

      return [
        (it: Item) => {
          // 만약 현재 아이템에 auth가 설정되어 있다면, 권한 체크를 반드시 통과해야 함
          if (it.auth) return authMap[it.auth] ?? false
          // auth가 설정되어 있지 않으면 표시
          return true
        },
      ]
    })

    const reactiveNav = computed(() =>
      filterNavItems(Array.isArray(nav) ? (nav as Item[]) : [], predicates.value),
    )

    // ---------------------------
    // 활성 메뉴 자동 열기/닫기 (openStates 상태를 갱신하도록 설계)
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
    const renderContent = (item: Item) => {
      const children: any[] = []
      if (item.icon) children.push(h(CIcon, { customClassName: 'nav-icon', name: item.icon }))
      if (item.name) children.push(item.name)
      const badge = typeof item.badge === 'function' ? item.badge() : item.badge
      if (badge && badge.text) {
        children.push(
          h(CBadge, { class: 'ms-auto', color: badge.color || 'primary' }, { default: () => badge.text! }),
        )
      }
      return children
    }

    const renderItem = (item: Item) => {
      if (Array.isArray(item.items) && item.items.length > 0) {
        const key = item.to || item.name || ''
        const isOpen = key ? !!openStates[key] : false

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
    // 라우트 변경 및 메뉴 데이터 로드 감지 (사이드바 클릭 제외)
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

    return () =>
      h(
        CSidebarNav,
        {},
        { default: () => reactiveNav.value.map(renderItem) },
      )
  },
})

export { AppSidebarNav }
