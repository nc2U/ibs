<script lang="ts" setup>
import { inject, type PropType } from 'vue'
import { useRouter } from 'vue-router'
import type { Contract, Contractor } from '@/store/types/contract'

const props = defineProps({
  project: { type: Number, default: null },
  contract: { type: Object as PropType<Contract>, default: null },
  contractor: { type: Object as PropType<Contractor>, default: null },
  fromPage: { type: [Number, null] as PropType<number | null>, default: null },
})

const router = useRouter()

const isDark = inject('isDark')
</script>

<template>
  <CCol> </CCol>
</template>
