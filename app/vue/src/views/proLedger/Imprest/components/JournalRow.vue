<script lang="ts" setup>
import ProAccountEntry, {
  type NewEntryForm,
} from '@/views/proLedger/Manage/components/ProAccountEntry.vue'

defineProps<{
  sort: 1 | 2
  displayRows: NewEntryForm[]
  transAmount: number | null
  project?: number | null
}>()

const emit = defineEmits<{
  (e: 'update:entries', rows: NewEntryForm[]): void
  (e: 'removeEntry', index: number): void
  (e: 'insertTransferFee', index: number): void
}>()
</script>

<template>
  <ProAccountEntry
    :sort="sort"
    :display-rows="displayRows"
    :trans-amount="transAmount"
    :project="project"
    @update:entries="emit('update:entries', $event)"
    @remove-entry="emit('removeEntry', $event)"
    @insert-transfer-fee="emit('insertTransferFee', $event)"
  />
</template>
