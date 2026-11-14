<script lang="ts" setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import type { Succession } from '@/store/types/contract'

const router = useRouter()

const props = defineProps<{
  succession: Succession
}>()

const emit = defineEmits<{
  'call-form': [succession: Succession]
  'done-alert': []
}>()

const { can, PERM } = usePerms()
const canContractSuccession = computed(() => can(PERM.CONTRACT_SUCCESSION))

const done = computed(() => props.succession?.status === '3')
const buttonColor = computed(() => (!done.value ? 'success' : 'secondary'))

const statusMap: Record<string, string> = {
  '1': '신청접수',
  '2': '변경인가대기',
  '3': '승계완료',
  '9': '승계취소',
}

const statusLabel = computed(() => statusMap[props.succession?.status] || '')

const callFormModal = () => {
  if (!done.value) {
    if (props.succession?.buyer?.pk) {
      router.replace({
        name: '권리 의무 승계',
        query: { contractor: props.succession.buyer.pk },
      })
    }
    emit('call-form', props.succession)
  } else {
    emit('done-alert')
  }
}
</script>

<template>
  <CTableDataCell class="text-center">
    <a href="#" class="text-decoration-none fw-semibold" @click.prevent="callFormModal">
      {{ succession.contract.serial_number }}
    </a>
  </CTableDataCell>
  <CTableDataCell class="text-center">
    <a href="#" class="text-decoration-none fw-semibold" @click.prevent="callFormModal">
      {{ succession.seller.name }}
    </a>
  </CTableDataCell>
  <CTableDataCell class="text-center">
    <a href="#" class="text-decoration-none fw-semibold" @click.prevent="callFormModal">
      {{ succession.buyer.name }}
    </a>
  </CTableDataCell>
  <CTableDataCell class="text-center">
    {{ succession.apply_date }}
  </CTableDataCell>
  <CTableDataCell class="text-center">
    {{ succession.trading_date }}
  </CTableDataCell>
  <CTableDataCell class="text-primary text-center fw-bold">
    {{ succession.approval_date || '-' }}
  </CTableDataCell>
  <CTableDataCell class="text-primary text-center fw-bold">
    {{ statusLabel }}
  </CTableDataCell>
  <CTableDataCell v-if="canContractSuccession" class="text-center">
    <v-btn type="button" :color="buttonColor" size="x-small" @click="callFormModal"> 확인</v-btn>
  </CTableDataCell>
</template>
