<script lang="ts" setup>
import type { ProBankTrans } from '@/store/types/proLedger.ts'
import ProTransItem from '@/views/proLedger/Manage/components/ProTransItem.vue'

defineProps<{
  proTrans: ProBankTrans
  project?: number | null
  calculated?: string
  isHighlighted?: boolean
}>()
</script>

<template>
  <ProTransItem
    :pro-trans="proTrans"
    :project="project"
    :calculated="calculated"
    :is-highlighted="isHighlighted"
    is-imprest
  />
</template>
