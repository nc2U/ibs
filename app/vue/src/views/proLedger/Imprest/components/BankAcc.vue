<script lang="ts" setup>
import { ref } from 'vue'
import type { ProjectBank } from '@/store/types/proLedger.ts'
import BankAcc from '@/views/proLedger/Manage/components/BankAcc.vue'

defineProps<{
  project?: number | null
}>()
const emit = defineEmits(['on-bank-create', 'on-bank-update'])

const innerRef = ref<InstanceType<typeof BankAcc> | null>(null)
const callModal = () => innerRef.value?.callModal()
defineExpose({ callModal })
</script>

<template>
  <BankAcc
    ref="innerRef"
    :project="project"
    is-imprest
    @on-bank-create="emit('on-bank-create', $event as ProjectBank)"
    @on-bank-update="emit('on-bank-update', $event as ProjectBank)"
  />
</template>
