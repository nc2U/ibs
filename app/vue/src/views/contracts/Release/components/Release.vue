<script lang="ts" setup>
import { computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { numFormat, cutString } from '@/utils/baseMixins'
import type { ContractRelease } from '@/store/types/contract'

const props = defineProps<{
  release: ContractRelease
}>()

const emit = defineEmits<{
  'call-form': [contractorId: number]
}>()

const { can, PERM } = usePerms()
const canContractRelease = computed(() => can(PERM.CONTRACT_RELEASE))

const releaseTypeMap: Record<string, string> = {
  '1': '해지',
  '2': '부적격',
  '3': '해지통보',
}

const releaseTypeLabel = computed(
  () => releaseTypeMap[props.release?.release_type] || '해지',
)

const statusMap: Record<string, string> = {
  '1': '접수등록',
  '2': '해지승인대기',
  '3': '변경인가대기',
  '4': '해지확정',
  '9': '신청취소',
}

const statusLabel = computed(() => statusMap[props.release?.status] || '')

const textColor = computed(() => {
  if (props.release?.status === '9') return 'text-primary'
  if (props.release?.status === '1') return 'text-danger'
  return ''
})

const buttonColor = computed(() => {
  if (props.release?.status === '9') return 'info'
  if (props.release?.status === '4') return 'secondary'
  return 'warning'
})

const callFormModal = () => {
  if (props.release?.contractor) {
    emit('call-form', props.release.contractor)
  }
}
</script>

<template>
  <CTableDataCell class="text-center">
    <a href="#" class="text-decoration-none fw-semibold" @click.prevent="callFormModal">
      {{ cutString(release.__str__ || '', 25) }}
    </a>
  </CTableDataCell>
  <CTableDataCell :class="textColor" class="text-center">
    [{{ releaseTypeLabel }}] {{ statusLabel }}
  </CTableDataCell>
  <CTableDataCell class="text-end">
    {{ numFormat(release.refund_amount ?? 0) }}
  </CTableDataCell>
  <CTableDataCell class="text-start">
    {{ release.refund_account_bank || '-' }}
  </CTableDataCell>
  <CTableDataCell class="text-start">
    {{ release.refund_account_number || '-' }}
  </CTableDataCell>
  <CTableDataCell class="text-center">
    {{ release.refund_account_depositor || '-' }}
  </CTableDataCell>
  <CTableDataCell class="text-center">
    {{ release.request_date }}
  </CTableDataCell>
  <CTableDataCell class="fw-bold text-primary text-center">
    {{ release.refund_completion_date || '-' }}
  </CTableDataCell>
  <CTableDataCell class="fw-bold text-primary text-center">
    {{ release.completion_date || '-' }}
  </CTableDataCell>
  <CTableDataCell v-if="canContractRelease" class="text-center">
    <v-btn type="button" :color="buttonColor" size="x-small" @click="callFormModal">확인</v-btn>
  </CTableDataCell>
</template>
