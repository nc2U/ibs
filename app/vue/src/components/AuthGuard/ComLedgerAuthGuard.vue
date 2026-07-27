<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import NoAuth from '@/views/_Accounts/NoAuth.vue'

const account = useAccount()

const isLoading = computed(() => !account.userInfo)

const hasAuth = computed(() => account.isFinancial)
</script>

<template>
  <div v-if="isLoading"></div>
  <NoAuth v-else-if="!hasAuth" />
  <slot v-else />
</template>
