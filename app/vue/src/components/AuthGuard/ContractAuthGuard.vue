<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import NoAuth from '@/views/_Accounts/NoAuth.vue'

const account = useAccount()

const hasAuth = computed(
  () =>
    account.userInfo?.is_superuser ||
    (account.userInfo?.staffauth && account.userInfo.staffauth?.contract > '0'),
)
</script>

<template>
  <NoAuth v-if="!hasAuth" />
  <slot v-else />
</template>
