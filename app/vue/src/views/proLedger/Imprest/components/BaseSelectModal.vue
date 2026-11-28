<script lang="ts" setup>
import BaseSelectModal from '@/views/proLedger/Manage/components/BaseSelectModal.vue'

withDefaults(
  defineProps<{
    modelValue: boolean
    type?: 'contract' | 'contractor'
    contract?: number | null
    contractor?: number | null
    accountName?: string
  }>(),
  {
    type: 'contract',
    contract: null,
    contractor: null,
    accountName: '',
  },
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'select', id: number | null): void
}>()
</script>

<template>
  <BaseSelectModal
    :model-value="modelValue"
    :type="type"
    :contract="contract"
    :contractor="contractor"
    :account-name="accountName"
    @update:model-value="emit('update:modelValue', $event)"
    @select="emit('select', $event)"
  />
</template>
