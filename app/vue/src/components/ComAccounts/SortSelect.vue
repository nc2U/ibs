<template>
  <CFormSelect v-model="sort" :size="size" :disabled="disabled" @change="handleChange">
    <option value="1">입금</option>
    <option value="2">출금</option>
  </CFormSelect>
</template>

<script setup lang="ts">
import { inject, computed } from 'vue'
import { AccountSelectionKey } from './keys'

interface Props {
  size?: 'sm' | 'lg'
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  size: 'sm',
  disabled: false,
})

const context = inject(AccountSelectionKey)
if (!context) {
  throw new Error('SortSelect must be used within AccountSelectorGroup')
}

const sort = computed({
  get: () => context.sort.value,
  set: (val) => {
    context.sort.value = val
  },
})

const handleChange = async () => {
  await context.handleSortChange()
}
</script>
