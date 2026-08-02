<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms.ts'
import NoAuth from '@/views/_Accounts/NoAuth.vue'

const account = useAccount()

const isLoading = computed(() => !account.userInfo)

const { can, PERM } = usePerms()
const canContractRead = computed(() => can(PERM.CONTRACT_READ))
</script>

<template>
  <div v-if="isLoading"></div>
  <NoAuth v-else-if="!canContractRead" />
  <slot v-else />
</template>
