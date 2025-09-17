import { computed } from 'vue'
import { useStore } from '@/store'

const isDark = computed(() => useStore().theme === 'dark')

// -----------------------------------------------------------------------
export const TableSecondary = computed(() => (isDark.value ? 'dark' : 'secondary'))
export const TablePrimary = computed(() => (isDark.value ? 'dark' : 'primary'))
export const TableSuccess = computed(() => (isDark.value ? 'dark' : 'success'))
export const TableInfo = computed(() => (isDark.value ? 'dark' : 'info'))

// export const TableWarning = computed(() => (isDark.value ? 'dark' : 'warning'))
// export const TableDanger = computed(() => (isDark.value ? 'dark' : 'danger'))
// export const TableLight = computed(() => (isDark.value ? 'dark' : 'light'))

// -----------------------------------------------------------------------

export const AlertSecondary = computed(() => (isDark.value ? '' : 'secondary'))
// export const AlertPrimary = computed(() => (isDark.value ? '' : 'primary'))
// export const AlertSuccess = computed(() => (isDark.value ? '' : 'success'))
// export const AlertInfo = computed(() => (isDark.value ? '' : 'info'))
// export const AlertWarning = computed(() => (isDark.value ? '' : 'warning'))
// export const AlertDanger = computed(() => (isDark.value ? '' : 'danger'))

export const AlertLight = computed(() => (isDark.value ? '' : 'light'))

// -----------------------------------------------------------------------
export const darkSecondary = computed(() => (isDark.value ? 'secondary' : ''))

// export const bgSecondary = computed(() => (isDark.value ? '' : 'bg-secondary'))
// export const bgPrimary = computed(() => (isDark.value ? '' : 'bg-primary'))
// export const bgSuccess = computed(() => (isDark.value ? '' : 'bg-success'))
// export const bgInfo = computed(() => (isDark.value ? '' : 'bg-info'))
// export const bgWarning = computed(() => (isDark.value ? '' : 'bg-warning'))
// export const bgDanger = computed(() => (isDark.value ? '' : 'bg-danger'))

export const bgSecondary = computed(() => (isDark.value ? '' : 'bg-secondary'))
export const bgPrimary = computed(() => (isDark.value ? '' : 'bg-primary'))
export const bgSuccess = computed(() => (isDark.value ? '' : 'bg-success'))
export const bgLight = computed(() => (isDark.value ? '' : 'bg-light'))
export const colorLight = computed(() => (isDark.value ? '' : 'light'))

export const btnSecondary = computed(() => (isDark.value ? 'secondary' : 'dark'))
export const btnLight = computed(() => (isDark.value ? 'grey-lighten-2' : 'light'))
