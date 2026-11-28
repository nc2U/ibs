<script lang="ts" setup>
import type { AccountPicker } from '@/store/types/comLedger.ts'
import BankTransactionRow, {
  type BankTransactionData,
} from '@/views/proLedger/Manage/components/BankTransactionRow.vue'

export type { BankTransactionData }

defineProps<{
  transaction: BankTransactionData
  index: number
  project?: number | null
  bankAccounts: { value: number | null | undefined; label: string }[]
  proAccounts: AccountPicker[]
  getContracts: { value: number; label: string }[]
  getAllContractors: { value: number; label: string }[]
}>()

const emit = defineEmits<{
  (e: 'update:transaction', value: BankTransactionData): void
  (e: 'remove'): void
  (e: 'detectTransferWithdraw', sourceData: BankTransactionData): void
  (e: 'downloadTemplate'): void
  (e: 'uploadEntries'): void
}>()
</script>

<template>
  <BankTransactionRow
    :transaction="transaction"
    :index="index"
    :project="project"
    :bank-accounts="bankAccounts"
    :pro-accounts="proAccounts"
    :get-contracts="getContracts"
    :get-all-contractors="getAllContractors"
    @update:transaction="emit('update:transaction', $event)"
    @remove="emit('remove')"
    @detect-transfer-withdraw="emit('detectTransferWithdraw', $event)"
    @download-template="emit('downloadTemplate')"
    @upload-entries="emit('uploadEntries')"
  />
</template>
