<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { read_auth_manage } from '@/utils/pageAuth'
import NoAuth from '@/views/_Accounts/NoAuth.vue'

const account = useAccount()

const isLoading = computed(() => account.userInfo === null || account.userInfo === undefined)

const hasAuth = computed(() => !!read_auth_manage.value)
</script>

<template>
  <div v-if="isLoading"></div>
  <NoAuth v-else-if="!hasAuth" />
  <slot v-else />
</template>
