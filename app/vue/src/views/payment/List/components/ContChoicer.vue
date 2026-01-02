<script lang="ts" setup>
import { ref, onMounted, computed, nextTick, type PropType } from 'vue'
import { numFormat } from '@/utils/baseMixins'
import { write_payment } from '@/utils/pageAuth'
import { useContract } from '@/store/pinia/contract'
import type { Contract, ContFilter } from '@/store/types/contract'
import type { PaymentList } from '@/store/types/payment.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({
  project: { type: Number, required: true },
  payment: { type: Object as PropType<PaymentList>, required: true },
})

const emit = defineEmits(['pay-match', 'close'])

const refAlertModal = ref()
const refConfirmModal = ref()

const form = ref({
  search: '',
})

const cont = ref<Contract | null>(null)
const msg = ref('')
const textClass = ref('')

onMounted(() => pageInit())

const contStore = useContract()
const contactList = computed(() => contStore.contractList)
const fetchContractList = (payload: ContFilter) => contStore.fetchContractList(payload)

const pageInit = () => {
  form.value.search = ''
  textClass.value = 'text-medium-emphasis'
  msg.value = '계약자 관련정보 또는 계약 일련변호를 입력하세요.'
  contStore.contractList = []
}

const searchCont = () => {
  nextTick(() => {
    if (form.value.search === '') pageInit()
    else {
      fetchContractList({ ...{ project: props.project }, ...form.value })
    }
  })
  if (contactList.value.length === 0) {
    msg.value = `해당 검색어로 등록된 데이터가 없습니다.`
    textClass.value = 'text-danger'
  }
}
const contMatching = (contract: Contract) => {
  if (write_payment) {
    cont.value = contract
    refConfirmModal.value.callModal()
  } else refAlertModal.value.callModal()
}

const modalAction = () => {
  const trans_id = props.payment?.trans_id
  const pk = props.payment?.entry_id
  const contract = (cont.value as Contract)?.pk
  const content = `${(cont.value as Contract)?.contractor?.name}[${(cont.value as Contract)?.serial_number}] 대금납부`
  emit('pay-match', { trans_id, content, accounting_entries: [{ pk, contract }] })
  pageInit()
  emit('close')
}
</script>

<template>
  <CRow>
    <CCol class="pl-4 pr-4">
      <CCallout color="warning" class="pb-1 mb-4">
        <CRow>
          <CCol>
            <CRow>
              <CCol md="5" class="mb-3">
                <CInputGroup class="flex-nowrap">
                  <CFormInput
                    v-model="form.search"
                    placeholder="계약자, 비고, 계약 일련번호"
                    aria-label="Search"
                    aria-describedby="addon-wrapping"
                    @keydown.enter="searchCont"
                  />
                  <CInputGroupText @click="searchCont"> 계약 건 찾기</CInputGroupText>
                </CInputGroup>
              </CCol>
            </CRow>
          </CCol>
        </CRow>
        <CRow>
          <CCol v-if="contactList.length !== 0" color="warning" class="p-2 pl-3">
            <v-btn
              v-for="c in contactList"
              :key="c.pk"
              type="button"
              color="#546E7A"
              variant="outlined"
              size="small"
              @click="contMatching(c)"
            >
              {{ `${c.contractor?.name}(${c.serial_number})` }}
            </v-btn>
          </CCol>
          <CCol v-else class="mt-3 m-2" :class="textClass">
            {{ msg }}
          </CCol>
        </CRow>
      </CCallout>

      <CAlert v-if="contactList.length !== 0" color="default" class="pt-0 pb-0 text-primary">
        상기 계약 건 중 아래 수납 항목을 매칭 등록할 계약 건을 선택한 후 클릭하여 주십시요.
      </CAlert>

      <CAlert color="info">
        <span>
          {{
            `[입금자] : ${payment.trader}  | [입금액] : ${numFormat(
              payment.amount,
            )} | [입금계좌] : ${payment.bank_account} | [입금일] : ${payment.deal_date}`
          }}
        </span>
      </CAlert>
    </CCol>
  </CRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header>건별 수납 매칭</template>
    <template #default>
      해당 수납 항목을 &lt;<span class="text-primary" style="font-weight: bold">
        {{ `${cont?.contractor?.name} [${cont?.serial_number}]` }} </span
      >&gt; 계약 건의 납부대금으로 등록합니다.
    </template>
    <template #footer>
      <v-btn color="primary" size="small" @click="modalAction">저장</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
