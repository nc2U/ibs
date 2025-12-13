<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from '@/store'
import { useAccount } from '@/store/pinia/account'
import { write_company_cash } from '@/utils/pageAuth'
import { cutString, diffDate, numFormat } from '@/utils/baseMixins'
import type { Project } from '@/store/types/project'
import type { BankTransaction, CompanyBank } from '@/store/types/comLedger'

const props = defineProps({
  projects: { type: Array as PropType<Project[]>, default: () => [] },
  transaction: { type: Object as PropType<BankTransaction>, required: true },
  calculated: { type: String, default: '2000-01-01' },
  isHighlighted: { type: Boolean, default: false },
  hasChildren: { type: Boolean, default: false },
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

const router = useRouter()

const store = useStore()
const dark = computed(() => store.theme === 'dark')
const rowColor = computed(() => {
  let color = ''
  color = dark.value ? '' : color
  // 하이라이트가 우선순위가 가장 높음
  if (props.isHighlighted) {
    color = 'warning'
  } else {
    color = '' // props.transaction?.accounting_entries.length > 1 ? 'primary' : color
    color = '' // props.transaction?.separated ? 'secondary' : color
  }
  return color
})

const accountStore = useAccount()
const allowedPeriod = computed(
  () =>
    accountStore.superAuth ||
    (props.transaction?.deal_date &&
      diffDate(props.transaction.deal_date, new Date(props.calculated)) <= 10),
)

const multiSubmit = (payload: { formData: BankTransaction; sepData: BankTransaction | null }) =>
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
  emit('on-delete', { company: props.transaction?.company, pk: props.transaction?.pk })
  refDelModal.value.close()
}

const patchD3Hide = (payload: { pk: number; is_hide: boolean }) => emit('patch-d3-hide', payload)

const onBankCreate = (payload: CompanyBank) => emit('on-bank-create', payload)
const onBankUpdate = (payload: CompanyBank) => emit('on-bank-update', payload)
</script>

<template>
  <template v-if="transaction">
    <CTableRow class="align-top" :color="rowColor" :data-cash-id="transaction.pk">
      <CTableDataCell style="padding-top: 12px">
        <span class="text-primary">{{ transaction.deal_date }}</span>
      </CTableDataCell>
      <CTableDataCell style="padding-top: 12px">
        {{ cutString(transaction.note, 20) }}
      </CTableDataCell>
      <CTableDataCell style="padding-top: 12px">
        <span v-if="transaction.bank_account_name">
          {{ cutString(transaction.bank_account_name, 10) }}
        </span>
      </CTableDataCell>
      <CTableDataCell class="truncate" style="padding-top: 12px">
        <span v-if="transaction.content">
          {{ cutString(transaction.content, 15) }}
        </span>
      </CTableDataCell>
      <CTableDataCell
        class="text-right"
        :class="transaction.sort === 1 ? 'text-success strong' : ''"
        style="padding-top: 12px"
      >
        {{ transaction.sort === 1 ? '+' : '-' }}{{ numFormat(transaction.amount || 0) }}
      </CTableDataCell>

      <CTableDataCell colspan="6" class="bg-yellow-lighten-5">
        <CTable small class="m-0 p-0">
          <colgroup>
            <col style="width: 20%" />
            <col style="width: 32%" />
            <col style="width: 16%" />
            <col style="width: 26%" />
            <col v-if="write_company_cash" style="width: 6%" />
          </colgroup>
          <CTableRow v-for="entry in transaction.accounting_entries" :key="entry.pk">
            <CTableDataCell>
              <div class="d-flex align-items-center bg-transparent">
                <span>{{ entry.account_name }}</span>
                <v-tooltip v-if="entry.affiliate" location="top">
                  <template v-slot:activator="{ props: tooltipProps }">
                    <v-icon
                      v-bind="tooltipProps"
                      icon="mdi-link-variant"
                      color="primary"
                      size="16"
                      class="ml-1"
                    />
                  </template>
                  <div class="pa-2">
                    <div class="font-weight-bold mb-1">관계회사/프로젝트</div>
                    <div>{{ entry.affiliate_display }}</div>
                  </div>
                </v-tooltip>
              </div>
            </CTableDataCell>
            <CTableDataCell> {{ cutString(entry.trader, 20) }} </CTableDataCell>
            <CTableDataCell
              class="text-right"
              :class="transaction.sort === 1 ? 'text-success strong' : ''"
            >
              {{ transaction.sort === 1 ? '+' : '-' }}{{ numFormat(entry.amount) }}
            </CTableDataCell>
            <CTableDataCell class="pl-3">
              {{ cutString(entry.evidence_type_display, 10) }}
            </CTableDataCell>
            <CTableDataCell v-if="write_company_cash" class="text-right pr-2">
              <v-icon
                icon="mdi-pencil"
                size="18"
                @click="
                  router.push({
                    name: '본사 거래 내역 - 수정',
                    params: { transId: transaction.pk },
                  })
                "
                class="pointer edit-icon-hover"
              />
            </CTableDataCell>
          </CTableRow>
        </CTable>
      </CTableDataCell>
    </CTableRow>
  </template>
</template>

<style scoped>
/* 기본적으로 수정 아이콘 숨김 */
.edit-icon-hover {
  opacity: 0;
  transition: opacity 0.2s ease;
  background-color: transparent !important;
}

/* 내부 테이블 행에 hover 시 아이콘 표시 */
.table tbody tr:hover .edit-icon-hover {
  opacity: 1;
}

.dark-theme .bg-yellow-lighten-5 {
  background-color: #49473a !important;
  color: #fff !important;
}
</style>
