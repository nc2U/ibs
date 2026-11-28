<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms'
import NoAuth from '@/views/_Accounts/NoAuth.vue'

const account = useAccount()

const isLoading = computed(() => !account.userInfo)

const { canGlobal, PERM } = usePerms()
const canAuthManage = computed(
  () =>
    Boolean(account.superAuth) ||
    Boolean(account.workManager) ||
    (account.isStaff && canGlobal(PERM.PROJECT_MEMBER)),
)
</script>

<template>
  <div v-if="isLoading"></div>
  <NoAuth v-else-if="!canAuthManage" />
  <slot v-else />
</template>
