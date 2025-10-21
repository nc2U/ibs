<script lang="ts" setup>
import { inject, type PropType } from 'vue'
import { useRouter } from 'vue-router'
import type { Contract, Contractor } from '@/store/types/contract'
import ContNavigation from './ContNavigation.vue'
import ContController from './ContController.vue'
import ContractorAlert from './ContractorAlert.vue'

const props = defineProps({
  project: { type: Number, default: null },
  contract: { type: Object as PropType<Contract>, default: null },
  contractor: { type: Object as PropType<Contractor>, default: null },
  fromPage: { type: [Number, null] as PropType<number | null>, default: null },
})

const emit = defineEmits(['type-select', 'on-submit', 'search-contractor', 'resume-form'])

const router = useRouter()

const searchContractor = (contor: string) => emit('search-contractor', contor)

const isDark = inject('isDark')

const resumeForm = (contor: string) => emit('resume-form', contor)
</script>

<template>
  <CCol>
    <ContNavigation :cont-on="!!contract" />
    <ContController :project="project" @search-contractor="searchContractor" />
    <ContractorAlert
      v-if="contractor"
      :is-blank="!contract"
      :contractor="contractor"
      @resume-form="resumeForm"
    />
  </CCol>
</template>
