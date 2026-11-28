<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms'
import NoAuth from '@/views/_Accounts/NoAuth.vue'

const account = useAccount()

const isLoading = computed(() => !account.userInfo)

const { canGlobal, PERM } = usePerms()
const canComSettingsRead = computed(
  () =>
    Boolean(account.superAuth) ||
    (account.isStaff && (canGlobal(PERM.PROJECT_CREATE) || canGlobal(PERM.PROJECT_UPDATE))),
)
</script>

<template>
  <div v-if="isLoading"></div>
  <NoAuth v-else-if="!canComSettingsRead" />
  <slot v-else />
</template>
