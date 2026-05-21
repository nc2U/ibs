import { ref } from 'vue'
import { defineStore } from 'pinia'
import Cookies from 'js-cookie'

type Type = 'default' | 'dark'

export const useStore = defineStore('store', () => {
  const asideVisible = ref(false)
  const sidebarVisible = ref(
    !Cookies.get('sidebarVisible') || Cookies.get('sidebarVisible') === 'true',
  )
  const sidebarUnfoldable = ref(Cookies.get('sidebarUnfoldable') === 'true')
  const theme = ref<Type>((Cookies.get('theme') as Type) || 'default')
  const LoadingStatus = ref(false)
  const registerCode = ref('dyibs-staff')

  const toggleAside = () => (asideVisible.value = !asideVisible.value)

  const toggleSidebar = () => {
    sidebarVisible.value = !sidebarVisible.value
    Cookies.set('sidebarVisible', String(sidebarVisible.value))
  }
  const toggleTheme = (payload: Type) => {
    theme.value = payload
    Cookies.set('theme', payload)
  }
  const toggleUnfoldable = () => {
    sidebarUnfoldable.value = !sidebarUnfoldable.value
    Cookies.set('sidebarUnfoldable', String(sidebarUnfoldable.value))
  }
  const updateSidebarVisible = (payload: boolean) => {
    sidebarVisible.value = payload
    Cookies.set('sidebarVisible', String(payload))
  }
  const startSpinner = () => (LoadingStatus.value = true)

  const endSpinner = () => (LoadingStatus.value = false)

  return {
    asideVisible,
    sidebarVisible,
    sidebarUnfoldable,
    theme,
    LoadingStatus,
    registerCode,

    toggleAside,
    toggleSidebar,
    toggleTheme,
    toggleUnfoldable,
    updateSidebarVisible,
    startSpinner,
    endSpinner,
  }
})
