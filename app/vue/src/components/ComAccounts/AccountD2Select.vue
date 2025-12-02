<template>
  <CFormSelect v-model="account_d2" :size="size" :disabled="isDisabled" @change="handleChange">
    <option :value="null">{{ placeholder }}</option>
    <option v-for="item in accD2List" :key="item.id" :value="item.id">
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
  placeholder: '중분류 선택',
})

const context = inject(AccountSelectionKey)
if (!context) {
  throw new Error('AccountD2Select must be used within AccountSelectorGroup')
}

const account_d2 = computed({
  get: () => context.account_d2.value,
  set: (val) => {
    context.account_d2.value = val
  },
})

const accD2List = computed(() => context.accD2List.value)

// D1이 선택되지 않으면 비활성화
const isDisabled = computed(() => props.disabled || !context.account_d1.value)

const handleChange = async () => {
  await context.handleD2Change()
}
</script>
