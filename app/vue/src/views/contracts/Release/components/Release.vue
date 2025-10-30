<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { type ContractRelease } from '@/store/types/contract'
import { numFormat, cutString } from '@/utils/baseMixins'

const props = defineProps({
  release: { type: Object as PropType<ContractRelease>, default: null },
  highlightId: { type: Number, default: null },
})
const emit = defineEmits(['call-form'])

const getStatus = (num: string) => {
  const status = [
    { code: '0', text: '신청 취소' },
    { code: '3', text: '해지 신청' },
    { code: '4', text: '해지 완료' },
    { code: '5', text: '자격 상실' },
  ]
  return status.filter(s => s.code === num).map(s => s.text)[0]
}

const textColor = computed(() => {
  if (props.release?.status === '0') return 'text-primary'
  else if (props.release?.status === '3') return 'text-danger'
  else return ''
})

const buttonColor = computed(() => {
  if (props.release?.status === '0') return 'info'
  else if (props.release?.status === '3') return 'warning'
  else return 'secondary'
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
    {{ getStatus(release.status) }}
  </CTableDataCell>
  <CTableDataCell class="text-right">
    {{ numFormat(release.refund_amount) }}
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
