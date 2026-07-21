<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { type ContractRelease } from '@/store/types/contract'
import { numFormat, cutString } from '@/utils/baseMixins'

const props = defineProps({
  release: { type: Object as PropType<ContractRelease>, default: null },
  highlightId: { type: Number, default: null },
})
const emit = defineEmits(['call-form'])

const releaseTypeLabel = computed(() => {
  return props.release?.release_type === '2' ? '부적격' : '해지'
})

const statusLabel = computed(() => {
  const statusMap: Record<string, string> = {
    '1': '접수등록',
    '2': '해지승인대기',
    '3': '변경인가대기',
    '4': '해지확정',
    '9': '신청취소',
  }
  return statusMap[props.release?.status] || ''
})

const textColor = computed(() => {
  if (props.release?.status === '9') return 'text-primary'
  else if (props.release?.status === '1') return 'text-danger'
  else return ''
})

const buttonColor = computed(() => {
  if (props.release?.status === '9') return 'info'
  else if (props.release?.status === '4') return 'secondary'
  else return 'warning'
})

const callFormModal = () => emit('call-form', props.release?.contractor)
</script>

<template>
  <CTableDataCell class="text-center">
    <router-link to="" @click="callFormModal">
      {{ cutString(release.__str__, 25) }}
    </router-link>
  </CTableDataCell>
  <CTableDataCell :class="textColor" class="text-center">
    [{{ releaseTypeLabel }}] {{ statusLabel }}
  </CTableDataCell>
  <CTableDataCell class="text-right">
    {{ numFormat(release.refund_amount ?? 0) }}
  </CTableDataCell>
  <CTableDataCell class="text-left">
    {{ release.refund_account_bank }}
  </CTableDataCell>
  <CTableDataCell class="text-left">
    {{ release.refund_account_number }}
  </CTableDataCell>
  <CTableDataCell class="text-center">
    {{ release.refund_account_depositor }}
  </CTableDataCell>
  <CTableDataCell class="text-center">
    {{ release.request_date }}
  </CTableDataCell>
  <CTableDataCell class="fw-bold text-primary text-center">
    {{ release.completion_date }}
  </CTableDataCell>
  <CTableDataCell class="text-center">
    <v-btn type="button" :color="buttonColor" size="x-small" @click="callFormModal"> 확인</v-btn>
  </CTableDataCell>
</template>
