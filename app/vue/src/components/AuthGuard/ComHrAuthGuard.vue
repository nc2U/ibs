<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms.ts'
import NoAuth from '@/views/_Accounts/NoAuth.vue'

const account = useAccount()

const isLoading = computed(() => !account.userInfo)

const { can, PERM } = usePerms()
const canComHrRead = computed(() => account.isStaff && can(PERM.HQ_HR_WORK_READ))
</script>

<template>
  <div v-if="isLoading"></div>
  <NoAuth v-else-if="!canComHrRead" />
  <slot v-else />
</template>
