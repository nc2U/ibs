<script lang="ts" setup>
import { type PropType } from 'vue'
import type { Contract } from '@/store/types/contract'
import AddProof from './AddProof.vue'
import AddPledge from './AddPledge.vue'
import AddConsultation from './AddConsultation.vue'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, required: true },
})
</script>

<template>
  <!-- 구비서류 제출 현황 카드 -->
  <AddProof />
  <AddPledge />

  <!-- 상담 내역 카드 -->
  <AddConsultation />
</template>
