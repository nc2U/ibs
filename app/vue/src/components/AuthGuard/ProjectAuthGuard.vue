<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'

const account = useAccount()

const isLoading = computed(() => !account.userInfo)
</script>

<template>
  <div v-if="isLoading"></div>
  <slot v-else />
</template>
