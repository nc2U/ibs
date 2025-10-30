<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { type SiteContract } from '@/store/types/project'
import { numFormat } from '@/utils/baseMixins'
import { write_project_site } from '@/utils/pageAuth'
import FormModal from '@/components/Modals/FormModal.vue'
import SiteContractForm from './SiteContractForm.vue'

const props = defineProps({
  contract: { type: Object as PropType<SiteContract>, required: true },
  isHighlight: { type: Boolean, default: false },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: SiteContract) => emit('multi-submit', payload)
const onDelete = (payload: { pk: number; project: number }) => emit('on-delete', payload)
</script>

<template>
  <CTableRow
    v-if="contract"
    class="text-center"
    :class="{ 'table-warning': props.isHighlight }"
    :data-site-contract-id="contract.pk"
  >
    <CTableDataCell>{{ contract.owner_desc?.own_sort_desc }}</CTableDataCell>
    <CTableDataCell>
      <a href="javascript:void(0);" @click="showDetail">
        {{ contract.owner_desc?.owner }}
      </a>
    </CTableDataCell>
    <CTableDataCell>
      <a href="javascript:void(0);" @click="showDetail">
        {{ contract.contract_date }}
      </a></CTableDataCell
    >
    <CTableDataCell class="text-right">
      {{ numFormat(contract.contract_area as number, 2) }}
    </CTableDataCell>
    <CTableDataCell class="text-right" color="warning">
      {{ numFormat((contract.contract_area as number) * 0.3025, 2) }}
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(contract.total_price as number) }}
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(contract.down_pay1 as number) }}
    </CTableDataCell>
    <CTableDataCell :class="{ 'bg-success': contract.down_pay1_is_paid }">
      {{ contract.down_pay1_is_paid ? '완료' : '' }}
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(contract.remain_pay as number) }}
    </CTableDataCell>
    <CTableDataCell :class="{ 'bg-success': contract.remain_pay_is_paid }">
      {{ contract.remain_pay_is_paid ? '완료' : '' }}
    </CTableDataCell>
    <CTableDataCell>
      <span v-if="!!contract.site_cont_files.length" class="pointer">
        <a :href="contract.site_cont_files[0].file" target="_blank">
          <v-icon icon="mdi-download-box" color="primary" />
        </a>
        <v-tooltip activator="parent" location="top">
          {{ contract.site_cont_files[0]?.file_name }} 다운로드
        </v-tooltip>
      </span>
      <span v-else>
        <v-icon icon="mdi-download-box-outline" color="secondary" />
        <v-tooltip activator="parent" location="top">미등록</v-tooltip>
      </span>
    </CTableDataCell>
    <CTableDataCell v-if="write_project_site">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>부지 매입 계약 등록</template>
    <template #default>
      <SiteContractForm
        :contract="contract"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
