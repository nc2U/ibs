<script lang="ts" setup>
import { ref, computed, type PropType } from 'vue'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account'
import { write_project_cash } from '@/utils/pageAuth'
import { numFormat, cutString, diffDate } from '@/utils/baseMixins'
import { type ProBankAcc, type ProjectCashBook } from '@/store/types/proCash'
import FormModal from '@/components/Modals/FormModal.vue'
import ProCashForm from '@/views/proCash/Manage/components/ProCashForm.vue'

const props = defineProps({
  proCash: { type: Object as PropType<ProjectCashBook>, required: true },
  calculated: { type: String, default: '2000-01-01' },
  isHighlighted: { type: Boolean, default: false },
})

const emit = defineEmits(['multi-submit', 'on-delete', 'on-bank-create', 'on-bank-update'])

const updateFormModal = ref()

const sortClass = computed(
  () => ['', 'text-primary', 'text-danger', 'text-info'][props.proCash?.sort || 0],
)

const store = useStore()
const dark = computed(() => store.theme === 'dark')
const rowColor = computed(() => {
  if (props.isHighlighted) return 'warning'
  const { proCash } = props
  if (proCash?.separated) return 'light'
  if (proCash?.is_separate) return 'primary'
  if (proCash?.contract && [1, 5].includes(proCash?.project_account_d3 ?? 0)) return 'info'

  return ''
})

const accountStore = useAccount()
const allowedPeriod = computed(
  () =>
    accountStore.superAuth ||
    (props.proCash?.deal_date &&
      diffDate(props.proCash.deal_date, new Date(props.calculated)) <= 10),
)

const showDetail = () => updateFormModal.value.callModal()

const multiSubmit = (payload: { formData: ProjectCashBook; sepData: ProjectCashBook | null }) =>
  emit('multi-submit', payload)

const onDelete = (payload: { project: number; pk: number }) => emit('on-delete', payload)

const onBankCreate = (payload: ProBankAcc) => emit('on-bank-create', payload)
const onBankUpdate = (payload: ProBankAcc) => emit('on-bank-update', payload)
</script>

<template>
  <CTableRow
    v-if="proCash"
    class="text-center"
    :color="rowColor"
    :style="proCash.is_separate ? 'font-weight: bold;' : ''"
    :data-procash-id="proCash.pk"
  >
    <CTableDataCell>{{ proCash.deal_date }}</CTableDataCell>
    <CTableDataCell :class="sortClass">
      {{ proCash?.sort_desc }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <span v-if="proCash.bank_account_desc">
        {{ cutString(proCash.bank_account_desc, 9) }}
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <span v-if="proCash.trader">
        {{ cutString(proCash.trader, 9) }}
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <span v-if="proCash.content">
        {{ cutString(proCash.content, 10) }}
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-right" :color="dark ? '' : 'success'">
      {{ numFormat(proCash.income || 0) }}
    </CTableDataCell>
    <CTableDataCell class="text-right" :color="dark ? '' : 'danger'">
      {{ numFormat(proCash.outlay || 0) }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      {{ proCash.project_account_d2_desc }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <span v-if="proCash.project_account_d3_desc">
        {{ cutString(proCash.project_account_d3_desc, 9) }}
      </span>
    </CTableDataCell>

    <CTableDataCell>{{ proCash.evidence_desc }}</CTableDataCell>
    <CTableDataCell v-if="write_project_cash">
      <v-btn color="info" size="x-small" @click="showDetail" :disabled="!allowedPeriod">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>프로젝트 입출금 거래 건별 관리</template>
    <template #default>
      <ProCashForm
        :pro-cash="proCash"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
        @on-bank-create="onBankCreate"
        @on-bank-update="onBankUpdate"
      />
    </template>
  </FormModal>
</template>
