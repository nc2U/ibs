<script lang="ts" setup>
import { computed } from 'vue'
import { useStore } from '@/store'

defineProps({
  size: {
    type: String,
    default: 'lg',
  },
  tooltipLocation: {
    type: String as () => 'top' | 'bottom' | 'left' | 'right',
    default: 'bottom',
  },
  customClass: {
    type: String,
    default: '',
  },
})

const store = useStore()
const theme = computed(() => store.theme)

const currentThemeIcon = computed(() => {
  if (theme.value === 'dark') return 'cil-moon'
  if (theme.value === 'auto') return 'cil-screen-desktop'
  return 'cil-sun'
})

const currentThemeLabel = computed(() => {
  if (theme.value === 'dark') return '다크 모드'
  if (theme.value === 'auto') return '기기 설정'
  return '라이트 모드'
})

const cycleTheme = () => {
  if (theme.value === 'default') {
    store.toggleTheme('dark')
  } else if (theme.value === 'dark') {
    store.toggleTheme('auto')
  } else {
    store.toggleTheme('default')
  }
}
</script>

<template>
  <button
    type="button"
    :class="['theme-switcher-btn pointer', customClass]"
    @click="cycleTheme"
    aria-label="Toggle Theme"
  >
    <CIcon :icon="currentThemeIcon" :size="size as any" class="text-50" />
    <v-tooltip activator="parent" :location="tooltipLocation">
      테마: {{ currentThemeLabel }}
    </v-tooltip>
  </button>
</template>

<style scoped>
.theme-switcher-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  padding: 0.375rem;
  border-radius: 0.375rem;
  color: inherit;
  transition: background-color 0.15s ease-in-out, opacity 0.15s ease-in-out;
}

.theme-switcher-btn:hover {
  background-color: rgba(128, 128, 128, 0.15);
}
</style>
