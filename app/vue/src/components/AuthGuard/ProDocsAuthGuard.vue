<script setup lang="ts">
import { computed } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms.ts'
import NoAuth from '@/views/_Accounts/NoAuth.vue'

const props = defineProps({
  global: { type: Boolean, default: false },
})

const account = useAccount()

const isLoading = computed(() => !account.userInfo)

const { can, canGlobal, PERM } = usePerms()
const canDocsRead = computed(() =>
  props.global ? canGlobal(PERM.DOCS_READ) : canGlobal(PERM.DOCS_READ) || can(PERM.DOCS_READ),
)
</script>

<template>
  <div v-if="isLoading"></div>
  <NoAuth v-else-if="!canDocsRead" />
  <slot v-else />
</template>
