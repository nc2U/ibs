<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms.ts'
import type { PermissionCode } from '@/store/constants/permissions'
import NoAuth from '@/views/_Accounts/NoAuth.vue'

const props = withDefaults(
  defineProps<{
    project?: number | null
    requiredPerm?: PermissionCode | PermissionCode[]
  }>(),
  {
    project: undefined,
    requiredPerm: undefined,
  },
)

const account = useAccount()

const isLoading = computed(() => !account.userInfo)

const { can, PERM } = usePerms()
const canAccess = computed(() => {
  const perm = props.requiredPerm ?? PERM.LEDGER_READ
  return props.project ? can(perm, props.project) : can(perm)
})
</script>

<template>
  <div v-if="isLoading"></div>
  <NoAuth v-else-if="!canAccess" />
  <slot v-else />
</template>
