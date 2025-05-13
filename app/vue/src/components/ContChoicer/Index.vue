<script lang="ts" setup>
import { type PropType } from 'vue'
import MultiSelect from '@/components/MultiSelect/index.vue'

defineProps({
  disabled: { type: Boolean, default: false },
  getContracts: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})
</script>

<template>
  <MultiSelect
    mode="single"
    :options="getContracts"
    :disabled="disabled"
    placeholder="계약 정보 선택"
  />
</template>
