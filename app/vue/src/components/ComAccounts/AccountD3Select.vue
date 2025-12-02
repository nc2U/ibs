<template>
  <CFormSelect v-model="account_d3" :size="size" :disabled="isDisabled" @change="handleChange">
    <option :value="null">{{ placeholder }}</option>
    <option v-for="item in accD3List" :key="item.id" :value="item.id">
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

const props = withDefaults(defineProps<Props>(), {
  size: 'sm',
  disabled: false,
  placeholder: '소분류 선택',
})

const context = inject(AccountSelectionKey)
if (!context) {
  throw new Error('AccountD3Select must be used within AccountSelectorGroup')
}

const account_d3 = computed({
  get: () => context.account_d3.value,
  set: (val) => {
    context.account_d3.value = val
  },
})

const accD3List = computed(() => context.accD3List.value)

// D2가 선택되지 않으면 비활성화
const isDisabled = computed(() => props.disabled || !context.account_d2.value)

const handleChange = async () => {
  await context.handleD3Change()
}
</script>
