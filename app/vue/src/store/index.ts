import { ref } from 'vue'
import { defineStore } from 'pinia'

type Type = 'default' | 'dark'

export const useStore = defineStore('store', () => {
  const asideVisible = ref(false)
  const sidebarVisible = ref(
    !localStorage.getItem('sidebarVisible') || localStorage.getItem('sidebarVisible') === 'true',
  )
  const sidebarUnfoldable = ref(localStorage.getItem('sidebarUnfoldable') === 'true')
  const theme = ref<Type>((localStorage.getItem('theme') as Type) || 'default')
  const LoadingStatus = ref(false)
  const registerCode = ref('dyibs-staff')

  const toggleAside = () => (asideVisible.value = !asideVisible.value)

  const toggleSidebar = () => {
    sidebarVisible.value = !sidebarVisible.value
    localStorage.setItem('sidebarVisible', String(sidebarVisible.value))
  }
  const toggleTheme = (payload: Type) => {
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
