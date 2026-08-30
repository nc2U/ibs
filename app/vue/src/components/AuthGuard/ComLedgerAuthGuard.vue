<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms'
import NoAuth from '@/views/_Accounts/NoAuth.vue'

const account = useAccount()
const { canGlobal, PERM } = usePerms()

const isLoading = computed(() => !account.userInfo)

const canComLedgerRead = computed(
  () => canGlobal(PERM.LEDGER_COM_READ),
)
</script>

<template>
  <div v-if="isLoading"></div>
  <NoAuth v-else-if="!canComLedgerRead" />
  <slot v-else />
</template>
