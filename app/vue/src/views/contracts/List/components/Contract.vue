<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { useRouter } from 'vue-router'
import { write_contract } from '@/utils/pageAuth'
import { type Contract } from '@/store/types/contract'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, required: true },
})

const contractor = computed(() => props.contract?.contractor?.pk)
const router = useRouter()

const getColor = (q: '1' | '2' | '3' | '4' | undefined) =>
  q ? { '1': 'info', '2': 'warning', '3': 'success', '4': 'danger' }[q] : ''
</script>

<template>
  <CTableRow v-if="contract" class="text-center" :color="contract.is_sup_cont ? 'success' : ''">
    <CTableDataCell>
      <router-link :to="{ name: '계약 등록 수정', query: { contractor } }">
        {{ contract.serial_number }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell>
      <CBadge :color="getColor(contract.contractor?.qualification)">
        {{ contract.contractor?.qualifi_display }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell>
      {{ contract.order_group_desc.order_group_name }}
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
      <router-link :to="{ name: '계약 등록 수정', query: { contractor } }">
        {{ contract.contractor?.name }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell
      class="text-left"
      :class="contract.key_unit?.houseunit !== null ? '' : 'text-danger'"
    >
      <router-link :to="{ name: '계약 등록 수정', query: { contractor } }">
        {{ contract.key_unit?.houseunit ? contract.key_unit?.houseunit.__str__ : '미정' }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell>{{ contract.contractor?.contract_date }}</CTableDataCell>
    <CTableDataCell>{{ contract.sup_cont_date }}</CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(contract.contractprice?.price || 0) }}
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(contract.contractprice?.down_pay || 0) }}
    </CTableDataCell>
    <CTableDataCell>
      {{ !contract.last_paid_order ? '-' : contract.last_paid_order.__str__ }}
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(contract.total_paid) }}
    </CTableDataCell>
    <CTableDataCell>
      <span v-if="!!contract.contract_files.length" class="pointer">
        <a :href="contract.contract_files[0].file" target="_blank">
          <v-icon icon="mdi-download-box" color="primary" />
        </a>
        <v-tooltip activator="parent" location="top">
          {{ contract.contract_files[0].file_name }} 다운로드
        </v-tooltip>
      </span>
      <span v-else>
        <v-icon icon="mdi-download-box-outline" color="secondary" />
        <v-tooltip activator="parent" location="top">미등록</v-tooltip>
      </span>
    </CTableDataCell>
    <CTableDataCell v-if="write_contract">
      <v-btn
        type="button"
        color="success"
        size="x-small"
        @click="
          router.push({
            name: '계약 등록 수정',
            query: { contractor },
          })
        "
      >
        수정
      </v-btn>
    </CTableDataCell>
  </CTableRow>
</template>
