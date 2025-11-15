<script lang="ts" setup>
import { ref, computed, type PropType } from 'vue'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account'
import type { CompanyBank, CashBook } from '@/store/types/comCash'
import type { Project } from '@/store/types/project'
import { write_company_cash } from '@/utils/pageAuth'
import { numFormat, cutString, diffDate } from '@/utils/baseMixins'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'
import CashForm from '@/views/comCash/CashManage/components/CashForm.vue'

const props = defineProps({
  projects: { type: Array as PropType<Project[]>, default: () => [] },
  cash: { type: Object as PropType<CashBook>, required: true },
  calculated: { type: String, default: '2000-01-01' },
  isHighlighted: { type: Boolean, default: false },
})

const emit = defineEmits([
  'multi-submit',
  'on-delete',
  'patch-d3-hide',
  'on-bank-create',
  'on-bank-update',
])

const refDelModal = ref()
const refAlertModal = ref()
const updateFormModal = ref()

const cls = ref(['text-primary', 'text-danger', 'text-info'])
const sortClass = computed(() => cls.value[(props.cash?.sort as number) - 1])
const d1Class = computed(() => cls.value[((props.cash?.account_d1 as number) % 3) - 1])

const store = useStore()
const dark = computed(() => store.theme === 'dark')
const rowColor = computed(() => {
  let color = ''
  color = dark.value ? '' : color
  // 하이라이트가 우선순위가 가장 높음
  if (props.isHighlighted) {
    color = 'warning'
  } else {
    color = props.cash?.is_separate ? 'primary' : color
    color = props.cash?.separated ? 'secondary' : color
  }
  return color
})

const accountStore = useAccount()
const allowedPeriod = computed(
  () =>
    accountStore.superAuth ||
    (props.cash?.deal_date && diffDate(props.cash.deal_date, new Date(props.calculated)) <= 10),
)

const showDetail = () => updateFormModal.value.callModal()

const multiSubmit = (payload: { formData: CashBook; sepData: CashBook | null }) =>
  emit('multi-submit', payload)

const deleteConfirm = () => {
  if (write_company_cash.value)
    if (allowedPeriod.value) refDelModal.value.callModal()
    else
      refAlertModal.value.callModal(
        null,
        '거래일로부터 30일이 경과한 건은 삭제할 수 없습니다. 관리자에게 문의바랍니다.',
      )
  else refAlertModal.value.callModal()
}

const deleteObject = () => {
  emit('on-delete', { company: props.cash?.company, pk: props.cash?.pk })
  refDelModal.value.close()
}

const patchD3Hide = (payload: { pk: number; is_hide: boolean }) => emit('patch-d3-hide', payload)

const onBankCreate = (payload: CompanyBank) => emit('on-bank-create', payload)
const onBankUpdate = (payload: CompanyBank) => emit('on-bank-update', payload)
</script>

<template>
  <CTableRow
    v-if="cash"
    class="text-center"
    :color="rowColor"
    :style="cash.is_separate ? 'font-weight: bold;' : ''"
    :data-cash-id="cash.pk"
  >
    <CTableDataCell>{{ cash.deal_date }}</CTableDataCell>
    <CTableDataCell :class="sortClass">
      {{ cash.sort_desc }}
    </CTableDataCell>
    <CTableDataCell class="text-left">
      <span v-if="cash.bank_account_desc">
        {{ cutString(cash.bank_account_desc, 10) }}
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-left truncate">
      <span v-if="cash.trader">
        {{ cutString(cash.trader, 8) }}
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-left truncate">
      <span v-if="cash.content">
        {{ cutString(cash.content, 15) }}
      </span>
    </CTableDataCell>
    <CTableDataCell class="text-right" :color="dark ? '' : 'primary'">
      {{ numFormat(cash.income || 0) }}
    </CTableDataCell>
    <CTableDataCell class="text-right" :color="dark ? '' : 'danger'">
      {{ numFormat(cash.outlay || 0) }}
    </CTableDataCell>
    <CTableDataCell :class="d1Class">
      {{ cash.account_d1_desc }}
    </CTableDataCell>
    <CTableDataCell class="text-left truncate">
      {{ cash.account_d3_desc }}
    </CTableDataCell>
    <CTableDataCell>{{ cash.evidence_desc }}</CTableDataCell>
    <CTableDataCell v-if="write_company_cash">
      <v-btn color="info" size="x-small" @click="showDetail" :disabled="!allowedPeriod">
        확인
      </v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>본사 입출금 거래 건별 수정</template>
    <template #default>
      <CashForm
        :cash="cash"
        :projects="projects"
        @multi-submit="multiSubmit"
        @on-delete="deleteConfirm"
        @patch-d3-hide="patchD3Hide"
        @on-bank-create="onBankCreate"
        @on-bank-update="onBankUpdate"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>

  <ConfirmModal ref="refDelModal">
    <template #header> 입출금 거래 정보 삭제</template>
    <template #default>
      삭제한 데이터는 복구할 수 없습니다. 해당 입출금 거래 정보를 삭제하시겠습니까?
    </template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteObject">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
