<script lang="ts" setup>
import { ref, computed, type PropType } from 'vue'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account'
import { write_project_cash } from '@/utils/pageAuth'
import { numFormat, cutString, diffDate } from '@/utils/baseMixins'
import { type ProBankAcc, type ProjectCashBook } from '@/store/types/proCash'
import FormModal from '@/components/Modals/FormModal.vue'
import ProImprestForm from '@/views/proCash/Imprest/components/ProImprestForm.vue'

const props = defineProps({
  imprest: { type: Object as PropType<ProjectCashBook>, required: true },
  calculated: { type: String, default: '2000-01-01' },
})

const emit = defineEmits(['multi-submit', 'on-delete', 'on-bank-update'])

const updateFormModal = ref()

const sortClass = computed(
  () => ['', 'text-primary', 'text-danger', 'text-info'][props.imprest?.sort || 0],
)

const store = useStore()
const dark = computed(() => store.theme === 'dark')
const rowColor = computed(() => {
  let color = ''
  color =
    props.imprest?.contract && (props.imprest.project_account_d3 as number) <= 2 ? 'info' : color
  color = dark.value ? '' : color
  color = props.imprest?.is_separate ? 'primary' : color
  color = props.imprest?.separated ? 'secondary' : color
  return color
})

const accountStore = useAccount()
const allowedPeriod = computed(
  () =>
    accountStore.superAuth ||
    (props.imprest?.deal_date &&
      diffDate(props.imprest.deal_date, new Date(props.calculated)) <= 10),
)

const showDetail = () => updateFormModal.value.callModal()

const multiSubmit = (payload: { formData: ProjectCashBook; sepData: ProjectCashBook | null }) =>
  emit('multi-submit', payload)

const onDelete = (payload: { project: number; pk: number }) => emit('on-delete', payload)

const onBankUpdate = (payload: ProBankAcc) => emit('on-bank-update', payload)
</script>

<template>
  <CTableRow
    v-if="imprest"
    class="text-center"
    :color="rowColor"
    :style="imprest.is_separate ? 'font-weight: bold;' : ''"
  >
    <CTableDataCell>{{ imprest.deal_date }}</CTableDataCell>
    <CTableDataCell :class="sortClass">
      {{ imprest.sort_desc }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <span v-if="imprest.bank_account_desc">
        {{ cutString(imprest.bank_account_desc, 9) }}
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <span v-if="imprest.trader">
        {{ cutString(imprest.trader, 9) }}
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <span v-if="imprest.content">
        {{ cutString(imprest.content, 10) }}
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-right" :color="dark ? '' : 'success'">
      {{ numFormat(imprest.income || 0) }}
    </CTableDataCell>
    <CTableDataCell class="text-right" :color="dark ? '' : 'danger'">
      {{ numFormat(imprest.outlay || 0) }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      {{ imprest.project_account_d2_desc }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <span v-if="imprest.project_account_d3_desc">
        {{ cutString(imprest.project_account_d3_desc, 9) }}
      </span>
    </CTableDataCell>
    <CTableDataCell>{{ imprest.evidence_desc }}</CTableDataCell>
    <CTableDataCell v-if="write_project_cash">
      <v-btn color="info" size="x-small" @click="showDetail" :disabled="!allowedPeriod">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>운영비(전도금) 거래 건별 관리</template>
    <template #default>
      <ProImprestForm
        :imprest="imprest"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @on-bank-update="onBankUpdate"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
