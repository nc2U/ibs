<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { type Contractor, type ContractRelease } from '@/store/types/contract'
import { AlertLight } from '@/utils/cssMixins'

const props = defineProps({
  contractor: { type: Object as PropType<Contractor>, default: null },
  contRelease: { type: Object as PropType<ContractRelease>, default: null },
})
const emit = defineEmits(['call-form'])

const isSuccession = computed(
  () => !!props.contractor?.succession && !props.contractor?.succession.is_approval,
)

const callFormModal = () => emit('call-form', props.contractor.pk)
</script>

<template>
  <CAlert :color="AlertLight" variant="solid" class="text-right">
    <v-btn
      :color="contRelease ? 'secondary' : 'warning'"
      :disabled="isSuccession"
      @click="callFormModal"
    >
      {{ contRelease ? '수정하기' : '등록하기' }}
    </v-btn>
  </CAlert>
</template>
