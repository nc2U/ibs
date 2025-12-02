<template>
  <CFormSelect v-model="account_d1" :size="size" :disabled="disabled" @change="handleChange">
    <option :value="null">{{ placeholder }}</option>
    <option v-for="item in accD1List" :key="item.id" :value="item.id">
      {{ item.name }}
    </option>
  </CFormSelect>
</template>

<script setup lang="ts">
import { inject, computed } from 'vue'
import { AccountSelectionKey } from './keys'

interface Props {
  size?: 'sm' | 'lg'
  disabled?: boolean
  placeholder?: string
}

withDefaults(defineProps<Props>(), {
  size: 'sm',
  disabled: false,
  placeholder: '대분류 선택',
})

const context = inject(AccountSelectionKey)
if (!context) {
  throw new Error('AccountD1Select must be used within AccountSelectorGroup')
}

const account_d1 = computed({
  get: () => context.account_d1.value,
  set: (val) => {
    context.account_d1.value = val
  },
})

const accD1List = computed(() => context.accD1List.value)

const handleChange = async () => {
  await context.handleD1Change()
}
</script>
