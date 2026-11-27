<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { numFormat } from '@/utils/baseMixins.ts'
import { usePerms } from '@/composables/usePerms.ts'
import type { Contract } from '@/store/types/contract'

interface Props {
  contract: Contract
  page?: number
  nowOrder?: number | null
  allChecked?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  page: 1,
  nowOrder: null,
  allChecked: false,
})

const emit = defineEmits<{
  (e: 'on-cont-chk', payload: { chk: boolean; pk: number }): void
}>()

const { can, PERM } = usePerms()
const canNoticeRead = computed(() => can(PERM.NOTICE_READ))

const checked = ref(false)

const paidCompleted = computed(() => {
  const paidOrder = props.contract?.last_paid_order
  const currentCode = paidOrder?.pay_code ?? paidOrder?.pay_time ?? 0
  return currentCode >= (props.nowOrder ?? 0)
})

watch(
  () => props.allChecked,
  val => {
    if (!paidCompleted.value) {
      checked.value = val
      emit('on-cont-chk', { chk: val, pk: props.contract?.pk as number })
    }
  },
)

watch(
  () => props.page,
  () => {
    checked.value = false
  },
)

const contChk = (ctorPk: number) => {
  emit('on-cont-chk', { chk: checked.value, pk: ctorPk })
}
</script>

<template>
  <CTableRow v-if="contract" class="text-center" :color="checked ? 'secondary' : undefined">
    <CTableDataCell v-if="canNoticeRead" class="ps-3">
      <CFormCheck
        :id="'check_' + contract.pk"
        v-model="checked"
        :disabled="paidCompleted"
        label="선택"
        @change="contChk(contract.pk as number)"
      />
    </CTableDataCell>

    <CTableDataCell>
      {{ contract.order_group_desc?.name || '-' }}
    </CTableDataCell>

    <CTableDataCell class="text-start">
      <template v-if="contract.unit_type_desc">
        <CIcon
          name="cibDiscover"
          :style="'color:' + contract.unit_type_desc.color"
          size="sm"
          class="me-1"
        />
        {{ contract.unit_type_desc.name }}
      </template>
      <span v-else class="text-medium-emphasis">미정</span>
    </CTableDataCell>
    <CTableDataCell>
      {{ contract.serial_number }}
    </CTableDataCell>
    <CTableDataCell :class="contract.key_unit?.houseunit ? '' : 'text-danger'" class="text-start">
      {{ contract.key_unit?.houseunit ? contract.key_unit?.houseunit?.__str__ : '미정' }}
    </CTableDataCell>
    <CTableDataCell>
      <router-link
        :to="{
          name: '계약 상세 보기',
          params: { contractorId: contract.contractor?.pk },
        }"
      >
        {{ contract.contractor?.name }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell class="text-end">
      <router-link :to="{ name: '건별 납부 관리 - 상세', params: { contractId: contract.pk } }">
        {{ numFormat(contract?.total_paid || 0) }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell>
      <span v-if="paidCompleted" class="text-success">완납중</span>
      <span v-else class="text-danger">미납중</span>
      ({{ contract.last_paid_order?.pay_name || '계약금 미납' }})
    </CTableDataCell>
    <CTableDataCell>{{ contract.contractor?.contract_date }}</CTableDataCell>
  </CTableRow>
</template>
