<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { useRouter } from 'vue-router'
import { write_contract } from '@/utils/pageAuth'
import { type Contract } from '@/store/types/contract'
import ContractForm from './ContractForm.vue'
import FormModal from '@/components/Modals/FormModal.vue'

const props = defineProps({
  contract: { type: Object as PropType<Contract>, required: true },
  unitSet: { type: Boolean, default: false },
  isHighlighted: { type: Boolean, default: false },
  currentPage: { type: Number, default: 1 },
})

const emit = defineEmits(['contract-converted'])

const updateFormModal = ref()

const router = useRouter()
const contractorPk = computed(() => props.contract?.contractor?.pk)

const getColor = (q: '1' | '2' | '3' | '4' | undefined) =>
  q ? { '1': 'info', '2': 'warning', '3': 'success', '4': 'danger' }[q] : ''
</script>

<template>
  <CTableRow
    v-if="contract"
    class="text-center"
    :color="props.isHighlighted ? 'warning' : contract.is_sup_cont ? 'success' : ''"
    :data-contract-id="contract.pk"
  >
    <CTableDataCell>
      <router-link
        :to="{
          name: '계약 상세 보기',
          params: { contractorId: contractorPk },
          query: { from_page: props.currentPage },
        }"
      >
        {{ contract.serial_number }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell>
      <CBadge :color="getColor(contract.contractor?.qualification)">
        {{ contract.contractor?.qualifi_display }}
      </CBadge>
    </CTableDataCell>
    <CTableDataCell>
      {{ contract.order_group_desc.name }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <template v-if="contract.unit_type_desc">
        <CIcon
          name="cibDiscover"
          :style="'color:' + contract.unit_type_desc.color"
          size="sm"
          class="mr-1"
        />
        {{ contract.unit_type_desc.name }}
      </template>
      <span v-else class="text-medium-emphasis">미정</span>
    </CTableDataCell>
    <CTableDataCell>
      <router-link
        :to="{
          name: '계약 상세 보기',
          params: { contractorId: contractorPk },
          query: { from_page: props.currentPage },
        }"
      >
        {{ contract.contractor?.name }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell
      class="text-left"
      :class="contract.key_unit?.houseunit !== null ? '' : 'text-danger'"
    >
      <router-link
        :to="{
          name: '계약 상세 보기',
          params: { contractorId: contractorPk },
          query: { from_page: props.currentPage },
        }"
      >
        {{ contract.key_unit?.houseunit ? contract.key_unit?.houseunit.__str__ : '미정' }}
      </router-link>
    </CTableDataCell>
    <CTableDataCell>{{ contract.contractor?.contract_date }}</CTableDataCell>
    <CTableDataCell>{{ contract.sup_cont_date }}</CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(contract.contractprice?.price || 0) }}
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(contract.total_paid) }}
    </CTableDataCell>
    <CTableDataCell>
      {{ !contract.last_paid_order ? '-' : contract.last_paid_order.__str__ }}
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
        color="info"
        size="x-small"
        @click="
          router.push({
            name: '계약 상세 보기',
            params: { contractorId: contractorPk },
            query: { from_page: props.currentPage },
          })
        "
      >
        보기
      </v-btn>
      <v-btn type="button" color="success" size="x-small" @click="updateFormModal.callModal()">
        수정
      </v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="xl">
    <template #header>청약 / 계약 등록 수정</template>
    <template #default>
      <ContractForm
        :project="contract.project"
        :contract="contract"
        :unit-set="unitSet"
        @close="updateFormModal.close()"
        @contract-converted="$emit('contract-converted')"
      />
    </template>
  </FormModal>
</template>
