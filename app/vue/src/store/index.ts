import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export type ThemeType = 'default' | 'dark' | 'auto'

export const useStore = defineStore('store', () => {
  const asideVisible = ref(false)
  const sidebarVisible = ref(
    !localStorage?.getItem?.('sidebarVisible') ||
      localStorage?.getItem?.('sidebarVisible') === 'true',
  )
  const sidebarUnfoldable = ref(localStorage?.getItem?.('sidebarUnfoldable') === 'true')
  const theme = ref<ThemeType>((localStorage?.getItem?.('theme') as ThemeType) || 'default')
  const systemDark = ref(
    typeof window !== 'undefined' && window.matchMedia
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
      : false,
  )
  const LoadingStatus = ref(false)
  const registerCode = ref('dyibs-staff')

  // isDark: 'dark' 이거나 'auto' 상태에서 시스템(OS)이 다크인 경우 true
  const isDark = computed(() => {
    if (theme.value === 'dark') return true
    if (theme.value === 'auto') return systemDark.value
    return false
  })

  // OS 다크모드 미디어 쿼리 리스너 초기화
  const initThemeListener = () => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemDark.value = mediaQuery.matches

    const handler = (e: MediaQueryListEvent) => {
      systemDark.value = e.matches
    }
    mediaQuery.addEventListener('change', handler)
  }

  const toggleAside = () => (asideVisible.value = !asideVisible.value)

  const toggleSidebar = () => {
    sidebarVisible.value = !sidebarVisible.value
    localStorage.setItem('sidebarVisible', String(sidebarVisible.value))
  }
  const toggleTheme = (payload: ThemeType) => {
    theme.value = payload
    localStorage.setItem('theme', payload)
  }
  const toggleUnfoldable = () => {
    sidebarUnfoldable.value = !sidebarUnfoldable.value
    localStorage.setItem('sidebarUnfoldable', String(sidebarUnfoldable.value))
  }
  const updateSidebarVisible = (payload: boolean) => {
    sidebarVisible.value = payload
    localStorage.setItem('sidebarVisible', String(payload))
  }
  const startSpinner = () => (LoadingStatus.value = true)

  const endSpinner = () => (LoadingStatus.value = false)

  return {
    asideVisible,
    sidebarVisible,
    sidebarUnfoldable,
    theme,
    isDark,
    systemDark,
    LoadingStatus,
    registerCode,

    initThemeListener,
    toggleAside,
    toggleSidebar,
    toggleTheme,
    toggleUnfoldable,
    updateSidebarVisible,
    startSpinner,
    endSpinner,
  }
})
