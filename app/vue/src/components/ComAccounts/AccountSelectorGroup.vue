<template>
  <slot />
</template>

<script setup lang="ts">
import { provide, onMounted, watch } from 'vue'
import { useAccountSelection } from './useAccountSelection'
import { AccountSelectionKey } from './keys'
import type { AccountSelectionContext } from './keys'

interface Props {
  fetchD1List: (sort: number) => Promise<void>
  fetchD2List: (d1: number) => Promise<void>
  fetchD3List: (d2: number) => Promise<void>
  getD1List: () => any[]
  getD2List: () => any[]
  getD3List: () => any[]
  initialValues?: {
    sort?: 1 | 2
    account_d1?: number | null
    account_d2?: number | null
    account_d3?: number | null
  }
  autoInitialize?: boolean
}

interface Emits {
  (e: 'update:sort', value: 1 | 2): void
  (e: 'update:accountD1', value: number | null): void
  (e: 'update:accountD2', value: number | null): void
  (e: 'update:accountD3', value: number | null): void
}

const props = withDefaults(defineProps<Props>(), {
  autoInitialize: true,
})

const emit = defineEmits<Emits>()

// useAccountSelection 실행
const selection = useAccountSelection(
  {
    fetchD1List: props.fetchD1List,
    fetchD2List: props.fetchD2List,
    fetchD3List: props.fetchD3List,
    getD1List: props.getD1List,
    getD2List: props.getD2List,
    getD3List: props.getD3List,
  },
  props.initialValues,
)

// Context 제공
const context: AccountSelectionContext = {
  sort: selection.sort,
  handleSortChange: selection.handleSortChange,
  account_d1: selection.account_d1,
  accD1List: selection.accD1List,
  handleD1Change: selection.handleD1Change,
  account_d2: selection.account_d2,
  accD2List: selection.accD2List,
  handleD2Change: selection.handleD2Change,
  account_d3: selection.account_d3,
  accD3List: selection.accD3List,
  handleD3Change: selection.handleD3Change,
  initialize: selection.initialize,
  reset: selection.reset,
}

provide(AccountSelectionKey, context)

// 변경사항을 부모에게 emit
watch(
  () => selection.sort.value,
  (val) => emit('update:sort', val),
)
watch(
  () => selection.account_d1.value,
  (val) => emit('update:accountD1', val),
)
watch(
  () => selection.account_d2.value,
  (val) => emit('update:accountD2', val),
)
watch(
  () => selection.account_d3.value,
  (val) => emit('update:accountD3', val),
)

// 초기화
onMounted(() => {
  if (props.autoInitialize && props.initialValues) {
    selection.initialize()
  }
})
</script>
