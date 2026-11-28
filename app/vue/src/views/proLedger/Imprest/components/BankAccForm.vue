<script lang="ts" setup>
import type { ProjectBank } from '@/store/types/proLedger.ts'
import BankAccForm from '@/views/proLedger/Manage/components/BankAccForm.vue'

defineProps<{
  bankAcc?: ProjectBank | null
  project?: number | null
}>()
const emit = defineEmits(['on-bank-create', 'on-bank-update'])
</script>

<template>
  <BankAccForm
    :bank-acc="bankAcc"
    :project="project"
    is-imprest
    @on-bank-create="emit('on-bank-create', $event)"
    @on-bank-update="emit('on-bank-update', $event)"
  />
</template>
