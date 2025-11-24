<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import NoAuth from '@/views/_Accounts/NoAuth.vue'

const account = useAccount()

const isLoading = computed(() => account.userInfo === null || account.userInfo === undefined)

const hasAuth = computed(
  () =>
    account.userInfo?.is_superuser ||
    (account.userInfo?.staffauth && account.userInfo.staffauth?.project_ledger > '0'),
)
</script>

<template>
  <div v-if="isLoading"></div>
  <NoAuth v-else-if="!hasAuth" />
  <slot v-else />
</template>
