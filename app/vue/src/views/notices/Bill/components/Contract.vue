<script lang="ts" setup>
import { computed, type PropType, ref, watch } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { type Contract } from '@/store/types/contract'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, required: true },
  page: { type: Number, default: 1 },
  nowOrder: { type: Number, default: null },
  allChecked: { type: Boolean, default: false },
})

const emit = defineEmits(['on-cont-chk'])

const checked = ref(false)

const paidCompleted = computed(
  () => (props.contract?.last_paid_order?.pay_time ?? 0) >= (props.nowOrder ?? 0),
)

watch(props, (n, o) => {
  if (!paidCompleted.value) {
    checked.value = !n.allChecked
    contChk(n.contract?.pk as number)
  }
  if (n.page !== o.page) checked.value = false
})

const contChk = (ctorPk: number) => {
  checked.value = !checked.value
  emit('on-cont-chk', { chk: checked.value, pk: ctorPk })
}
</script>

<template>
  <CTableRow v-if="contract" class="text-center" :color="checked ? 'secondary' : ''">
    <CTableDataCell>
      <CFormCheck
        :id="'check_' + contract.pk"
        v-model="checked"
        :value="contract.pk"
        :disabled="paidCompleted"
        label="선택"
        @change="contChk(contract.pk as number)"
      />
    </CTableDataCell>

    <CTableDataCell>
      {{ contract.order_group_desc.name }}
    </CTableDataCell>

    <CTableDataCell class="text-left">
      <CIcon
        name="cibDiscover"
        :style="'color:' + contract.unit_type_desc.color"
        size="sm"
        class="mr-1"
      />
      {{ contract.unit_type_desc.name }}
    </CTableDataCell>
    <CTableDataCell>
      {{ contract.serial_number }}
    </CTableDataCell>
    <CTableDataCell :class="contract.key_unit?.houseunit ? '' : 'text-danger'" class="text-left">
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
    <CTableDataCell class="text-right">
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
